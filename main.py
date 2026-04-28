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
            pix = page.get_pixmap(dpi=300)
            img_path = f"p{i+1}_{pdf_name}.png"
            pix.save(img_path)
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image", lossless=True)
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
    v_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:150px;object-fit:fill;background:#000;display:block;"><b style="font-size:12px;display:block;padding:5px;color:#333;">{v["public_id"]}</b><div style="display:flex;flex-wrap:wrap;gap:4px;padding:2px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">PLAY</a><a href="{v["secure_url"].replace("/upload/","/upload/fl_attachment/")}" style="flex:1;background:#28a745;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">SAVE</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">DEL</a></div></div>""" for v in videos])
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ UPLOAD</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a></div><form action="/" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search Videos..." style="flex:1;padding:8px;border:none;border-radius:4px 0 0 4px;"><button style="background:#333;color:#fff;border:none;padding:8px 15px;border-radius:0 4px 4px 0;font-weight:bold;">GO</button></form></div>{v_list if v_list else "<p style='text-align:center;padding:20px;'>No Results Found</p>"} {"<a href='/?next="+new_c+"&q="+q+"' style='display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;font-weight:bold;margin:10px;border-radius:5px;'>LOAD NEXT VIDEOS ↓</a>" if new_c else ""}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:5px;"><b style="font-size:13px;display:block;color:#e74c3c;margin-bottom:8px;">{f["name"].upper()}</b><div style="display:flex;gap:4px;"><a href="/view_pdf?name={f["name"]}" style="flex:2;background:#e74c3c;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;font-weight:bold;">OPEN PDF</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" style="flex:1;background:orange;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;font-weight:bold;">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;font-weight:bold;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">PDF Archive</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">HOME</a><a href="/upload_pdf_page" style="flex:1;background:#fff;color:#e74c3c;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ NEW PDF</a></div><form action="/pdf_home" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search PDFs..." style="flex:1;padding:8px;border:none;border-radius:4px 0 0 4px;"><button style="background:#333;color:#fff;border:none;padding:8px 15px;border-radius:0 4px 4px 0;font-weight:bold;">GO</button></form></div>{f_list if f_list else "<p style='text-align:center;padding:20px;'>No PDFs Found</p>"}</body>"""

def get_upload_template(target_url, title, theme_color):
    return render_template_string("""
    <body style="padding:20px;font-family:sans-serif;text-align:center;background:#f0f0f0;">
        <div style="background:#fff;padding:20px;border-radius:10px;max-width:400px;margin:auto;box-shadow:0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="color:{{theme_color}};">{{title}}</h3>
            <form id="uploadForm">
                <input type="file" name="file" id="fileInput" style="margin-bottom:15px;width:100%;"><br>
                <input type="text" name="name" id="nameInput" placeholder="Enter Name" style="width:95%;padding:12px;margin-bottom:10px;border:1px solid #ddd;border-radius:5px;">
                <input type="password" name="pw" id="pwInput" placeholder="Admin Pass" style="width:95%;padding:12px;margin-bottom:15px;border:1px solid #ddd;border-radius:5px;">
                
                <div id="progressWrapper" style="display:none;margin-bottom:15px;">
                    <div style="background:#eee;border-radius:10px;overflow:hidden;height:20px;border:1px solid #ccc;">
                        <div id="progressBar" style="width:0%;height:100%;background:{{theme_color}};transition:width 0.3s;"></div>
                    </div>
                    <small id="statusText" style="color:#666;">Uploading: 0%</small>
                </div>

                <button type="button" onclick="uploadFile()" id="upBtn" style="width:100%;padding:15px;background:{{theme_color}};color:#fff;border:none;border-radius:5px;font-weight:bold;cursor:pointer;">START UPLOAD</button>
            </form>
            <br><a href="javascript:history.back()" style="color:#666;text-decoration:none;font-size:12px;">← Go Back</a>
        </div>

        <script>
        function uploadFile() {
            var file = document.getElementById('fileInput').files[0];
            var name = document.getElementById('nameInput').value;
            var pw = document.getElementById('pwInput').value;
            if(!file || !name || !pw) { alert("Sari fields bharo!"); return; }

            var formData = new FormData();
            formData.append("file", file);
            formData.append("name", name);
            formData.append("pw", pw);

            document.getElementById('progressWrapper').style.display = 'block';
            document.getElementById('upBtn').disabled = true;
            document.getElementById('upBtn').innerText = "UPLOADING...";

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "{{target_url}}", true);

            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    var percent = Math.round((e.loaded / e.total) * 100);
                    document.getElementById('progressBar').style.width = percent + '%';
                    document.getElementById('statusText').innerText = "Uploading: " + percent + "%";
                }
            };

            xhr.onload = function() {
                if (xhr.status == 200) {
                    alert("Upload Successful!");
                    window.location.href = (window.location.pathname == "/admin_upload") ? "/" : "/pdf_home";
                } else {
                    alert("Error: " + xhr.responseText);
                    document.getElementById('upBtn').disabled = false;
                }
            };
            xhr.send(formData);
        }
        </script>
    </body>
    """, title=title, theme_color=theme_color, target_url=target_url)

