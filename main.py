import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi, requests
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_hotstar_ultra_v32_home_fixed"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30 

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, ai_col, chat_col = db['users'], db['ai_history'], db['chat_history']
except: print("DB Connection Error")

ADMIN_PASSWORD = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    :root { --jio-blue: #0072ef; --bg: #0f1014; --card: #16181f; --border: #252833; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color:#fff; }
    .header { background: var(--bg); padding:15px; text-align:center; border-bottom: 1px solid var(--border); position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; }
    .logo { color: var(--jio-blue); font-weight: bold; font-size: 22px; text-decoration:none; }
    .card { background: var(--card); margin:12px; border-radius:12px; overflow:hidden; border: 1px solid var(--border); padding:15px; }
    .btn { display:inline-block; padding:12px 15px; border-radius:6px; text-decoration:none; font-size:14px; font-weight:600; color:#fff; border:none; cursor:pointer; text-align:center; transition: 0.3s; }
    .btn-jio { background: var(--jio-blue); width:100%; margin-bottom:10px; }
    .btn-outline { background:transparent; border:1px solid #fff; width:100%; }
    .chat-container { height: 400px; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 10px 15px; border-radius: 15px; max-width: 80%; }
    .user-msg { background: var(--jio-blue); align-self: flex-end; }
    .ai-msg { background: var(--border); align-self: flex-start; }
</style>"""

@app.route("/")
def index():
    # Central Home Page - Teeno features yahan se milenge
    return f'''{STYLE}
    <div class="header"><a href="/" class="logo">JioHub</a></div>
    <div style="padding:20px;">
        <div class="card" style="text-align:center;">
            <h3>Welcome, Atif</h3>
            <p>Select a service to continue</p>
            <a href="/video_home" class="btn btn-jio">JioTUBE (Videos)</a>
            <a href="/pdf_home" class="btn btn-jio">JioPDF (Books)</a>
            <a href="/ai_home" class="btn btn-jio" style="background:#8e44ad;">JioAI (Tools)</a>
        </div>
    </div>'''

@app.route("/video_home")
def video_home():
    q = request.args.get("q", "").strip().lower()
    try: res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20)
    except: res = {"resources": []}
    v_html = "".join([f'<div class="card"><b>{v["public_id"]}</b><br><br><a href="{v["secure_url"]}" class="btn btn-jio">WATCH NOW</a></div>' for v in res["resources"]])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-outline" style="width:auto;">← HOME</a><b class="logo">JioTube</b></div>{v_html}'

@app.route("/pdf_home")
def pdf_home():
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><b>{f["name"].split("__")[0].upper()}</b><br><br><div style="display:flex; gap:10px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-outline" style="border-color:#e50914; color:#e50914;">DEL</a></div></div>''' for f in folders])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-outline" style="width:auto;">← HOME</a><b class="logo">JioPDF</b><a href="/upload_pdf_page" class="btn btn-jio" style="width:auto; margin:0;">+</a></div>{f_list}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-outline" style="width:auto;">← HOME</a><b class="logo">JioAI</b></div><div class="card" style="text-align:center;"><a href="/ai_enhance" class="btn btn-jio">AI PHOTO ENHANCE</a><a href="/ai_chatter" class="btn btn-jio" style="background:#27ae60;">AI CHATTER</a><br><br><a href="/logout" style="color:#e50914;">Logout</a></div>'

# ... (PDF View, Upload, Enhance, Chatter, Auth routes exactly as before) ...

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        u_msg = request.form.get("msg")
        ai_resp = f"Atif bhai, aapka message mil gaya! Main 'Joya' AI hoon, kaise help karun?"
        chat_col.insert_one({"u": session['u'], "msg": u_msg, "resp": ai_resp, "t": time.time()})
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    chat_html = "".join([f'<div class="msg user-msg">{c["msg"]}</div><div class="msg ai-msg">{c["resp"]}</div>' for c in chats])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline" style="width:auto;">←</a><b>Joya Chatter</b></div><div class="chat-container" id="box">{chat_html}</div><div style="padding:10px;"><form method="POST" style="display:flex;gap:5px;"><input name="msg" style="flex:1; padding:10px; border-radius:5px;"><button class="btn btn-jio" style="width:auto; margin:0;">SEND</button></form></div>'

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p = request.form.get("m"), request.form.get("pw")
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<div class="card" style="margin-top:100px; text-align:center;"><h2>AI Login</h2><form method="POST"><input name="m" placeholder="User" required><br><input name="pw" type="password" placeholder="Pass" required><br><br><button class="btn btn-jio">LOGIN</button></form></div>'

# PDF View & Upload (Simplified stable versions)
@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=50)
    pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; margin-bottom:10px;">' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline" style="width:auto;">←</a><b>{name.split("__")[0]}</b></div>{h}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
