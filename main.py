import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import threading
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Cloudinary Config
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

def background_processor(pdf_path, pdf_name):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            # AUTO-CROP logic for Jio Bharat
            text_bbox = page.get_textbox_rects()
            if text_bbox:
                union_rect = fitz.Rect()
                for rect in text_bbox: union_rect.include_rect(rect)
                union_rect.x0 = max(0, union_rect.x0 - 5)
                union_rect.y0 = max(0, union_rect.y0 - 5)
                union_rect.x1 = min(page.rect.width, union_rect.x1 + 5)
                union_rect.y1 = min(page.rect.height, union_rect.y1 + 5)
                page.set_cropbox(union_rect)

            pix = page.get_pixmap(dpi=142)
            img_path = f"p{i+1}_{pdf_name}.jpg"
            pix.save(img_path, "jpg")
            
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image", quality="auto:eco")
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
    except: pass
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=12, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    
    v_html = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:150px;object-fit:fill;background:#000;display:block;"><b style="font-size:12px;display:block;padding:5px;">{v["public_id"]}</b><div style="display:flex;gap:4px;padding:2px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:10px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">PLAY</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="background:orange;color:#fff;padding:10px;text-decoration:none;border-radius:4px;font-size:10px;font-weight:bold;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="background:red;color:#fff;padding:10px;text-decoration:none;border-radius:4px;font-size:10px;font-weight:bold;">DEL</a></div></div>""" for v in videos])
    p_btn = f"<a href='/?next={new_c}&q={q}' style='display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;margin:10px;border-radius:5px;font-weight:bold;'>NEXT VIDEOS ↓</a>" if new_c else ""
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a></div><form style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search..." style="flex:1;padding:8px;border:none;border-radius:4px 0 0 4px;"><button style="background:#333;color:#fff;padding:8px 15px;border:none;">GO</button></form></div>{v_html}{p_btn}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_html = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:5px;"><b style="font-size:13px;color:#e74c3c;display:block;margin-bottom:8px;">{f["name"].upper()}</b><div style="display:flex;gap:4px;"><a href="/view_pdf?name={f["name"]}" style="flex:2;background:#e74c3c;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;font-size:11px;">OPEN PDF</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" style="flex:1;background:orange;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;font-size:11px;">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;font-size:11px;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">PDF Archive</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:8px;text-decoration:none;border-radius:4px;font-weight:bold;font-size:11px;">HOME</a><a href="/upload_pdf_page" style="flex:1;background:#fff;color:#e74c3c;padding:8px;text-decoration:none;border-radius:4px;font-weight:bold;font-size:11px;">+ UPLOAD</a></div><form style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search PDFs..." style="flex:1;padding:8px;border:none;"><button style="background:#333;color:#fff;padding:8px 15px;border:none;">GO</button></form></div>{f_html}</body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next"); ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f"""<div style="background:#000;margin-bottom:15px;text-align:center;border-bottom:2px solid #e74c3c;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;"><div style="padding:10px;background:#333;"><a href="{p["secure_url"].replace('/upload/','/upload/fl_attachment/')}" style="background:#28a745;color:#fff;text-decoration:none;padding:12px 25px;border-radius:5px;font-size:12px;font-weight:bold;">DOWNLOAD PAGE</a></div></div>""" for p in pages])
    p_btn = f"<a href='/view_pdf?name={name}&next={new_c}' style='display:block;background:#e74c3c;color:#fff;padding:18px;text-align:center;text-decoration:none;margin:10px;border-radius:5px;font-weight:bold;'>LOAD MORE →</a>" if new_c else ""
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:10px;position:sticky;top:0;z-index:100;border-bottom:2px solid #e74c3c;display:flex;align-items:center;justify-content:space-between;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;font-weight:bold;">← BACK</a> <b style="font-size:12px;color:#333;">{name.upper()}</b><span></span></div>{h}{p_btn}</body>"""

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return render_template_string("""
    <body style="padding:20px;font-family:sans-serif;text-align:center;background:#f0f0f0;">
        <div style="background:#fff;padding:25px;border-radius:12px;max-width:400px;margin:auto;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color:#e74c3c;">Add New Kitab</h3>
            <p style="font-size:12px;color:#666;margin-bottom:20px;">Android se file select karein aur upload dabayein.</p>
            <input type="file" id="f" style="width:100%;margin-bottom:20px;border:1px solid #ddd;padding:10px;border-radius:5px;"><br>
            <input type="text" id="n" placeholder="Book Name" style="width:90%;padding:12px;margin-bottom:10px;border:1px solid #ddd;border-radius:6px;"><br>
            <input type="password" id="p" placeholder="Admin Pass" style="width:90%;padding:12px;margin-bottom:20px;border:1px solid #ddd;border-radius:6px;"><br>
            <div id="progBox" style="display:none;margin-bottom:20px;">
                <div style="background:#eee;height:25px;border-radius:12px;overflow:hidden;"><div id="bar" style="width:0%;height:100%;background:#e74c3c;transition:width 0.3s;"></div></div>
                <small id="stat">0%</small>
            </div>
            <button onclick="startUp()" id="btn" style="width:100%;padding:18px;background:#e74c3c;color:#fff;border:none;border-radius:8px;font-weight:bold;font-size:16px;">UPLOAD NOW</button>
        </div>
        <script>
        function startUp(){
            var file = document.getElementById('f').files[0];
            var name = document.getElementById('n').value;
            var pw = document.getElementById('p').value;
            if(!file || !name || !pw) { alert("Details bhariye!"); return; }
            var fd = new FormData(); fd.append("file", file); fd.append("name", name); fd.append("pw", pw);
            document.getElementById('progBox').style.display='block';
            document.getElementById('btn').disabled=true;
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/do_pdf_upload", true);
            xhr.upload.onprogress = function(e){
                var p = Math.round((e.loaded/e.total)*100);
                document.getElementById('bar').style.width=p+'%';
                document.getElementById('stat').innerText="Sending to Server: "+p+"%";
            };
            xhr.onload = function(){ 
                if(xhr.status==200){ 
                    document.getElementById('stat').innerText="DONE! Now wait 2 mins for processing.";
                    setTimeout(()=> location.href="/pdf_home", 2500); 
                } else { alert("Error!"); document.getElementById('btn').disabled=false; } 
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
            pdf_path = f"tmp_{int(time.time())}.pdf"
            f.save(pdf_path)
            threading.Thread(target=background_processor, args=(pdf_path, n)).start()
            return "OK"
    return "Error", 403

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="text-align:center;padding:30px;font-family:sans-serif;"><div style="background:#fff;padding:25px;border-radius:10px;border:1px solid #ddd;"><h4>{{t.upper()}}</h4><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="Enter New Name" style="width:90%;padding:12px;margin-bottom:15px;border:1px solid #ccc;border-radius:6px;"><br>{% endif %}<input type="password" name="pw" placeholder="Admin Pass" style="width:90%;padding:12px;margin-bottom:20px;border:1px solid #ccc;border-radius:6px;"><br><button style="width:100%;padding:15px;background:#333;color:#fff;border-radius:6px;border:none;font-weight:bold;">CONFIRM</button></form></div></body>""", t=t, p=p, tp=tp)

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
                for r in res.get("resources", []): cloudinary.uploader.rename(r["public_id"], r["public_id"].replace(f"pdf_data/{p}/", f"pdf_data/{new_n}/"))
            elif t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/")
                cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect("/pdf_home")
    return "Error"

@app.route("/admin_upload")
def admin_upload():
    return render_template_string("""<body style="padding:20px;text-align:center;font-family:sans-serif;"><h3>Upload Video</h3><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" style="margin-bottom:10px;"><br><input type="text" name="name" placeholder="Name"><br><input type="password" name="pw" placeholder="Pass"><br><button style="background:#28a745;color:#fff;padding:15px;width:80%;border:none;border-radius:6px;font-weight:bold;">UPLOAD</button></form></body>""")

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "vid").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
        return redirect("/")
    return "Err"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
