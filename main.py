import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import threading
from flask import Flask, request, redirect, render_template_string, jsonify

app = Flask(__name__)

# Config
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

def process_pdf_background(pdf_path, pdf_name):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            
            # --- AUTO-CROP LOGIC ---
            text_bbox = page.get_textbox_rects()
            if text_bbox:
                union_rect = fitz.Rect()
                for rect in text_bbox: union_rect.include_rect(rect)
                union_rect.x0 = max(0, union_rect.x0 - 5)
                union_rect.y0 = max(0, union_rect.y0 - 5)
                union_rect.x1 = min(page.rect.width, union_rect.x1 + 5)
                union_rect.y1 = min(page.rect.height, union_rect.y1 + 5)
                page.set_cropbox(union_rect)

            # Mobile friendly quality
            pix = page.get_pixmap(dpi=140) 
            img_path = f"p{i+1}_{pdf_name}.jpg"
            pix.save(img_path, "jpg")
            
            # Uploading pages
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image", quality="auto:eco")
            
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
        if os.path.exists(pdf_path): os.remove(pdf_path)
    except: pass

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:150px;object-fit:fill;background:#000;display:block;"><b style="font-size:12px;display:block;padding:5px;color:#333;">{v["public_id"]}</b><div style="display:flex;flex-wrap:wrap;gap:4px;padding:2px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">PLAY</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">DEL</a></div></div>""" for v in videos])
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a></div><form action="/" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search..." style="flex:1;padding:8px;border:none;border-radius:4px 0 0 4px;"><button style="background:#333;color:#fff;border:none;padding:8px 15px;border-radius:0 4px 4px 0;">GO</button></form></div>{v_list}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:5px;"><b style="font-size:13px;display:block;color:#e74c3c;">{f["name"].upper()}</b><div style="display:flex;gap:4px;margin-top:5px;"><a href="/view_pdf?name={f["name"]}" style="flex:2;background:#e74c3c;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;">OPEN PDF</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;position:sticky;top:0;"><h3 style="margin:0;">PDF Archive</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="background:#333;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">HOME</a><a href="/upload_pdf_page" style="background:#fff;color:#e74c3c;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">+ NEW PDF</a></div><form action="/pdf_home" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search PDFs..." style="flex:1;padding:8px;border:none;"><button style="background:#333;color:#fff;border:none;padding:8px;">GO</button></form></div>{f_list}</body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next"); ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f"""<div style="background:#000;margin-bottom:15px;text-align:center;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;"><div style="padding:10px;background:#333;"><a href="{p["secure_url"].rsplit(".", 1)[0]}.jpg" style="background:#28a745;color:#fff;font-size:11px;text-decoration:none;padding:8px 20px;border-radius:5px;">DOWNLOAD {p["public_id"].split("/")[-1].upper()}</a></div></div>""" for p in pages])
    next_btn = f"<a href='/view_pdf?name={name}&next={new_c}' style='display:block;background:#e74c3c;color:#fff;padding:18px;text-align:center;text-decoration:none;font-weight:bold;margin:10px;border-radius:5px;'>LOAD NEXT 10 PAGES →</a>" if new_c else ""
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:10px;position:sticky;top:0;border-bottom:2px solid #e74c3c;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;">← BACK</a></div>{h}{next_btn}</body>"""

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return render_template_string("""
    <body style="padding:20px;font-family:sans-serif;text-align:center;">
        <div style="background:#fff;padding:20px;border:1px solid #ddd;border-radius:10px;">
            <h3 style="color:#e74c3c;">Upload PDF</h3>
            <input type="file" id="fileInput" style="margin-bottom:10px;"><br>
            <input type="text" id="nameInput" placeholder="Kitab Name" style="width:90%;padding:10px;margin-bottom:10px;"><br>
            <input type="password" id="pwInput" placeholder="Pass" style="width:90%;padding:10px;margin-bottom:15px;"><br>
            <div id="prog" style="display:none;margin-bottom:10px;">
                <div style="background:#eee;height:20px;border-radius:10px;overflow:hidden;">
                    <div id="bar" style="width:0%;height:100%;background:#e74c3c;"></div>
                </div>
                <small id="status">Starting...</small>
            </div>
            <button onclick="upload()" id="btn" style="width:100%;padding:15px;background:#e74c3c;color:#fff;border:none;border-radius:5px;">UPLOAD NOW</button>
        </div>
        <script>
        function upload() {
            var file = document.getElementById('fileInput').files[0];
            var name = document.getElementById('nameInput').value;
            var pw = document.getElementById('pwInput').value;
            if(!file || !name || !pw) return;
            var fd = new FormData();
            fd.append("file", file); fd.append("name", name); fd.append("pw", pw);
            document.getElementById('prog').style.display = 'block';
            document.getElementById('btn').disabled = true;
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/do_pdf_upload", true);
            xhr.upload.onprogress = function(e) {
                var p = Math.round((e.loaded/e.total)*100);
                document.getElementById('bar').style.width = p+'%';
                document.getElementById('status').innerText = "Sending to Server: "+p+"%";
            };
            xhr.onload = function() {
                if(xhr.status==200) { 
                    document.getElementById('status').innerText = "Done! Processing pages...";
                    setTimeout(()=>location.href="/pdf_home", 2000);
                } else { alert("Error!"); document.getElementById('btn').disabled = false; }
            };
            xhr.send(fd);
        }
        </script>
    </body>
    """)

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("name").replace(" ","_")
        if f:
            pdf_path = f"temp_{int(time.time())}.pdf"
            f.save(pdf_path)
            threading.Thread(target=process_pdf_background, args=(pdf_path, n)).start()
            return "OK"
    return "Error", 403

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="padding:20px;text-align:center;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name" style="width:90%;padding:10px;"><br><br>{% endif %}<input type="password" name="pw" placeholder="Pass" style="width:90%;padding:10px;"><br><br><button style="width:100%;padding:15px;background:#333;color:#fff;">CONFIRM</button></form></body>""", t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t = request.form.get("task"); p = request.form.get("pid"); tp = request.form.get("type")
        if tp == "video":
            if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
            return redirect("/")
        else:
            if t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/")
                cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect("/pdf_home")
    return "Error"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
