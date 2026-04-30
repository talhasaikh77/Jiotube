import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi, requests
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_hotstar_ultra_v28_final_stable"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30 

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, ai_col = db['users'], db['ai_history']
except: print("DB Connection Error")

ADMIN_PASSWORD = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# --- Background Workers ---
def full_bg_pdf(file_path, unique_name):
    try:
        cloudinary.uploader.upload(file_path, resource_type="raw", public_id="source", folder=f"pdf_data/{unique_name}")
        doc = fitz.open(file_path)
        for i in range(len(doc)):
            pix = doc.load_page(i).get_pixmap(matrix=fitz.Matrix(2, 2))
            img_p = f"p{i+1:03d}.jpg"; pix.save(img_p)
            cloudinary.uploader.upload(img_p, public_id=f"p{i+1:03d}", folder=f"pdf_data/{unique_name}")
            if os.path.exists(img_p): os.remove(img_p)
        doc.close()
        if os.path.exists(file_path): os.remove(file_path)
    except: pass

def bg_pdf_rename(old_folder, new_folder_name):
    try:
        new_folder_full = f"{new_folder_name}__{int(time.time())}"
        res = cloudinary.api.resources(prefix=f"pdf_data/{old_folder}/", type="upload", max_results=500)
        for r in res.get("resources", []):
            old_id = r['public_id']
            new_id = old_id.replace(f"pdf_data/{old_folder}", f"pdf_data/{new_folder_full}")
            cloudinary.uploader.rename(old_id, new_id)
        # Also move the raw source file
        try: cloudinary.uploader.rename(f"pdf_data/{old_folder}/source", f"pdf_data/{new_folder_full}/source", resource_type="raw")
        except: pass
    except: pass

def bg_pdf_delete(folder_name):
    try:
        cloudinary.api.delete_resources_by_prefix(f"pdf_data/{folder_name}/")
        time.sleep(2)
        try: cloudinary.api.delete_folder(f"pdf_data/{folder_name}")
        except: pass
    except: pass

# --- UI Styles ---
STYLE = """<style>
    :root { --jio-blue: #0072ef; --bg: #0f1014; --card: #16181f; --border: #252833; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color:#fff; }
    .header { background: var(--bg); padding:15px; text-align:center; border-bottom: 1px solid var(--border); position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; }
    .logo { color: var(--jio-blue); font-weight: bold; font-size: 22px; text-decoration:none; }
    .card { background: var(--card); margin:12px; border-radius:12px; overflow:hidden; border: 1px solid var(--border); }
    .btn { display:inline-block; padding:12px 15px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600; color:#fff; border:none; cursor:pointer; text-align:center; transition: 0.3s; }
    .btn-jio { background: var(--jio-blue); } .btn-outline { background:transparent; border:1px solid #fff; } .btn-danger { background:#e50914; } .btn-ren { background:#ff9900; }
    .btn-next { background: var(--border); width:90%; padding:15px; display:block; text-align:center; margin:15px auto; border-radius:10px; color:#fff; }
    .search-box { background: var(--border); display:flex; margin:12px; border-radius:8px; overflow:hidden; border: 1px solid #333; }
    .search-box input { flex:1; border:none; padding:12px; outline:none; background:transparent; color:#fff; }
    .search-box button { background: var(--jio-blue); color:#fff; border:none; padding:0 20px; }
    input[type="text"], input[type="password"], input[type="file"] { width:90%; padding:12px; margin:8px 0; border-radius:6px; border:1px solid var(--border); background:#1c1e26; color:#fff; }
    #progress-wrapper { display:none; padding:20px; text-align:center; }
    #progress-bar { width: 0%; height: 8px; background: var(--jio-blue); border-radius: 4px; transition: width 0.2s; }
</style>
<script>
function startUp(form, target) {
    const fd = new FormData(form);
    const xhr = new XMLHttpRequest();
    document.getElementById('progress-wrapper').style.display = 'block';
    document.getElementById('upload-form').style.display = 'none';
    xhr.upload.addEventListener('progress', e => {
        const p = Math.round((e.loaded / e.total) * 100);
        document.getElementById('progress-bar').style.width = p + '%';
    });
    xhr.onreadystatechange = () => { if (xhr.readyState === 4) window.location.href = target; };
    xhr.open('POST', form.action, true);
    xhr.send(fd);
    return false;
}
</script>"""

