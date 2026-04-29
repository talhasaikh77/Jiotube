import os, hashlib, certifi, time
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "atif_fix_v4"
app.permanent_session_lifetime = timedelta(days=30)

# Database Config (Fixed SSL & Connection)
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col = db['users']
    ai_col = db['ai_history']
except: print("DB Connection Error")

ADMIN_PW = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# --- HOME / JIOTUBE ---
@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    
    v_list = "".join([f'<div style="border-bottom:1px solid #ccc;padding:10px;"><b>{v["public_id"]}</b><br><a href="{v["secure_url"]}">PLAY</a> | <a href="/modify?task=rename&pid={v["public_id"]}">RENAME</a> | <a href="/modify?task=delete&pid={v["public_id"]}">DEL</a></div>' for v in videos])
    
    return f"""<body style="font-family:sans-serif;padding:10px;">
    <h3>JioTube Pro</h3>
    <a href="/admin_upload">[+Upload]</a> | <a href="/pdf_home">[PDF Library]</a> | <a href="/ai_home">[AI Enhance]</a>
    <form style="margin:10px 0;"><input name="q" value="{q}"><button>Search</button></form>
    {v_list}
    {"<br><a href='/?next="+new_c+"&q="+q+"'>Next Videos >></a>" if new_c else ""}
    </body>"""

# --- PDF VIEWER (FIXED) ---
@app.route("/pdf_home")
def pdf_home():
    # PDF Folder check (Cloudinary folder: pdf_data)
    try:
        res = cloudinary.api.resources(resource_type="image", prefix="pdf_data/", type="upload")
        pdfs = res.get("resources", [])
    except: pdfs = []
    
    p_list = "".join([f'<li><a href="{p["secure_url"]}">{p["public_id"].replace("pdf_data/","")}</a></li>' for p in pdfs])
    return f"<h3>PDF List</h3><ul>{p_list}</ul><a href='/'>Back Home</a>"

# --- AI ENHANCE & HISTORY ---
@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('login'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div><img src="{i["url"]}" width="100%"><br><a href="{i["url"]}" download>Download</a><hr></div>' for i in history])
    
    return f"""<h3>AI Enhancer</h3>
    <form action="/enhance" method="POST" enctype="multipart/form-data">
        <input type="file" name="file"><button>Enhance</button>
    </form>
    <h4>Recent History</h4>{h_html}
    <br><a href="/">Back</a> | <a href="/logout">Logout</a>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('login'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[
            {"effect": "grayscale"}, {"contrast": "auto"}, {"sharpen": 200}, {"crop": "trim", "gravity": "auto"}
        ])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

# --- LOGIN / ADMIN / MISC ---
@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = users_col.find_one({"m": request.form.get("m")})
        if u and u['p'] == hash_pw(request.form.get("pw")):
            session.permanent = True; session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
    return '<form method="POST">Mobile: <input name="m"><br>Pass: <input name="pw" type="password"><br><button>Login</button></form>'

@app.route("/admin_upload")
def admin_upload():
    return '<form action="/do_up" method="POST" enctype="multipart/form-data">File: <input type="file" name="file"><br>Name: <input name="name"><br>Admin Pass: <input name="pw"><button>Upload</button></form>'

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PW:
        f = request.files.get("file"); n = request.form.get("name", "file").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="auto", public_id=n)
    return redirect("/")

@app.route("/modify")
def modify():
    return render_template_string('<form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}">{% if t=="rename" %}<input name="new" placeholder="New Name">{% endif %}<br>Admin Pass: <input name="pw"><button>Confirm</button></form>', t=request.args.get("task"), p=request.args.get("pid"))

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PW:
        t, p = request.form.get("task"), request.form.get("pid")
        if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
        elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
    return redirect("/")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
