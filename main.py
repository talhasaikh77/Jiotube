import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi, requests
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_final_v34_stable_fix"
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
    :root { --jio-blue: #0072ef; --bg: #0f1014; --card: #1c1e26; --border: #2d303d; }
    body { margin:0; font-family: 'Segoe UI', sans-serif; background: var(--bg); color:#fff; }
    .header { background: rgba(15,16,20,0.9); padding:15px; text-align:center; border-bottom: 1px solid var(--border); position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; backdrop-filter: blur(10px); }
    .logo { color: var(--jio-blue); font-weight: bold; font-size: 24px; text-decoration:none; letter-spacing:1px; }
    .card { background: var(--card); margin:15px; border-radius:15px; overflow:hidden; border: 1px solid var(--border); box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .btn { display:inline-block; padding:12px 20px; border-radius:8px; text-decoration:none; font-size:13px; font-weight:600; color:#fff; border:none; cursor:pointer; text-align:center; transition: 0.3s; }
    .btn-jio { background: linear-gradient(45deg, #0072ef, #00c6ff); box-shadow: 0 4px 10px rgba(0,114,239,0.3); }
    .btn-outline { background:transparent; border:1.5px solid var(--border); }
    .btn-danger { background: #ff4b5c; }
    .input-box { width:90%; padding:14px; margin:10px 0; border-radius:10px; border:1px solid var(--border); background:#12141a; color:#fff; font-size:15px; }
    
    /* Chatter Look */
    .chat-box { height:60vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:12px; background: #12141a; }
    .msg-u { align-self:flex-end; background:var(--jio-blue); padding:12px 18px; border-radius:18px 18px 0 18px; max-width:75%; font-size:14px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .msg-ai { align-self:flex-start; background:var(--border); padding:12px 18px; border-radius:18px 18px 18px 0; max-width:75%; font-size:14px; line-height:1.5; color:#e0e0e0; }
</style>"""

@app.route("/")
def index():
    return redirect(url_for('pdf_home'))

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:20px;"><b>{f["name"].split("__")[0].upper()}</b><div style="margin-top:15px; display:flex; gap:10px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:1;">OPEN BOOK</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-outline" style="color:#ff4b5c;">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioHub</a><a href="/ai_home" class="btn btn-jio">AI TOOLS</a></div><div style="padding:10px;"><input type="text" class="input-box" placeholder="Search books..." style="width:94%; margin:10px auto; display:block;"></div>{f_list}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">← BACK</a><b class="logo">JioAI</b><a href="/logout" class="btn btn-danger" style="padding:8px 12px;">OUT</a></div><div style="padding:25px; text-align:center;"><div class="card" style="padding:30px; background:linear-gradient(180deg, #1c1e26 0%, #12141a 100%);"><h3>AI Smart Dashboard</h3><p style="color:#888; font-size:14px;">Powered by Joya AI</p><br><a href="/ai_enhance" class="btn btn-jio" style="width:100%; margin-bottom:15px; padding:15px;">PHOTO ENHANCER</a><a href="/ai_chatter" class="btn btn-outline" style="width:100%; border-color:var(--jio-blue); color:var(--jio-blue); padding:15px;">AI CHATTER (JOYA)</a></div></div>'

@app.route("/ai_enhance")
def ai_enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(5))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div style="padding:10px;text-align:center;"><a href="{i["url"]}" download class="btn btn-jio">SAVE TO GALLERY</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>AI Enhancer</b></div><div class="card" style="padding:20px;text-align:center; border:2px dashed var(--border);"><form action="/do_enhance" method="POST" enctype="multipart/form-data"><p>Select photo to fix quality</p><input type="file" name="file" required style="margin-bottom:15px;"><br><button class="btn btn-jio" style="width:100%;">ENHANCE HD</button></form></div>{h_html}'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        resp = f"Hello Atif bhai! Main Joya hoon. Aapne pucha: '{msg}'. Main abhi process kar rahi hoon, jaldi hi seekh jaungi!"
        chat_col.insert_one({"u": session['u'], "msg": msg, "resp": resp, "t": time.time()})
        return redirect(url_for('ai_chatter')) # Refresh to show new msg

    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="msg-u">{c["msg"]}</div><div class="msg-ai"><b>Joya:</b><br>{c["resp"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>Joya Chatter</b></div>
    <div class="chat-box" id="cb">{c_html}</div>
    <div style="padding:15px; background:var(--card); border-top:1px solid var(--border); position:fixed; bottom:0; width:100%; box-sizing:border-box;">
        <form method="POST" style="display:flex; gap:10px;">
            <input name="msg" class="input-box" placeholder="Ask Joya anything..." required style="margin:0; flex:1;">
            <button class="btn btn-jio">SEND</button>
        </form>
    </div>
    <script>var b=document.getElementById("cb"); b.scrollTop=b.scrollHeight;</script>'''

@app.route("/do_enhance", methods=["POST"])
def do_enhance():
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_fixed", transformation=[{"effect": "improve", "quality": "auto"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_enhance'))

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if not users_col.find_one({"m": m}): users_col.insert_one({"m": m, "p": hash_pw(p)})
            return '<h3>Success! <a href="/ai_auth">Login Now</a></h3>'
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:35px;text-align:center;"><h2>JioAI</h2><form method="POST"><input name="m" class="input-box" placeholder="Username" required><br><input name="pw" type="password" class="input-box" placeholder="Password" required><br><br><button name="act" value="log" class="btn btn-jio" style="width:48%;">LOGIN</button> <button name="act" value="reg" class="btn btn-outline" style="width:48%;">SIGN UP</button></form></div></body>'

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=50)
    pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; border-bottom:2px solid var(--bg);">' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">←</a><b>{name.split("__")[0]}</b></div>{h}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