# --- Routes ---
@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:12px;"><b>{v["public_id"]}</b><div class="action-bar"><a href="{v["secure_url"]}" class="btn btn-outline" style="flex:1;">WATCH</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" class="btn btn-ren">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-danger">DEL</a></div></div></div>''' for v in videos])
    nb = f'<a href="/?next={new_c}&q={q}" class="btn btn-next">LOAD MORE</a>' if new_c else ""
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioTube</a><div><a href="/pdf_home" class="btn btn-outline">PDF</a> <a href="/ai_home" class="btn btn-jio">AI</a></div></div><form class="search-box"><input name="q" placeholder="Search..." value="{q}"><button>GO</button></form><div style="padding:0 12px;"><a href="/admin_upload" class="btn btn-jio">+ VIDEO</a></div>{v_html}{nb}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:15px;"><b>{f["name"].split("__")[0].upper()}</b><div class="action-bar"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:2;">OPEN</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" class="btn btn-ren">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-danger">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioPDF</a><a href="/upload_pdf_page" class="btn btn-jio">+ NEW BOOK</a></div><form class="search-box"><input name="q" placeholder="Search books..." value="{q}"><button>FIND</button></form>{f_list}'

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f, n = request.files.get("file"), request.form.get("name").replace(" ","_")
        if f:
            u_n = f"{n}__{int(time.time())}"; t_p = f"t_{u_n}.pdf"; f.save(t_p)
            threading.Thread(target=full_bg_pdf, args=(t_p, u_n)).start()
            return "OK"
    return "Error", 400

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "delete": cloudinary.uploader.destroy(p, resource_type="video", invalidate=True)
            elif t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video", invalidate=True)
            return redirect("/")
        else:
            if t == "rename":
                new_val = request.form.get("new").replace(" ","_")
                threading.Thread(target=bg_pdf_rename, args=(p, new_val)).start()
            elif t == "delete":
                threading.Thread(target=bg_pdf_delete, args=(p,)).start()
            return redirect(url_for('pdf_home'))
    return "Wrong PIN"

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"><div class="action-bar"><a href="{p["secure_url"]}" download class="btn btn-jio" style="width:100%;">SAVE</a></div></div>' for p in pages])
    nb = f"<a href='/view_pdf?name={name}&next={new_c}' class='btn btn-next'>NEXT</a>" if new_c else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">← BACK</a><b>{name.split("__")[0]}</b></div>{h}{nb}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(20))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div class="action-bar"><a href="{i["url"]}" download class="btn btn-jio" style="flex:1;">SAVE</a><a href="/ai_del?id={str(i["_id"])}" class="btn btn-danger">DEL</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioAI</a><a href="/logout" class="btn btn-danger">LOGOUT</a></div><div class="card" style="padding:20px;text-align:center;"><form action="/enhance" method="POST" enctype="multipart/form-data"><h3>Scan Image</h3><input type="file" name="file" required><br><button class="btn btn-jio" style="width:90%;margin-top:10px;">ENHANCE NOW</button></form></div>{h_html}'

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if not users_col.find_one({"m": m}): users_col.insert_one({"m": m, "p": hash_pw(p)})
            return render_template_string(f'{STYLE}<div class="card" style="padding:20px;text-align:center;"><h3>Success!</h3><p>Account Created.</p><a href="/ai_auth" class="btn btn-jio">LOGIN</a></div>')
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;"><h2>JioAI</h2><form method="POST"><input name="m" placeholder="Mobile / Username" required><br><input name="pw" type="password" placeholder="Password" required><br><br><button name="act" value="log" class="btn btn-jio" style="width:48%;">LOGIN</button> <button name="act" value="reg" class="btn btn-outline" style="width:48%;color:#0072ef;border-color:#0072ef;">SIGN UP</button></form></div></body>'

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[{"width": 1800, "crop": "limit"}, {"effect": "improve"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

@app.route("/admin_upload")
def admin_upload():
    return f'{STYLE}<div class="card" style="padding:20px;text-align:center;"><div id="progress-wrapper"><div id="progress-bar"></div><p>Sending to Server...</p></div><form id="upload-form" action="/do_up" method="POST" enctype="multipart/form-data" onsubmit="return startUp(this, \'/\')"><h3>Upload Video</h3><input type="file" name="file" required><br><input name="name" placeholder="Title"><br><input name="pw" type="password" placeholder="PIN"><br><button class="btn btn-jio">UPLOAD</button></form></div>'

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return f'{STYLE}<div class="card" style="padding:20px;text-align:center;"><div id="progress-wrapper"><div id="progress-bar"></div><p>Sending to Server...</p></div><form id="upload-form" action="/do_pdf_upload" method="POST" enctype="multipart/form-data" onsubmit="return startUp(this, \'/pdf_home\')"><h3>New Book</h3><input type="file" name="file" required><br><input name="name" placeholder="Name"><br><input name="pw" type="password" placeholder="PIN"><br><button class="btn btn-jio">UPLOAD</button></form></div>'

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f, v = request.files.get("file"), request.form.get("name").replace(" ","_")
        if f:
            t_p = f"t_{v}.mp4"; f.save(t_p)
            threading.Thread(target=full_bg_video, args=(t_p, v)).start()
            return "OK"
    return "Error", 400

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string("""<style>:root{--bg:#0f1014;--card:#16181f;--jio-blue:#0072ef}body{background:var(--bg);color:#fff;font-family:sans-serif}.card{background:var(--card);margin:50px auto;padding:30px;width:80%;border-radius:12px;text-align:center}.btn-danger{background:#e50914;color:#fff;padding:10px;border:none;border-radius:6px;width:100%;cursor:pointer}</style><div class="card"><h3>Admin: {{t|upper}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=='rename' %}<input name="new" placeholder="New Name" required style="width:90%;padding:10px;margin-bottom:10px;"><br>{% endif %}<input name="pw" type="password" placeholder="PIN" required style="width:90%;padding:10px;"><br><br><button class="btn-danger">CONFIRM</button></form></div>""", p=p, t=t, tp=tp)

@app.route("/ai_del")
def ai_del():
    ai_col.delete_one({"_id": ObjectId(request.args.get("id")), "u": session.get('u')})
    return redirect(url_for('ai_home'))

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
