import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import threading
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Config
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

def background_processor(public_id, pdf_name):
    """Cloudinary se file fetch karke crop karna"""
    try:
        # Cloudinary se original PDF download karna temporary processing ke liye
        import requests
        res = cloudinary.api.resource(public_id, resource_type="raw")
        url = res['secure_url']
        pdf_path = f"process_{int(time.time())}.pdf"
        
        with requests.get(url, stream=True) as r:
            with open(pdf_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
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
        os.remove(pdf_path)
        # Original raw file delete kar dena
        cloudinary.uploader.destroy(public_id, resource_type="raw")
    except: pass

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=12, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_html = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:150px;object-fit:cover;display:block;"><b style="font-size:12px;display:block;padding:5px;">{v["public_id"]}</b><div style="display:flex;gap:4px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:10px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">PLAY</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="background:orange;color:#fff;padding:10px;text-decoration:none;border-radius:4px;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="background:red;color:#fff;padding:10px;text-decoration:none;border-radius:4px;">DEL</a></div></div>""" for v in videos])
    p_btn = f"<a href='/?next={new_c}&q={q}' style='display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;margin:10px;border-radius:5px;font-weight:bold;'>NEXT VIDEOS ↓</a>" if new_c else ""
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a></div><form style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search..." style="flex:1;padding:8px;border:none;border-radius:4px 0 0 4px;"><button style="background:#333;color:#fff;padding:8px 15px;border:none;">GO</button></form></div>{v_html}{p_btn}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_html = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:5px;"><b style="font-size:13px;color:#e74c3c;">{f["name"].upper()}</b><div style="display:flex;gap:4px;margin-top:8px;"><a href="/view_pdf?name={f["name"]}" style="flex:2;background:#e74c3c;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;">OPEN</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" style="flex:1;background:orange;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">PDF Archive</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:8px;text-decoration:none;border-radius:4px;font-weight:bold;">HOME</a><a href="/upload_pdf_page" style="flex:1;background:#fff;color:#e74c3c;padding:8px;text-decoration:none;border-radius:4px;font-weight:bold;">+ UPLOAD</a></div><form style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search PDFs..." style="flex:1;padding:8px;border:none;"><button style="background:#333;color:#fff;padding:8px 15px;border:none;">GO</button></form></div>{f_html}</body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next"); ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f"""<div style="background:#000;margin-bottom:15px;text-align:center;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;"><div style="padding:10px;background:#333;"><a href="{p["secure_url"].replace('/upload/','/upload/fl_attachment/')}" style="background:#28a745;color:#fff;text-decoration:none;padding:12px 25px;border-radius:5px;font-size:12px;font-weight:bold;">DOWNLOAD PAGE</a></div></div>""" for p in pages])
    p_btn = f"<a href='/view_pdf?name={name}&next={new_c}' style='display:block;background:#e74c3c;color:#fff;padding:18px;text-align:center;text-decoration:none;margin:10px;border-radius:5px;font-weight:bold;'>LOAD MORE →</a>" if new_c else ""
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:10px;position:sticky;top:0;border-bottom:2px solid #e74c3c;display:flex;align-items:center;justify-content:space-between;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;font-weight:bold;">← BACK</a> <b style="font-size:12px;">{name.upper()}</b><span></span></div>{h}{p_btn}</body>"""

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return render_template_string("""
    <script src="https://upload-widget.cloudinary.com/global/all.js" type="text/javascript"></script>
    <body style="padding:20px;font-family:sans-serif;text-align:center;background:#f0f0f0;">
        <div style="background:#fff;padding:25px;border-radius:12px;max-width:400px;margin:auto;">
            <h3 style="color:#e74c3c;">Direct Fast Upload</h3>
            <p style="font-size:11px;color:#666;">Ye system kabhi nahi atkega!</p>
            <input type="text" id="n" placeholder="Book Name" style="width:90%;padding:12px;margin-bottom:10px;border:1px solid #ddd;border-radius:6px;"><br>
            <input type="password" id="p" placeholder="Admin Pass" style="width:90%;padding:12px;margin-bottom:15px;border:1px solid #ddd;border-radius:6px;"><br>
            <button onclick="openWidget()" id="btn" style="width:100%;padding:15px;background:#e74c3c;color:#fff;border:none;border-radius:6px;font-weight:bold;">CHOOSE & UPLOAD PDF</button>
            <div id="stat" style="margin-top:15px;color:green;font-weight:bold;"></div>
        </div>
        <script>
        function openWidget(){
            var name = document.getElementById('n').value;
            var pw = document.getElementById('p').value;
            if(!name || pw != '809047') { alert("Name aur Pass sahi bhariye!"); return; }
            
            cloudinary.openUploadWidget({
                cloudName: 'dawterffe', 
                uploadPreset: 'ml_default',
                sources: ['local'],
                multiple: false,
                clientAllowedFormats: ["pdf"]
            }, (error, result) => {
                if (!error && result && result.event === "success") {
                    document.getElementById('stat').innerText = "Upload Done! Processing pages...";
                    fetch('/trigger_process?pid=' + result.info.public_id + '&name=' + name);
                    setTimeout(()=> location.href="/pdf_home", 3000);
                }
            });
        }
        </script>
    </body>
    """)

@app.route("/trigger_process")
def trigger_process():
    pid = request.args.get("pid")
    name = request.args.get("name").replace(" ","_")
    threading.Thread(target=background_processor, args=(pid, name)).start()
    return "OK"

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="text-align:center;padding:30px;"><div style="background:#fff;padding:25px;border-radius:10px;border:1px solid #ddd;"><h4>{{t.upper()}}</h4><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name" style="width:90%;padding:12px;margin-bottom:15px;"><br>{% endif %}<input type="password" name="pw" placeholder="Pass" style="width:90%;padding:12px;margin-bottom:20px;"><br><button style="width:100%;padding:15px;background:#333;color:#fff;">CONFIRM</button></form></div></body>""", t=t, p=p, tp=tp)

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
    return render_template_string("""<body style="padding:20px;text-align:center;"><h3>Upload Video</h3><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><br><input type="text" name="name" placeholder="Name"><br><input type="password" name="pw" placeholder="Pass"><br><button>UPLOAD</button></form></body>""")

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "vid").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
        return redirect("/")
    return "Err"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
