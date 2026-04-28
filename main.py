import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import threading
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

def process_pdf_background(pdf_path, pdf_name):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            # DPI 300 sabse high quality image generate karta hai text ke liye
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
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=50)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
    except: videos = []
    v_list = "".join([f"""<div style="background:#fff;border-bottom:1px solid #ddd;padding:8px;"><b style="font-size:12px;display:block;">{v["public_id"]}</b><div style="display:flex;gap:4px;margin-top:5px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:5px;text-decoration:none;font-size:10px;border-radius:3px;">PLAY</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:5px;text-decoration:none;font-size:10px;border-radius:3px;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:5px;text-decoration:none;font-size:10px;border-radius:3px;">DEL</a></div></div>""" for v in videos])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f0f0f0;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;"><h4 style="margin:0;">JioTube Pro</h4><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:5px;text-decoration:none;font-size:11px;border-radius:4px;">+VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:5px;text-decoration:none;font-size:11px;border-radius:4px;">PDF</a></div><form action="/" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" style="flex:1;padding:5px;border:none;"><button style="background:#333;color:#fff;border:none;padding:5px;">OK</button></form></div>{v_list}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div style="background:#fff;border-bottom:1px solid #ddd;padding:10px;"><a href="/view_pdf?name={f["name"]}" style="text-decoration:none;color:#333;font-weight:bold;font-size:12px;">{f["name"].upper()}</a><div style="display:flex;gap:5px;margin-top:5px;"><a href="/modify?task=rename&pid={f["name"]}&type=pdf" style="flex:1;background:orange;color:#fff;padding:4px;text-align:center;text-decoration:none;border-radius:3px;font-size:10px;">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:4px;text-align:center;text-decoration:none;border-radius:3px;font-size:10px;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;"><h4 style="margin:0;">PDF Archive</h4><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:5px;text-decoration:none;font-size:11px;border-radius:4px;">BACK</a><a href="/upload_pdf_page" style="flex:1;background:#fff;color:#e74c3c;padding:5px;text-decoration:none;font-size:11px;border-radius:4px;">+NEW</a></div><form action="/pdf_home" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" style="flex:1;padding:5px;border:none;"><button style="background:#333;color:#fff;border:none;padding:5px;">OK</button></form></div>{f_list}</body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=50)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
    except: pages = []
    h = "".join([f"""<div style="background:#000;margin-bottom:10px;"><img src="{p["secure_url"]}?v={int(time.time())}" style="width:100%;"><div style="text-align:center;padding:5px;"><a href="{p["secure_url"].replace("/upload/","/upload/fl_attachment/")}" style="color:#fff;font-size:10px;">Download Page</a></div></div>""" for p in pages])
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:8px;display:flex;justify-content:space-between;align-items:center;"><a href="/pdf_home" style="text-decoration:none;font-size:12px;color:#e74c3c;">← BACK</a><b style="font-size:11px;">{name[:15]}</b></div>{h}</body>"""

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="text-align:center;padding:20px;font-family:sans-serif;"><h5>{{t.upper()}}</h5><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name" style="width:90%;padding:5px;margin-bottom:10px;"><br>{% endif %}<input type="password" name="pw" placeholder="Password" style="width:90%;padding:5px;margin-bottom:10px;"><br><button style="width:100%;padding:10px;background:#333;color:#fff;border:none;">CONFIRM</button></form></body>""", t=t, p=p, tp=tp)

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
                res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{p}/")
                ids = [r["public_id"] for r in res.get("resources", [])]
                if ids: cloudinary.api.delete_resources(ids)
            return redirect("/pdf_home")
    return "Wrong Password"

@app.route("/admin_upload")
def admin_upload():
    return """<body style="padding:15px;font-family:sans-serif;text-align:center;"><h4>Upload Video</h4><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" style="margin-bottom:10px;"><br><input type="text" name="vname" placeholder="Name" style="width:90%;padding:5px;margin-bottom:10px;"><input type="password" name="pw" placeholder="Pass" style="width:90%;padding:5px;margin-bottom:10px;"><button style="width:100%;padding:10px;background:#28a745;color:#fff;border:none;">UPLOAD</button></form></body>"""

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("vname", "video").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
        return redirect("/")
    return "Error"

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return """<body style="padding:15px;font-family:sans-serif;text-align:center;"><h4>Upload PDF</h4><form action="/do_pdf_upload" method="POST" enctype="multipart/form-data"><input type="file" name="file" accept=".pdf" style="margin-bottom:10px;"><br><input type="text" name="pdf_name" placeholder="PDF Name" style="width:90%;padding:5px;margin-bottom:10px;"><input type="password" name="pw" placeholder="Pass" style="width:90%;padding:10px;margin-bottom:10px;"><button style="width:100%;padding:10px;background:#e74c3c;color:#fff;border:none;">START UPLOAD</button></form></body>"""

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("pdf_name").replace(" ","_")
        if f:
            pdf_path = f"temp_{int(time.time())}.pdf"
            f.save(pdf_path)
            threading.Thread(target=process_pdf_background, args=(pdf_path, n)).start()
            return redirect("/pdf_home")
    return "Error"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
