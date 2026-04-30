import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_hotstar_pro_ultra_v17"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30 

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

# JioHotstar Premium UI Theme
STYLE = """<style>
    :root { --jio-blue: #0072ef; --bg: #0f1014; --card: #16181f; --border: #252833; }
    body { margin:0; font-family: 'Segoe UI', Roboto, sans-serif; background: var(--bg); color:#fff; }
    .header { background: var(--bg); padding:15px; text-align:center; border-bottom: 1px solid var(--border); position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; }
    .logo { color: var(--jio-blue); font-weight: bold; font-size: 22px; text-decoration:none; }
    .card { background: var(--card); margin:12px; border-radius:12px; overflow:hidden; border: 1px solid var(--border); transition: 0.3s; }
    .btn { display:inline-block; padding:10px 18px; border-radius:6px; text-decoration:none; font-size:13px; font-weight:600; color:#fff; border:none; cursor:pointer; transition: 0.2s; }
    .btn-jio { background: var(--jio-blue); } .btn-outline { background:transparent; border:1px solid #fff; } .btn-danger { background:#e50914; }
    .btn-next { background: var(--border); width:90%; padding:15px; display:block; text-align:center; margin:20px auto; border-radius:10px; color:#fff; font-weight:bold; }
    .search-box { background: var(--border); display:flex; margin:12px; border-radius:8px; overflow:hidden; border: 1px solid #333; }
    .search-box input { flex:1; border:none; padding:14px; outline:none; background:transparent; color:#fff; font-size:16px; }
    .search-box button { background: var(--jio-blue); color:#fff; border:none; padding:0 25px; cursor:pointer; }
    .thumb { width:100%; height:200px; object-fit:cover; background:#000; border-bottom: 1px solid var(--border); }
    .action-bar { display:flex; gap:8px; padding:12px; flex-wrap: wrap; }
    input[type="file"], input[type="text"], input[type="password"] { width:90%; padding:12px; margin:10px 0; border-radius:8px; border:1px solid var(--border); background:#050505; color:#fff; }
</style>"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:12px;"><b style="display:block;margin-bottom:10px;">{v["public_id"]}</b><div class="action-bar"><a href="{v["secure_url"]}" class="btn btn-outline" style="flex:1;text-align:center;">WATCH</a><a href="{v["secure_url"]}" download class="btn btn-jio">SAVE</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-danger">DEL</a></div></div></div>''' for v in videos])
    next_btn = f'<a href="/?next={new_c}&q={q}" class="btn btn-next">SHOW MORE VIDEOS</a>' if new_c else ""
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioTube</a><div><a href="/pdf_home" class="btn btn-outline" style="margin-right:5px;">PDF</a><a href="/ai_home" class="btn btn-jio">AI</a></div></div><form class="search-box"><input name="q" placeholder="Search movies, trailers..." value="{q}"><button>GO</button></form><div style="padding:5px;"><a href="/admin_upload" class="btn btn-jio" style="margin-left:12px;">+ UPLOAD VIDEO</a></div>{v_html}{next_btn}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:20px;"><b>{f["name"].upper()}</b><div class="action-bar" style="padding-left:0;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:2;text-align:center;">OPEN BOOK</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-danger">DEL</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" class="btn btn-outline" style="color:#ff9900;border-color:#ff9900;">RENAME</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioPDF</a><a href="/upload_pdf_page" class="btn btn-jio">+ NEW BOOK</a></div><form class="search-box"><input name="q" placeholder="Search books..." value="{q}"><button>FIND</button></form>{f_list}'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"><div class="action-bar"><a href="{p["secure_url"]}" download class="btn btn-jio" style="width:100%;text-align:center;">DOWNLOAD PAGE (1800px)</a></div></div>' for p in pages])
    next_btn = f"<a href='/view_pdf?name={name}&next={new_c}' class='btn btn-next'>NEXT 10 PAGES</a>" if new_c else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">← BACK</a><span style="font-weight:bold;">{name.upper()}</span></div>{h}{next_btn}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(20))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div class="action-bar"><a href="{i["url"]}" download class="btn btn-jio" style="flex:1;text-align:center;">SAVE</a><a href="/ai_del?id={str(i["_id"])}" class="btn btn-danger">DEL</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioAI</a><a href="/logout" class="btn btn-danger">LOGOUT</a></div><div class="card" style="padding:20px;text-align:center;"><h3>Enhance Image (1800px)</h3><form action="/enhance" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><button class="btn btn-jio" style="width:90%;padding:15px;margin-top:10px;">START ENHANCING</button></form></div>{h_html}'

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if not users_col.find_one({"m": m}): users_col.insert_one({"m": m, "p": hash_pw(p)})
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;"><h2 style="color:var(--jio-blue);">JioAI Login</h2><form method="POST"><input name="m" placeholder="Mobile Number" required><br><input name="pw" type="password" placeholder="Password" required><br><br><button name="act" value="log" class="btn btn-jio" style="width:100%;">LOGIN</button><br><button name="act" value="reg" class="btn btn-outline" style="width:100%;margin-top:10px;">REGISTER NEW ACCOUNT</button></form></div></body>'

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[{"width": 1800, "crop": "limit"}, {"effect": "improve"}, {"quality": "auto"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

@app.route("/ai_del")
def ai_del():
    ai_col.delete_one({"_id": ObjectId(request.args.get("id")), "u": session.get('u')})
    return redirect(url_for('ai_home'))

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string(f'{STYLE}<div class="card" style="padding:30px;text-align:center;"><h3>Admin Action: {t.upper()}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{"<input name=\'new\' placeholder=\'Enter New Name\' required><br>" if t=="rename" else ""}<input name="pw" type="password" placeholder="Admin PIN" required><br><br><button class="btn btn-danger" style="width:100%;padding:15px;">CONFIRM & EXECUTE</button></form><br><a href="/" style="color:#aaa;">Cancel</a></div>', p=p, t=t, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "delete": cloudinary.uploader.destroy(p, resource_type="video", invalidate=True)
            return redirect("/")
        else:
            if t == "rename":
                new_n = request.form.get("new").replace(" ","_")
                res = cloudinary.api.resources(prefix=f"pdf_data/{p}/")
                for r in res.get("resources", []):
                    cloudinary.uploader.rename(r['public_id'], r['public_id'].replace(f"pdf_data/{p}/", f"pdf_data/{new_n}/"))
            elif t == "delete":
                for rt in ["image", "video", "raw"]:
                    try: cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type=rt, invalidate=True)
                    except: pass
                try: cloudinary.api.delete_folder(f"pdf_data/{p}")
                except: pass
            return redirect("/pdf_home")
    return "Invalid Admin Password"

@app.route("/admin_upload")
def admin_upload(): return render_template_string(f'{STYLE}<div class="header"><a href="/" class="btn btn-outline">← BACK</a></div><div class="card" style="padding:20px;text-align:center;"><h3>Upload Video</h3><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><input name="name" placeholder="Title" required><br><input name="pw" type="password" placeholder="Admin PIN" required><br><button class="btn btn-jio">UPLOAD NOW</button></form></div>')

@app.route("/upload_pdf_page")
def upload_pdf_page(): return render_template_string(f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">← BACK</a></div><div class="card" style="padding:20px;text-align:center;"><h3>Upload & Convert PDF</h3><form action="/do_pdf_upload" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><input name="name" placeholder="Book Name" required><br><input name="pw" type="password" placeholder="Admin PIN" required><br><button class="btn btn-jio">START CONVERSION</button></form></div>')

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f, v = request.files.get("file"), request.form.get("name").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
    return redirect("/")

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f, n = request.files.get("file"), request.form.get("name").replace(" ","_")
        if f:
            p_path = f"temp_{int(time.time())}.pdf"; f.save(p_path)
            def process_pdf(path, name):
                try:
                    doc = fitz.open(path)
                    for i in range(len(doc)):
                        page = doc.load_page(i)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
                        img_path = f"p{i+1}.jpg"; pix.save(img_path)
                        cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{name}", resource_type="image")
                        os.remove(img_path)
                    doc.close(); os.remove(path)
                except: pass
            threading.Thread(target=process_pdf, args=(p_path, n)).start()
    return redirect("/pdf_home")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
