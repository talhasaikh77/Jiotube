import os, time, threading, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api
import fitz # PyMuPDF

app = Flask(__name__)
app.secret_key = "atif_mega_key_786"

# Fix Details (No need to change)
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:wzMuEHK9QV7cZbkv@cluster0.udiyfhu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['Atif_AI_Database']
users_col = db['users']
ADMIN_PASSWORD = "809047"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# --- JIO TUBE & PDF LOGIC (OLD SYSTEM) ---
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
    next_btn = f"<a href='/?next={new_c}&q={q}' style='display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;font-weight:bold;margin:10px;border-radius:5px;'>LOAD NEXT VIDEOS ↓</a>" if new_c else ""
    
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ UPLOAD</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a><a href="/ai_login" style="flex:1;background:#9b59b6;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">AI ENHANCE</a></div><form action="/" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search..." style="flex:1;padding:8px;border:none;"><button style="background:#333;color:#fff;padding:8px 15px;border:none;">GO</button></form></div>{v_list}{next_btn}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:5px;"><b style="font-size:13px;display:block;color:#e74c3c;margin-bottom:8px;">{f["name"].upper()}</b><div style="display:flex;gap:4px;"><a href="/view_pdf?name={f["name"]}" style="flex:2;background:#e74c3c;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;font-weight:bold;">OPEN PDF</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="flex:1;background:red;color:#fff;padding:10px;text-align:center;text-decoration:none;border-radius:4px;font-size:11px;font-weight:bold;">DEL</a></div></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">PDF Viewer</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:8px;text-decoration:none;font-size:11px;font-weight:bold;">HOME</a><a href="/upload_pdf_page" style="flex:1;background:#fff;color:#e74c3c;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ NEW PDF</a></div><form action="/pdf_home" style="margin-top:8px;display:flex;"><input type="text" name="q" value="{q}" placeholder="Search..." style="flex:1;padding:8px;border:none;"><button style="background:#333;color:#fff;padding:8px 15px;border:none;">GO</button></form></div>{f_list}</body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next"); ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f"""<div style="background:#000;margin-bottom:15px;text-align:center;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;display:block;"><div style="padding:10px;background:#333;"><a href="{p["secure_url"].rsplit(".", 1)[0]}.jpg" style="background:#28a745;color:#fff;font-size:11px;text-decoration:none;padding:8px 20px;border-radius:5px;font-weight:bold;">DOWNLOAD</a></div></div>""" for p in pages])
    nb = f"<a href='/view_pdf?name={name}&next={new_c}' style='display:block;background:#e74c3c;color:#fff;padding:18px;text-align:center;text-decoration:none;font-weight:bold;margin:10px;border-radius:5px;'>NEXT 10 PAGES →</a>" if new_c else ""
    return f"""<body style="margin:0;background:#111;"><div style="background:#fff;padding:10px;display:flex;justify-content:space-between;position:sticky;top:0;z-index:100;border-bottom:2px solid #e74c3c;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;font-weight:bold;">← BACK</a><b style="font-size:12px;">{name.upper()}</b><span></span></div>{h}{nb}</body>"""

# --- NEW AI ENHANCER LOGIN SYSTEM ---
@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        m = request.form.get("mobile"); p = request.form.get("pw")
        u = users_col.find_one({"mobile": m})
        if u and u['password'] == hash_pw(p):
            session['user_id'] = str(u['_id']); session.permanent = True
            return redirect(url_for('ai_home'))
        return "Ghalat Details! <a href='/ai_login'>Try Again</a>"
    return render_template_string('<body style="padding:20px;font-family:sans-serif;text-align:center;"><h3>AI Enhancer Login</h3><form method="POST"><input type="number" name="mobile" placeholder="Mobile" style="width:100%;padding:12px;margin-bottom:10px;"><br><input type="password" name="pw" placeholder="Pass" style="width:100%;padding:12px;margin-bottom:10px;"><br><button style="width:100%;padding:15px;background:#9b59b6;color:#fff;border:none;">LOGIN</button></form><p>New? <a href="/ai_register">Register</a></p><br><a href="/">Back to Home</a></body>')

@app.route("/ai_register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        m = request.form.get("mobile"); p = request.form.get("pw")
        if users_col.find_one({"mobile": m}): return "Number exists!"
        users_col.insert_one({"mobile": m, "password": hash_pw(p)})
        return redirect(url_for('login'))
    return render_template_string('<body style="padding:20px;font-family:sans-serif;text-align:center;"><h3>Register AI Account</h3><form method="POST"><input type="number" name="mobile" placeholder="Mobile" style="width:100%;padding:12px;margin-bottom:10px;"><br><input type="password" name="pw" placeholder="Create Pass" style="width:100%;padding:12px;margin-bottom:10px;"><br><button style="width:100%;padding:15px;background:#28a745;color:#fff;border:none;">REGISTER</button></form></body>')

@app.route("/ai_home")
def ai_home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template_string('<body style="padding:20px;text-align:center;font-family:sans-serif;"><h3>AI Panel</h3><p>Salam!</p><a href="/enhance_upload" style="display:block;background:#9b59b6;color:#fff;padding:20px;margin-bottom:10px;text-decoration:none;border-radius:10px;">+ ENHANCE PHOTO</a><a href="/ai_history" style="display:block;background:#333;color:#fff;padding:20px;text-decoration:none;border-radius:10px;">HISTORY</a><br><a href="/">HOME</a> | <a href="/logout">LOGOUT</a></body>')

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

@app.route("/admin_upload")
def admin_upload(): return render_template_string('<body><h3>Video Upload</h3><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="name" placeholder="Name"><input type="password" name="pw" placeholder="Pass"><button>UP</button></form></body>')

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "vid").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
        return redirect("/")
    return "Err"

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string('<body><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name">{% endif %}<input type="password" name="pw" placeholder="Admin Pass"><button>OK</button></form></body>', t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t = request.form.get("task"); p = request.form.get("pid"); tp = request.form.get("type")
        if tp == "video":
            if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
            elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
            return redirect("/")
        else:
            if t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/")
                cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect("/pdf_home")
    return "Err"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
