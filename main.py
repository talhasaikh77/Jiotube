import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "atif_old_gold_v6"

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

# --- PDF PROCESSING ---
def process_pdf_background(pdf_path, pdf_name):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            mat = fitz.Matrix(2, 2) # High Quality JPG for Jio Bharat
            pix = page.get_pixmap(matrix=mat)
            img_path = f"p{i+1}_{pdf_name}.jpg"
            pix.save(img_path)
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", resource_type="image")
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
        if os.path.exists(pdf_path): os.remove(pdf_path)
    except: pass

# --- ROUTES ---
@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    
    v_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:150px;object-fit:fill;background:#000;display:block;"><b style="font-size:12px;display:block;padding:5px;color:#333;">{v["public_id"]}</b><div style="display:flex;flex-wrap:wrap;gap:4px;padding:2px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">PLAY</a><a href="{v["secure_url"]}" download style="flex:1;background:#28a745;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">SAVE</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">DEL</a></div></div>""" for v in videos])
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ UPLOAD</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a><a href="/ai_home" style="flex:1;background:#9b59b6;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">AI MACHINE</a></div><form style="margin-top:8px;display:flex;"><input name="q" value="{q}" style="flex:1;padding:8px;border:none;border-radius:4px 0 0 4px;"><button style="background:#333;color:#fff;border:none;padding:8px 15px;border-radius:0 4px 4px 0;">GO</button></form></div>{v_list}</body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:5px;"><b>{f["name"].upper()}</b><br><br><a href="/view_pdf?name={f["name"]}" style="background:#e74c3c;color:#fff;padding:8px 15px;text-decoration:none;border-radius:4px;font-size:11px;font-weight:bold;">OPEN KITAB</a></div>""" for f in folders if q in f["name"].lower()])
    return f"""<body style="margin:0;font-family:sans-serif;background:#f9f9f9;"><div style="background:#e74c3c;color:#fff;padding:10px;text-align:center;"><h3>PDF Archive</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">HOME</a><a href="/upload_pdf_page" style="flex:1;background:#fff;color:#e74c3c;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">+ NEW PDF</a></div></div>{f_list}</body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        new_c = res.get("next_cursor")
    except: pages = []; new_c = None
    h = "".join([f'<div style="margin-bottom:15px;text-align:center;background:#fff;"><img src="{p["secure_url"]}" style="width:100%;"><br><a href="{p["secure_url"]}" download style="background:#28a745;color:#fff;padding:10px;display:block;text-decoration:none;font-weight:bold;">SAVE PAGE</a><hr></div>' for p in pages])
    next_btn = f"<a href='/view_pdf?name={name}&next={new_c}' style='display:block;background:#e74c3c;color:#fff;padding:15px;text-align:center;text-decoration:none;font-weight:bold;'>NEXT 10 PAGES →</a>" if new_c else ""
    return f'<body style="margin:0;background:#eee;"><div style="background:#fff;padding:10px;border-bottom:2px solid red;"><a href="/pdf_home">← BACK</a> | <b>{name.upper()}</b></div>{h}{next_btn}</body>'

# --- AI LOGIN & REGISTER SYSTEM ---
@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_login'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div style="background:#fff;margin:10px;padding:10px;border-radius:8px;"><img src="{i["url"]}" style="width:100%;"><br><a href="{i["url"]}" download style="color:green;font-weight:bold;text-decoration:none;">Download File</a></div>' for i in history])
    return f"""<body style="font-family:sans-serif;background:#f0f2f5;margin:0;"><div style="background:#9b59b6;color:#fff;padding:15px;text-align:center;"><h3>AI Enhancer</h3><a href="/" style="color:#fff;">← Home</a></div><div style="padding:15px;"><div style="background:#fff;padding:20px;border-radius:10px;text-align:center;"><form action="/enhance" method="POST" enctype="multipart/form-data"><input type="file" name="file"><br><br><button style="width:100%;padding:12px;background:#9b59b6;color:#fff;border:none;border-radius:5px;font-weight:bold;">ENHANCE PHOTO</button></form></div><h4>History:</h4>{h_html}<br><a href="/logout" style="color:red;">Logout</a></div></body>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('ai_login'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[{"effect": "grayscale"}, {"contrast": "auto"}, {"sharpen": 300}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

@app.route("/ai_login", methods=["GET", "POST"])
def ai_login():
    if request.method == "POST":
        u = users_col.find_one({"m": request.form.get("m")})
        if u and u['p'] == hash_pw(request.form.get("pw")):
            session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
    return f"""<body style="font-family:sans-serif;background:#eee;padding:50px;text-align:center;"><div style="background:#fff;padding:20px;border-radius:10px;"><h3>AI Login</h3><form method="POST"><input name="m" placeholder="Mobile"><br><input name="pw" type="password" placeholder="Pass"><br><br><button style="width:100%;background:#0078d7;color:#fff;padding:10px;border:none;border-radius:5px;">LOGIN</button></form><br><a href="/ai_register">Create New Account</a></div></body>"""

@app.route("/ai_register", methods=["GET", "POST"])
def ai_register():
    if request.method == "POST":
        m, p = request.form.get("m"), request.form.get("pw")
        if users_col.find_one({"m": m}): return "Number exists! <a href='/ai_register'>Back</a>"
        users_col.insert_one({"m": m, "p": hash_pw(p)})
        return "Done! <a href='/ai_login'>Login Now</a>"
    return f"""<body style="font-family:sans-serif;background:#eee;padding:50px;text-align:center;"><div style="background:#fff;padding:20px;border-radius:10px;"><h3>Create Account</h3><form method="POST"><input name="m" placeholder="Set Mobile"><br><input name="pw" type="password" placeholder="Set Pass"><br><br><button style="width:100%;background:#28a745;color:#fff;padding:10px;border:none;border-radius:5px;">REGISTER</button></form><br><a href="/ai_login">Already have account?</a></div></body>"""

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

# --- UPLOAD SYSTEM (ORIGINAL) ---
@app.route("/admin_upload")
def admin_upload(): return render_template_string('<body style="padding:20px;text-align:center;"><form action="/do_up" method="POST" enctype="multipart/form-data"><h3>Video Up</h3><input type="file" name="file"><br><input name="name" placeholder="Name"><br><input name="pw" placeholder="Pass"><br><button>UPLOAD</button></form></body>')

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("name", "video").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
    return redirect("/")

@app.route("/upload_pdf_page")
def upload_pdf_page(): return render_template_string('<body style="padding:20px;text-align:center;"><form action="/do_pdf_upload" method="POST" enctype="multipart/form-data"><h3>PDF Up</h3><input type="file" name="file"><br><input name="name" placeholder="Name"><br><input name="pw" placeholder="Pass"><br><button>UPLOAD PDF</button></form></body>')

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("name").replace(" ","_")
        if f:
            pdf_path = f"temp_{int(time.time())}.pdf"
            f.save(pdf_path)
            threading.Thread(target=process_pdf_background, args=(pdf_path, n)).start()
    return redirect("/pdf_home")

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string('<body style="padding:20px;text-align:center;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input name="new" placeholder="New Name">{% endif %}<br><input name="pw" placeholder="Pass"><button>OK</button></form></body>', t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
            elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        else:
            if t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/")
                cloudinary.api.delete_folder(f"pdf_data/{p}")
        return redirect("/")
    return "Wrong Pass"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
