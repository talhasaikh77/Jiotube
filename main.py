import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "atif_ultimate_v11"

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

# Universal Style
STYLE = """<style>
    body { margin:0; font-family:sans-serif; background:#f0f2f5; color:#1c1e21; }
    .header { background: linear-gradient(135deg, #1e3c72, #2a5298); color:#fff; padding:15px; text-align:center; box-shadow:0 2px 10px rgba(0,0,0,0.2); position:sticky; top:0; z-index:1000; }
    .card { background:#fff; margin:10px; border-radius:12px; overflow:hidden; box-shadow:0 4px 15px rgba(0,0,0,0.08); border-bottom:4px solid #0078d7; }
    .btn { display:inline-block; padding:8px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:bold; color:#fff; margin:2px; transition:0.2s; border:none; cursor:pointer; }
    .btn-dl { background:#28a745; } .btn-play { background:#0078d7; } .btn-del { background:#e74c3c; } .btn-ren { background:#f39c12; } .btn-next { background:#333; width:92%; padding:15px; display:block; text-align:center; margin:15px auto; border-radius:10px; }
    .search-box { background:#fff; display:flex; margin:12px; border-radius:30px; overflow:hidden; border:1px solid #ddd; box-shadow:0 2px 5px rgba(0,0,0,0.05); }
    .search-box input { flex:1; border:none; padding:12px 18px; outline:none; font-size:14px; }
    .search-box button { background:#0078d7; color:#fff; border:none; padding:0 20px; font-weight:bold; }
    .thumb { width:100%; height:160px; object-fit:fill; background:#000; display:block; }
    .footer-nav { background:#fff; padding:15px; text-align:center; border-top:1px solid #ddd; margin-top:20px; }
</style>"""

