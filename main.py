import os, hashlib, certifi, time
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api

app = Flask(__name__)
app.secret_key = "atif_mega_all_in_one"

# Configuration
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col = db['users']
    history_col = db['ai_history']
except: print("DB Connection Error")

ADMIN_PASSWORD = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# --- HOME PAGE ---
@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    
    v_list = "".join([f"""
    <div style="background:#fff;border-bottom:2px solid #ddd;padding:10px;margin-bottom:10px;">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;border-radius:5px;background:#000;">
        <b style="display:block;padding:5px;">{v["public_id"]}</b>
        <div style="display:flex;gap:5px;margin-top:5px;">
            <a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:10px;text-decoration:none;border-radius:4px;font-size:12px;">PLAY</a>
            <a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:10px;text-decoration:none;border-radius:4px;font-size:12px;">RENAME</a>
            <a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:10px;text-decoration:none;border-radius:4px;font-size:12px;">DELETE</a>
        </div>
    </div>""" for v in videos])
    
    nb = f"<a href='/?next={new_c}&q={q}' style='display:block;background:#333;color:#fff;text-align:center;padding:15px;margin:10px;text-decoration:none;border-radius:5px;'>NEXT VIDEOS →</a>" if new_c else ""
    
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;">
    <div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;">
        <h3 style="margin:0;">JioTube Pro</h3>
        <div style="display:flex;gap:5px;margin-top:8px;">
            <a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">+ UPLOAD</a>
            <a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">PDF VIEWER</a>
            <a href="/ai_login" style="flex:1;background:#9b59b6;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;">AI ENHANCE</a>
        </div>
        <form style="margin-top:8px;display:flex;"><input name="q" value="{q}" style="flex:1;padding:8px;border:none;"><button style="padding:8px;">GO</button></form>
    </div>{v_list}{nb}</body>"""

# --- AI ENHANCER ---
@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = users_col.find_one({"mobile": request.form.get("mobile")})
        if u and u['password'] == hash_pw(request.form.get("pw")):
            session['user_id'] = str(u['_id']); return redirect(url_for('ai_home'))
        return "Wrong! <a href='/ai_login'>Retry</a>"
    return render_template_string('<body style="padding:20px;text-align:center;font-family:sans-serif;"><h3>AI Login</h3><form method="POST"><input name="mobile" placeholder="Mobile" style="width:80%;padding:10px;"><br><br><input name="pw" type="password" placeholder="Pass" style="width:80%;padding:10px;"><br><br><button style="width:80%;padding:10px;background:#9b59b6;color:#fff;border:none;">LOGIN</button></form><p>New? <a href="/ai_register">Register</a></p></body>')

@app.route("/ai_register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        m = request.form.get("mobile"); p = request.form.get("pw")
        if users_col.find_one({"mobile": m}): return "Number exists!"
        users_col.insert_one({"mobile": m, "password": hash_pw(p)})
        return 'Done! <a href="/ai_login">Login</a>'
    return '<body><form method="POST"><h3>Register</h3><input name="mobile" placeholder="Mobile"><br><input name="pw" type="password" placeholder="Pass"><br><button>Create Account</button></form></body>'

@app.route("/ai_home")
def ai_home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return f"""<body style="padding:20px;text-align:center;font-family:sans-serif;">
    <h3>AI Machine</h3>
    <form action="/enhance" method="POST" enctype="multipart/form-data" style="padding:20px;border:1px solid #ccc;">
        <input type="file" name="file"><br><br>
        <button style="background:#9b59b6;color:#fff;padding:15px;width:100%;border:none;">CLEAN & ENHANCE</button>
    </form>
    <br><a href="/">HOME</a> | <a href="/logout">LOGOUT</a></body>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'user_id' not in session: return redirect(url_for('login'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[{"effect": "grayscale"},{"effect": "improve:outdoor"},{"contrast": "auto"},{"sharpen": 100}])
        return f'<h3>Done!</h3><img src="{up["secure_url"]}" style="width:100%"><br><a href="{up["secure_url"]}" download style="display:block;background:green;color:#fff;padding:15px;text-decoration:none;margin-top:10px;">DOWNLOAD PHOTO</a><br><a href="/ai_home">Back</a>'
    return "No file selected."

# --- ADMIN & UTILS ---
@app.route("/admin_upload")
def admin_upload(): return '<body><form action="/do_up" method="POST" enctype="multipart/form-data">File: <input type="file" name="file"><br>Name: <input name="name"><br>Pass: <input name="pw"><button>UP</button></form></body>'

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("name", "vid").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=n)
        return redirect("/")
    return "Pass Error"

@app.route("/modify")
def modify():
    return render_template_string('<body style="padding:20px;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input name="new" placeholder="New Name">{% endif %}<br><br><input name="pw" placeholder="Admin Pass"><button>GO</button></form></body>', t=request.args.get("task"), p=request.args.get("pid"), tp=request.args.get("type"))

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
        elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        return redirect("/")
    return "Error"

@app.route("/pdf_home")
def pdf_home():
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'<li><a href="/view_pdf?name={f["name"]}">{f["name"]}</a></li>' for f in folders])
    return f"<body><h3>PDF List</h3><ul>{f_list}</ul><a href='/'>Back Home</a></body>"

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
