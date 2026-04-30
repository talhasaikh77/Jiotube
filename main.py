import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "atif_jio_hotstar_final_v16"

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
    body { margin:0; font-family: sans-serif; background:#0f1014; color:#fff; }
    .header { background: #0f1014; padding:15px; text-align:center; border-bottom: 1px solid #252833; position:sticky; top:0; z-index:1000; }
    .card { background:#16181f; margin:12px; border-radius:8px; overflow:hidden; border: 1px solid #252833; }
    .btn { display:inline-block; padding:10px 15px; border-radius:4px; text-decoration:none; font-size:12px; font-weight:bold; color:#fff; margin:2px; border:none; cursor:pointer; text-align:center; }
    .btn-dl { background:#0072ef; } .btn-play { background:rgba(255,255,255,0.1); border:1px solid #fff; } .btn-del { background:#e50914; } .btn-ren { background:#ff9900; }
    .btn-next { background:#252833; width:92%; padding:15px; display:block; text-align:center; margin:15px auto; border-radius:8px; color:#fff; }
    .search-box { background:#252833; display:flex; margin:12px; border-radius:4px; overflow:hidden; }
    .search-box input { flex:1; border:none; padding:12px; outline:none; background:transparent; color:#fff; }
    .search-box button { background:#0072ef; color:#fff; border:none; padding:0 20px; }
    .thumb { width:100%; height:180px; object-fit:cover; background:#000; }
    .btn-group { display:flex; gap:5px; padding:10px; flex-wrap: wrap; }
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
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:12px;"><b>{v["public_id"]}</b><div class="btn-group"><a href="{v["secure_url"]}" class="btn btn-play" style="flex:1;">WATCH</a><a href="{v["secure_url"]}" download class="btn btn-dl">SAVE</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-del">DEL</a></div></div></div>''' for v in videos])
    return f'{STYLE}<div class="header"><h2 style="color:#0072ef;margin:0;">JioHotstar</h2><div style="margin-top:10px;"><a href="/admin_upload" class="btn btn-dl">+ VIDEO</a><a href="/pdf_home" class="btn btn-play">PDF BOOKS</a><a href="/ai_home" class="btn" style="background:#8e44ad;">AI SCAN</a></div></div><form class="search-box"><input name="q" placeholder="Search movies..." value="{q}"><button>GO</button></form>{v_html}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:15px;"><b>{f["name"].upper()}</b><div class="btn-group"><a href="/view_pdf?name={f["name"]}" class="btn btn-dl" style="flex:2;">OPEN BOOK</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-del">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><h2>PDF Archive</h2><a href="/" class="btn btn-play">← BACK</a><a href="/upload_pdf_page" class="btn btn-dl" style="margin-left:10px;">+ NEW PDF</a></div><form class="search-box"><input name="q" placeholder="Search books..." value="{q}"><button>FIND</button></form>{f_list}'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"><div class="btn-group"><a href="{p["secure_url"]}" download class="btn btn-dl" style="width:100%;">DOWNLOAD PAGE JPG</a></div></div>' for p in pages])
    next_btn = f"<a href='/view_pdf?name={name}&next={new_c}' class='btn btn-next'>LOAD NEXT PAGES</a>" if new_c else ""
    return f'{STYLE}<div class="header"><h3>{name.upper()}</h3><a href="/pdf_home" class="btn btn-play">← LIST</a></div>{h}{next_btn}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_login'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div class="btn-group"><a href="{i["url"]}" download class="btn btn-dl" style="width:100%;">DOWNLOAD ENHANCED JPG</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><h2>AI Scanner Pro</h2><a href="/" class="btn btn-play">← HOME</a></div><div class="card" style="padding:20px;text-align:center;"><form action="/enhance" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><button class="btn btn-dl" style="width:100%;padding:15px;">SCAN & IMPROVE</button></form></div>{h_html}<div style="text-align:center;padding:15px;"><a href="/logout" style="color:#e50914;">Logout</a></div>'

@app.route("/ai_login", methods=["GET", "POST"])
def ai_login():
    if request.method == "POST":
        u = users_col.find_one({"m": request.form.get("m")})
        if u and u['p'] == hash_pw(request.form.get("pw")):
            session.permanent = True; session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;"><h3>Login AI</h3><form method="POST"><input name="m" placeholder="Mobile"><br><br><input name="pw" type="password" placeholder="Pass"><br><br><button class="btn btn-dl" style="width:100%;">ENTER</button></form></div></body>'

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('ai_login'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", format="jpg", transformation=[{"gravity": "auto", "crop": "limit", "width": 1900}, {"effect": "improve:outdoor"}, {"effect": "sharpen:150"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

@app.route("/admin_upload")
def admin_upload(): return render_template_string(f'{STYLE}<div class="header"><h2>Upload</h2></div><form action="/do_up" method="POST" enctype="multipart/form-data" class="card" style="padding:20px;text-align:center;"><input type="file" name="file"><br><input name="name" placeholder="Title"><br><input name="pw" type="password" placeholder="Pass"><br><button class="btn btn-dl">UPLOAD</button></form>')

@app.route("/upload_pdf_page")
def upload_pdf_page(): return render_template_string(f'{STYLE}<div class="header"><h2>New PDF</h2></div><form action="/do_pdf_upload" method="POST" enctype="multipart/form-data" class="card" style="padding:20px;text-align:center;"><input type="file" name="file"><br><input name="name" placeholder="Book Name"><br><input name="pw" type="password" placeholder="Pass"><br><button class="btn btn-dl">START</button></form>')

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
            def process_pdf(pdf_path, pdf_name):
                try:
                    doc = fitz.open(pdf_path)
                    for i in range(len(doc)):
                        page = doc.load_page(i)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img_path = f"p{i+1}_{pdf_name}.jpg"; pix.save(img_path)
                        cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image")
                        os.remove(img_path)
                    doc.close(); os.remove(pdf_path)
                except: pass
            threading.Thread(target=process_pdf, args=(p_path, n)).start()
    return redirect("/pdf_home")

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string(f'{STYLE}<div class="card" style="padding:25px;text-align:center;"><h3>Confirm Delete?</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}"><input name="pw" type="password" placeholder="Admin Pass"><br><br><button class="btn btn-del">DELETE NOW</button></form></div>', p=p, t=t, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video": cloudinary.uploader.destroy(p, resource_type="video", invalidate=True)
        else:
            for rt in ["image", "video", "raw"]:
                try: cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type=rt, invalidate=True)
                except: pass
            try: cloudinary.api.delete_folder(f"pdf_data/{p}")
            except: pass
        return redirect("/pdf_home" if tp=="pdf" else "/")
    return "Wrong Pass"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