# --- PDF Background Engine ---
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
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image", transformation=[{"quality":"auto"}])
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
    
    v_html = "".join([f"""<div class="card">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb">
        <div style="padding:12px;"><b>{v["public_id"]}</b><br><br>
            <div style="display:flex; gap:4px;">
                <a href="{v["secure_url"]}" class="btn btn-play" style="flex:1;text-align:center;">OPEN</a>
                <a href="{v["secure_url"]}" download class="btn btn-dl" style="flex:1;text-align:center;">SAVE</a>
            </div>
            <div style="display:flex; gap:4px; margin-top:5px;">
                <a href="/modify?task=rename&pid={v["public_id"]}&type=video" class="btn btn-ren" style="flex:1;text-align:center;">RENAME</a>
                <a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-del" style="flex:1;text-align:center;">DELETE</a>
            </div>
        </div>
    </div>""" for v in videos])
    
    next_btn = f'<a href="/?next={new_c}&q={q}" class="btn btn-next">LOAD NEXT VIDEOS ↓</a>' if new_c else ""
    return f"""{STYLE}<div class="header"><h2>JioTube Video</h2><div style="margin-top:8px;"><a href="/admin_upload" class="btn btn-dl">+ UPLOAD</a><a href="/pdf_home" class="btn btn-del">PDF VIEWER</a><a href="/ai_home" class="btn" style="background:#9b59b6;">AI SCANNER</a></div></div>
    <form class="search-box"><input name="q" placeholder="Search videos..." value="{q}"><button>GO</button></form>
    {v_html}{next_btn}"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    
    f_list = "".join([f"""<div class="card" style="border-left:8px solid #e74c3c;">
        <div style="padding:15px;"><b style="color:#c0392b; font-size:15px;">{f["name"].upper()}</b><br><br>
            <div style="display:flex; gap:4px;">
                <a href="/view_pdf?name={f["name"]}" class="btn btn-play" style="flex:2;text-align:center;">OPEN KITAB</a>
                <a href="/modify?task=rename&pid={f["name"]}&type=pdf" class="btn btn-ren" style="flex:1;text-align:center;">RENAME</a>
                <a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-del" style="flex:1;text-align:center;">DELETE</a>
            </div>
        </div>
    </div>""" for f in folders if q in f["name"].lower()])
    
    return f"""{STYLE}<div class="header" style="background:#c0392b;"><h2>PDF Search Engine</h2><div style="margin-top:8px;"><a href="/upload_pdf_page" class="btn btn-dl">+ UPLOAD PDF</a><a href="/" class="btn" style="background:#333;">VIDEO HOME</a><a href="/ai_home" class="btn" style="background:#9b59b6;">AI MACHINE</a></div></div>
    <form class="search-box"><input name="q" placeholder="Search Books..." value="{q}"><button style="background:#c0392b;">FIND</button></form>
    {f_list if f_list else "<p style='text-align:center;'>No Books Found</p>"}"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"><div style="padding:10px;text-align:center;"><a href="{p["secure_url"]}" download class="btn btn-dl" style="width:80%;">SAVE PAGE JPG</a></div></div>' for p in pages])
    next_btn = f"<a href='/view_pdf?name={name}&next={new_c}' class='btn btn-next' style='background:#e74c3c;'>LOAD NEXT 10 PAGES →</a>" if new_c else ""
    return f'{STYLE}<div class="header" style="background:#333;"><h3>{name.upper()}</h3><a href="/pdf_home" style="color:#fff;text-decoration:none;">← BACK TO LIST</a></div>{h}{next_btn}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_login'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div style="padding:10px;text-align:center;"><a href="{i["url"]}" download class="btn btn-dl">DOWNLOAD JPG</a></div></div>' for i in history])
    return f"""{STYLE}<div class="header" style="background:#8e44ad;"><h2>AI Machine Pro</h2><div style="margin-top:8px;"><a href="/" class="btn btn-play">VIDEO</a><a href="/pdf_home" class="btn btn-del">PDF</a></div></div>
    <div class="card" style="padding:20px;text-align:center;">
        <form action="/enhance" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required style="margin-bottom:10px;"><br>
            <button class="btn" style="background:#8e44ad;width:100%;padding:15px;font-size:14px;">AUTO-CROP & ENHANCE</button>
        </form>
    </div>
    {h_html}<div style="text-align:center;padding:15px;"><a href="/logout" style="color:red;font-weight:bold;">Logout Account</a></div>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('ai_login'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", format="jpg", transformation=[{"gravity": "auto", "crop": "limit", "width": 1900}, {"effect": "improve:outdoor"}, {"effect": "sharpen:150"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

@app.route("/ai_login", methods=["GET", "POST"])
def ai_login():
    if request.method == "POST":
        u = users_col.find_one({"m": request.form.get("m")})
        if u and u['p'] == hash_pw(request.form.get("pw")):
            session.permanent = True; session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="background:#1e3c72;display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;border:none;"><h3>AI Account Login</h3><form method="POST"><input name="m" placeholder="Mobile" style="width:100%;padding:12px;margin:5px 0;border:1px solid #ddd;border-radius:6px;"><br><input name="pw" type="password" placeholder="Password" style="width:100%;padding:12px;margin:5px 0;border:1px solid #ddd;border-radius:6px;"><br><button class="btn btn-play" style="width:100%;padding:15px;margin-top:10px;">LOGIN NOW</button></form><br><a href="/ai_register" style="color:#666;font-size:12px;">Create New Account</a></div></body>'

@app.route("/ai_register", methods=["GET", "POST"])
def ai_register():
    if request.method == "POST":
        m, p = request.form.get("m"), request.form.get("pw")
        if users_col.find_one({"m": m}): return "Number Already Registered!"
        users_col.insert_one({"m": m, "p": hash_pw(p)})
        return "Registration Success! <a href='/ai_login'>Login Here</a>"
    return f'{STYLE}<body style="background:#28a745;display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;border:none;"><h3>Create AI Account</h3><form method="POST"><input name="m" placeholder="Enter Mobile Number" style="width:100%;padding:12px;margin:5px 0;border:1px solid #ddd;border-radius:6px;"><br><input name="pw" type="password" placeholder="Set Password" style="width:100%;padding:12px;margin:5px 0;border:1px solid #ddd;border-radius:6px;"><br><button class="btn btn-dl" style="width:100%;padding:15px;margin-top:10px;">SIGN UP</button></form></div></body>'

@app.route("/admin_upload")
def admin_upload(): return render_template_string(f'{STYLE}<div class="header"><h2>Upload Video</h2></div><div class="card" style="padding:25px;text-align:center;"><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><input name="name" placeholder="Video Title" style="width:100%;padding:10px;"><br><br><input name="pw" type="password" placeholder="Admin Pass" style="width:100%;padding:10px;"><br><br><button class="btn btn-play" style="width:100%;padding:15px;">START UPLOAD</button></form></div>')

@app.route("/upload_pdf_page")
def upload_pdf_page(): return render_template_string(f'{STYLE}<div class="header" style="background:#c0392b;"><h2>Upload PDF Kitab</h2></div><div class="card" style="padding:25px;text-align:center;"><form action="/do_pdf_upload" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><input name="name" placeholder="Book Name" style="width:100%;padding:10px;"><br><br><input name="pw" type="password" placeholder="Admin Pass" style="width:100%;padding:10px;"><br><br><button class="btn btn-del" style="width:100%;padding:15px;">CONVERT & UPLOAD</button></form></div>')

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
    return render_template_string(f'{STYLE}<div class="header"><h2>Confirm Action</h2></div><div class="card" style="padding:25px;text-align:center;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{{% if t=="rename" %}}<input name="new" placeholder="Enter New Name" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;"><br><br>{{% endif %}}<input name="pw" type="password" placeholder="Admin Password" style="width:100%;padding:12px;border:1px solid #ddd;border-radius:6px;"><br><br><button class="btn btn-del" style="width:100%;padding:15px;font-size:14px;">EXECUTE NOW</button></form></div>', t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
            elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
            return redirect("/")
        else:
            if t == "rename":
                # Rename PDF folder by renaming its resources (complex in Cloudinary API, but doable)
                res = cloudinary.api.resources(prefix=f"pdf_data/{p}/")
                new_n = request.form.get("new").replace(" ","_")
                for r in res.get("resources", []):
                    old_id = r['public_id']
                    new_id = old_id.replace(f"pdf_data/{p}/", f"pdf_data/{new_n}/")
                    cloudinary.uploader.rename(old_id, new_id)
            elif t == "delete":
                for r_type in ["image", "video", "raw"]:
                    try: cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type=r_type)
                    except: pass
                try: cloudinary.api.delete_folder(f"pdf_data/{p}")
                except: pass
            return redirect("/pdf_home")
    return "Wrong Pass"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
