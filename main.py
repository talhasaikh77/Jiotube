import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "atif_force_wipe_v12"

# Database & Cloudinary
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, ai_col = db['users'], db['ai_history']
except: print("DB Connection Error")

ADMIN_PASSWORD = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    body { margin:0; font-family:sans-serif; background:#f0f2f5; color:#1c1e21; }
    .header { background: linear-gradient(135deg, #1e3c72, #2a5298); color:#fff; padding:15px; text-align:center; box-shadow:0 2px 10px rgba(0,0,0,0.2); position:sticky; top:0; z-index:1000; }
    .card { background:#fff; margin:10px; border-radius:12px; overflow:hidden; box-shadow:0 4px 15px rgba(0,0,0,0.08); border-bottom:4px solid #0078d7; }
    .btn { display:inline-block; padding:8px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:bold; color:#fff; margin:2px; transition:0.2s; border:none; cursor:pointer; }
    .btn-dl { background:#28a745; } .btn-play { background:#0078d7; } .btn-del { background:#e74c3c; } .btn-ren { background:#f39c12; }
    .search-box { background:#fff; display:flex; margin:12px; border-radius:30px; overflow:hidden; border:1px solid #ddd; }
    .search-box input { flex:1; border:none; padding:12px 18px; outline:none; }
    .search-box button { background:#0078d7; color:#fff; border:none; padding:0 20px; font-weight:bold; }
</style>"""

def process_pdf_background(pdf_path, pdf_name):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            zoom = 1900 / page.rect.width
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_path = f"p{i+1}_{pdf_name}.jpg"
            pix.save(img_path)
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image")
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
    v_html = "".join([f'<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;height:160px;object-fit:fill;"><div style="padding:10px;"><b>{v["public_id"]}</b><br><br><div style="display:flex;gap:4px;"><a href="{v["secure_url"]}" class="btn btn-play" style="flex:1;text-align:center;">OPEN</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-del" style="flex:1;text-align:center;">DELETE</a></div></div></div>' for v in videos])
    return f'{STYLE}<div class="header"><h2>JioTube</h2><div style="margin-top:8px;"><a href="/admin_upload" class="btn btn-dl">+ VIDEO</a><a href="/pdf_home" class="btn btn-del">PDF LIST</a></div></div><form class="search-box"><input name="q" placeholder="Search..." value="{q}"><button>GO</button></form>{v_html}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div class="card" style="border-left:8px solid #e74c3c;padding:15px;"><b style="color:#c0392b;">{f["name"].upper()}</b><br><br><div style="display:flex;gap:4px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-play" style="flex:2;text-align:center;">OPEN</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-del" style="flex:1;text-align:center;">DELETE</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header" style="background:#c0392b;"><h2>PDF List</h2><a href="/" style="color:#fff;">← HOME</a><a href="/upload_pdf_page" class="btn btn-dl" style="margin-left:10px;">+ NEW PDF</a></div><form class="search-box"><input name="q" placeholder="Search Books..." value="{q}"><button style="background:#c0392b;">FIND</button></form>{f_list}'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"></div>' for p in pages])
    return f'{STYLE}<div class="header" style="background:#333;"><h3>{name.upper()}</h3><a href="/pdf_home" style="color:#fff;">← BACK</a></div>{h}'

@app.route("/admin_upload")
def admin_upload(): return render_template_string(f'{STYLE}<div class="header"><h2>Upload</h2></div><form action="/do_up" method="POST" enctype="multipart/form-data" class="card" style="padding:20px;text-align:center;"><input type="file" name="file"><br><input name="name" placeholder="Name"><br><input name="pw" type="password" placeholder="Pass"><br><button class="btn btn-play">UPLOAD</button></form>')

@app.route("/upload_pdf_page")
def upload_pdf_page(): return render_template_string(f'{STYLE}<div class="header" style="background:#c0392b;"><h2>New PDF</h2></div><form action="/do_pdf_upload" method="POST" enctype="multipart/form-data" class="card" style="padding:20px;text-align:center;"><input type="file" name="file"><br><input name="name" placeholder="Book Name"><br><input name="pw" type="password" placeholder="Pass"><br><button class="btn btn-del">START</button></form>')

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "video").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
    return redirect("/")

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("name").replace(" ","_")
        if f:
            p_path = f"temp_{int(time.time())}.pdf"; f.save(p_path)
            threading.Thread(target=process_pdf_background, args=(p_path, n)).start()
    return redirect("/pdf_home")

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string(f'{STYLE}<div class="card" style="padding:20px;text-align:center;"><h3>Confirm Delete?</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="type" value="{{tp}}"><input name="pw" type="password" placeholder="Pass"><br><br><button class="btn btn-del">YES, DELETE</button></form></div>', p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        p, tp = request.form.get("pid"), request.form.get("type")
        if tp == "video": cloudinary.uploader.destroy(p, resource_type="video")
        else:
            # Force Wipe: Image, Video, Raw sab saaf karo
            for r_type in ["image", "video", "raw"]:
                try: cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type=r_type)
                except: pass
            # Folder ko force delete karne ke liye multiple attempts
            for _ in range(3):
                try: cloudinary.api.delete_folder(f"pdf_data/{p}")
                except: time.sleep(1)
        return redirect("/pdf_home" if tp=="pdf" else "/")
    return "Wrong Pass"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