@app.route("/admin_upload")
def admin_upload():
    return get_upload_template("/do_up", "Upload Video", "#28a745")

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return get_upload_template("/do_pdf_upload", "Upload PDF", "#e74c3c")

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "video").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
        return "OK"
    return "Wrong Password", 403

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("name").replace(" ","_")
        if f:
            pdf_path = f"temp_{int(time.time())}.pdf"
            f.save(pdf_path)
            threading.Thread(target=process_pdf_background, args=(pdf_path, n)).start()
            return "OK"
    return "Wrong Password", 403

# Reuse confirm/view_pdf/modify from previous version
@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    next_c = request.args.get("next")
    ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f"""<div style="background:#000;margin-bottom:15px;text-align:center;border-bottom:3px solid #e74c3c;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;display:block;"><div style="padding:10px;background:#333;"><a href="{p["secure_url"].replace("/upload/","/upload/fl_attachment/")}" style="background:#28a745;color:#fff;font-size:11px;text-decoration:none;padding:8px 20px;border-radius:5px;font-weight:bold;">DOWNLOAD PAGE</a></div></div>""" for p in pages])
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:10px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;border-bottom:2px solid #e74c3c;"><a href="/pdf_home" style="text-decoration:none;font-size:13px;color:#e74c3c;font-weight:bold;">← BACK</a><b style="font-size:12px;color:#333;">{name[:15].upper()}</b><span></span></div>{h} {f"<a href='/view_pdf?name="+name+"&next="+new_c+"' style='display:block;background:#e74c3c;color:#fff;padding:18px;text-align:center;text-decoration:none;font-weight:bold;font-size:14px;border-radius:5px;margin:10px;'>NEXT 10 PAGES →</a>" if new_c else ""}</body>"""

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="text-align:center;padding:25px;font-family:sans-serif;background:#f0f0f0;"><div style="background:#fff;padding:20px;border-radius:10px;"><h4 style="color:#333;">{{t.upper()}}</h4><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name" style="width:90%;padding:12px;margin-bottom:15px;border:1px solid #ddd;border-radius:5px;"><br>{% endif %}<input type="password" name="pw" placeholder="Pass" style="width:90%;padding:12px;margin-bottom:20px;border:1px solid #ddd;border-radius:5px;"><br><button style="width:100%;padding:15px;background:#333;color:#fff;border:none;border-radius:5px;font-weight:bold;">CONFIRM</button></form></div></body>""", t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t = request.form.get("task"); p = request.form.get("pid"); tp = request.form.get("type")
        if tp == "video":
            if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
            elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
            return redirect("/")
        else:
            if t == "rename":
                new_n = request.form.get("new").replace(" ","_")
                res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{p}/")
                for r in res.get("resources", []):
                    cloudinary.uploader.rename(r["public_id"], r["public_id"].replace(f"pdf_data/{p}/", f"pdf_data/{new_n}/"))
            elif t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/")
                cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect("/pdf_home")
    return "Wrong Password"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
