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
    """Ye function background mein kaam karega, chahe user site band kar de"""
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            
            # --- AUTO-CROP LOGIC (Ibarat ko zoom karne ke liye) ---
            text_bbox = page.get_textbox_rects()
            if text_bbox:
                union_rect = fitz.Rect()
                for rect in text_bbox: union_rect.include_rect(rect)
                # Margin safety (5px)
                union_rect.x0 = max(0, union_rect.x0 - 5)
                union_rect.y0 = max(0, union_rect.y0 - 5)
                union_rect.x1 = min(page.rect.width, union_rect.x1 + 5)
                union_rect.y1 = min(page.rect.height, union_rect.y1 + 5)
                page.set_cropbox(union_rect)

            # Optimized Resolution for Jio Bharat
            pix = page.get_pixmap(dpi=145) 
            img_path = f"temp_p{i+1}_{pdf_name}.jpg"
            pix.save(img_path, "jpg")
            
            # Cloudinary par upload
            cloudinary.uploader.upload(img_path, 
                                       public_id=f"p{i+1}", 
                                       folder=f"pdf_data/{pdf_name}", 
                                       resource_type="image", 
                                       quality="auto:good")
            
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
    except Exception as e:
        print(f"Background Error: {e}")
    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=15)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
    except: videos = []
    
    v_list = "".join([f"""<div style="background:#fff;border-bottom:1px solid #ccc;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:140px;object-fit:cover;display:block;"><b style="font-size:12px;display:block;padding:5px;">{v["public_id"]}</b><div style="display:flex;gap:5px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:10px;text-decoration:none;font-size:11px;font-weight:bold;border-radius:4px;">PLAY</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="background:red;color:#fff;padding:10px;text-decoration:none;border-radius:4px;">DEL</a></div></div>""" for v in videos])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f4f4f4;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:10px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">+ VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">PDF VIEWER</a></div></div><div style="padding:10px;">{v_list}</div></body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div style="background:#fff;border-bottom:1px solid #ddd;padding:10px;margin-bottom:5px;"><b style="font-size:13px;color:#e74c3c;">{f["name"].upper()}</b><div style="display:flex;gap:5px;margin-top:10px;"><a href="/view_pdf?name={f["name"]}" style="flex:2;background:#e74c3c;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;font-weight:bold;">OPEN KITAB</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:12px;text-align:center;text-decoration:none;border-radius:4px;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;position:sticky;top:0;"><h3 style="margin:0;">PDF Archive</h3><div style="display:flex;gap:5px;margin-top:10px;"><a href="/" style="background:#333;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">HOME</a><a href="/upload_pdf_page" style="background:#fff;color:#e74c3c;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">+ UPLOAD NEW</a></div></div><div style="padding:10px;">{f_list}</div></body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next"); ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f"""<div style="background:#000;margin-bottom:15px;text-align:center;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;display:block;"><div style="padding:10px;background:#222;"><a href="{p["secure_url"].rsplit(".", 1)[0]}.jpg" style="background:#28a745;color:#fff;text-decoration:none;padding:10px 20px;border-radius:5px;font-size:12px;font-weight:bold;">DOWNLOAD PAGE</a></div></div>""" for p in pages])
    next_btn = f"<a href='/view_pdf?name={name}&next={new_c}' style='display:block;background:#e74c3c;color:#fff;padding:15px;text-align:center;text-decoration:none;font-weight:bold;margin:10px;border-radius:5px;'>LOAD NEXT 10 PAGES →</a>" if new_c else ""
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:10px;position:sticky;top:0;border-bottom:2px solid #e74c3c;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;font-weight:bold;">← BACK TO LIST</a></div>{h}{next_btn}</body>"""

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return render_template_string("""
    <body style="padding:20px;font-family:sans-serif;text-align:center;background:#f9f9f9;">
        <div style="background:#fff;padding:25px;border:1px solid #ddd;border-radius:12px;max-width:400px;margin:auto;">
            <h3 style="color:#e74c3c;">Add New Kitab</h3>
            <p style="font-size:11px;color:#666;">File select karke "Upload" dabayein. Jab 100% ho jaye toh aap site band kar sakte hain, background mein kaam hota rahega.</p>
            <input type="file" id="file" style="width:100%;margin-bottom:15px;"><br>
            <input type="text" id="name" placeholder="Kitab ka Naam" style="width:90%;padding:12px;margin-bottom:10px;border:1px solid #ccc;border-radius:6px;"><br>
            <input type="password" id="pw" placeholder="Admin Pass" style="width:90%;padding:12px;margin-bottom:15px;border:1px solid #ccc;border-radius:6px;"><br>
            <div id="progBox" style="display:none;margin-bottom:15px;">
                <div style="background:#eee;height:24px;border-radius:12px;overflow:hidden;border:1px solid #ddd;">
                    <div id="bar" style="width:0%;height:100%;background:#e74c3c;transition:width 0.3s;"></div>
                </div>
                <small id="stat" style="font-weight:bold;color:#e74c3c;margin-top:5px;display:block;">0% Sent</small>
            </div>
            <button onclick="startUp()" id="btn" style="width:100%;padding:15px;background:#e74c3c;color:#fff;border:none;border-radius:6px;font-weight:bold;font-size:16px;">START UPLOAD</button>
        </div>
        <script>
        function startUp() {
            var f = document.getElementById('file').files[0];
            var n = document.getElementById('name').value;
            var p = document.getElementById('pw').value;
            if(!f || !n || !p) { alert("Sab details bhariye!"); return; }
            var fd = new FormData(); fd.append("file", f); fd.append("name", n); fd.append("pw", p);
            document.getElementById('progBox').style.display = 'block';
            document.getElementById('btn').disabled = true;
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/do_pdf_upload", true);
            xhr.upload.onprogress = function(e) {
                var pct = Math.round((e.loaded/e.total)*100);
                document.getElementById('bar').style.width = pct + '%';
                document.getElementById('stat').innerText = "Sending File: " + pct + "%";
            };
            xhr.onload = function() {
                if(xhr.status == 200) {
                    document.getElementById('stat').innerText = "SUCCESS! Background processing started. You can leave now.";
                    setTimeout(()=> location.href="/pdf_home", 2500);
                } else { alert("Error! Check Password."); document.getElementById('btn').disabled = false; }
            };
            xhr.send(fd);
        }
        </script>
    </body>
    """)

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file")
        n = request.form.get("name").replace(" ","_")
        if f:
            pdf_path = f"bk_{int(time.time())}.pdf"
            f.save(pdf_path) # Pehle server par temporary save
            # Background thread shuru karein aur free ho jayein
            threading.Thread(target=background_processor, args=(pdf_path, n)).start()
            return "OK"
    return "Auth Error", 403

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="padding:30px;text-align:center;font-family:sans-serif;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}"><p>Confirm {{t.upper()}} for: <b>{{p}}</b></p><input type="password" name="pw" placeholder="Admin Password" style="width:90%;padding:15px;margin-bottom:20px;"><br><button style="width:100%;padding:15px;background:red;color:#fff;border:none;border-radius:5px;font-weight:bold;">CONFIRM NOW</button></form></body>""", t=t, p=p, tp=tp)

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

@app.route("/admin_upload")
def admin_upload():
    return render_template_string("""
    <body style="padding:20px;text-align:center;font-family:sans-serif;">
        <h3>Upload Video</h3>
        <form action="/do_up" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" style="margin-bottom:10px;"><br>
            <input type="text" name="name" placeholder="Video Name" style="width:80%;padding:10px;margin-bottom:10px;"><br>
            <input type="password" name="pw" placeholder="Pass" style="width:80%;padding:10px;margin-bottom:10px;"><br>
            <button style="width:80%;padding:15px;background:#28a745;color:#fff;border:none;">UPLOAD VIDEO</button>
        </form>
    </body>
    """)

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "vid").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
        return redirect("/")
    return "Error"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
