import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi, requests
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_hotstar_ultra_v31_chatter_final"
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

# --- UI STYLE (Including Chat Bubbles) ---
STYLE = """<style>
    :root { --jio-blue: #0072ef; --bg: #0f1014; --card: #16181f; --border: #252833; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color:#fff; }
    .header { background: var(--bg); padding:15px; text-align:center; border-bottom: 1px solid var(--border); position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; }
    .logo { color: var(--jio-blue); font-weight: bold; font-size: 22px; text-decoration:none; }
    .card { background: var(--card); margin:12px; border-radius:12px; overflow:hidden; border: 1px solid var(--border); }
    .btn { display:inline-block; padding:12px 15px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600; color:#fff; border:none; cursor:pointer; text-align:center; transition: 0.3s; }
    .btn-jio { background: var(--jio-blue); } .btn-outline { background:transparent; border:1px solid #fff; } .btn-danger { background:#e50914; }
    .chat-container { height: 400px; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
    .msg { padding: 10px 15px; border-radius: 15px; max-width: 80%; font-size: 14px; }
    .user-msg { background: var(--jio-blue); align-self: flex-end; border-bottom-right-radius: 2px; }
    .ai-msg { background: var(--border); align-self: flex-start; border-bottom-left-radius: 2px; }
    input[type="text"], input[type="password"] { width:80%; padding:12px; border-radius:6px; border:1px solid var(--border); background:#1c1e26; color:#fff; }
</style>"""

@app.route("/")
def index():
    # ... (Same Video Index Logic) ...
    return redirect(url_for('pdf_home')) # Defaulting to PDF for now or your preferred home

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:15px;"><b>{f["name"].split("__")[0].upper()}</b><div class="action-bar"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:2;">OPEN</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" class="btn btn-ren">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-danger">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioPDF</a><div><a href="/ai_home" class="btn btn-jio">AI TOOLS</a></div></div>{f_list}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">← BACK</a><b style="color:var(--jio-blue);">AI DASHBOARD</b></div><div style="padding:10px;"><a href="/ai_enhance" class="btn btn-jio" style="width:45%;">AI ENHANCE</a> <a href="/ai_chatter" class="btn btn-outline" style="width:45%; border-color:var(--jio-blue); color:var(--jio-blue);">AI CHATTER</a></div>'

@app.route("/ai_enhance")
def ai_enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div style="padding:10px;"><a href="{i["url"]}" download class="btn btn-jio">SAVE</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>Enhance</b></div><div class="card" style="padding:20px;text-align:center;"><form action="/enhance_action" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><button class="btn btn-jio" style="width:90%;margin-top:10px;">UPLOAD & FIX</button></form></div>{h_html}'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        u_msg = request.form.get("msg")
        # Simulating AI Response (You can connect Gemini/OpenAI API here)
        ai_resp = f"Atif bhai, aapne pucha: '{u_msg}'. Main abhi seekh rahi hoon, par aapka kaam ho jayega!"
        chat_col.insert_one({"u": session['u'], "msg": u_msg, "resp": ai_resp, "t": time.time()})
    
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    chat_html = "".join([f'<div class="msg user-msg">{c["msg"]}</div><div class="msg ai-msg">{c["resp"]}</div>' for c in chats])
    
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>AI Chatter</b></div>
    <div class="chat-container" id="box">{chat_html}</div>
    <div style="position:fixed; bottom:0; width:100%; background:var(--card); padding:10px; border-top:1px solid var(--border);">
        <form method="POST" style="display:flex; gap:10px;">
            <input name="msg" placeholder="Type something..." required>
            <button class="btn btn-jio">SEND</button>
        </form>
    </div>
    <script>document.getElementById("box").scrollTop = document.getElementById("box").scrollHeight;</script>'''

@app.route("/enhance_action", methods=["POST"])
def enhance_action():
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[{"width": 1800, "crop": "limit"}, {"effect": "improve"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_enhance'))

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p = request.form.get("m"), request.form.get("pw")
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;"><h2>JioAI Login</h2><form method="POST"><input name="m" placeholder="Username" required><br><input name="pw" type="password" placeholder="Password" required><br><br><button class="btn btn-jio" style="width:100%;">LOGIN</button></form></div></body>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
