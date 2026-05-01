import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, threading, hashlib, certifi, requests
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_full_v33_all_features_restored"
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
    .card { background: var(--card); margin:12px; border-radius:12px; overflow:hidden; border: 1px solid var(--border); }
    .btn { display:inline-block; padding:10px 15px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600; color:#fff; border:none; cursor:pointer; }
    .btn-jio { background: var(--jio-blue); } .btn-ren { background:#ff9900; } .btn-danger { background:#e50914; } .btn-outline { background:transparent; border:1px solid #fff; }
    .search-box { background: var(--border); display:flex; margin:12px; border-radius:8px; overflow:hidden; border: 1px solid #333; }
    .search-box input { flex:1; border:none; padding:12px; outline:none; background:transparent; color:#fff; }
    .search-box button { background: var(--jio-blue); color:#fff; border:none; padding:0 20px; }
    .thumb { width:100%; height:180px; object-fit:cover; background:#000; }
    .action-bar { display:flex; gap:5px; padding:10px; flex-wrap:wrap; }
    .chat-bubble { padding:15px; border-radius:12px; margin:10px 0; line-height:1.5; }
    .user-q { background: var(--jio-blue); align-self: flex-end; margin-left: 20%; }
    .ai-a { background: var(--border); border: 1px solid var(--jio-blue); margin-right: 20%; }
</style>"""

# --- 1. JIO TUBE (VIDEO) ---
@app.route("/")
@app.route("/video_home")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:12px;"><b>{v["public_id"]}</b><div class="action-bar"><a href="{v["secure_url"]}" class="btn btn-jio" style="flex:1;">WATCH</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" class="btn btn-ren">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-danger">DEL</a></div></div></div>''' for v in videos])
    nb = f'<a href="/video_home?next={new_c}&q={q}" class="btn btn-outline" style="display:block; margin:15px; text-align:center;">LOAD NEXT</a>' if new_c else ""
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioTube</a><div><a href="/pdf_home" class="btn btn-outline">PDF</a> <a href="/ai_home" class="btn btn-jio">AI</a></div></div><form class="search-box"><input name="q" placeholder="Search videos..." value="{q}"><button>GO</button></form><div style="padding:0 12px;"><a href="/admin_upload" class="btn btn-jio">+ VIDEO</a></div>{v_html}{nb}'

# --- 2. JIO PDF ---
@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:15px;"><b>{f["name"].split("__")[0].upper()}</b><div class="action-bar"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:2;">OPEN</a><a href="/modify?task=rename&pid={f["name"]}&type=pdf" class="btn btn-ren">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-danger">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/video_home" class="btn btn-outline">TUBE</a><b class="logo">JioPDF</b><a href="/ai_home" class="btn btn-jio">AI</a></div><form class="search-box"><input name="q" placeholder="Search books..." value="{q}"><button>FIND</button></form><div style="padding:0 12px;"><a href="/upload_pdf_page" class="btn btn-jio">+ BOOK</a></div>{f_list}'

# --- 3. JIO AI (LOGIN / REGISTER / TOOLS) ---
@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-outline">HOME</a><b class="logo">JioAI</b><a href="/logout" class="btn btn-danger">OFF</a></div><div style="padding:20px; text-align:center;"><div class="card" style="padding:20px;"><a href="/ai_enhance" class="btn btn-jio" style="width:100%; margin-bottom:10px;">AI PHOTO ENHANCE</a><a href="/ai_chatter" class="btn btn-jio" style="width:100%; background:#27ae60;">AI CHATTER (JOYA)</a></div></div>'

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if not users_col.find_one({"m": m}): users_col.insert_one({"m": m, "p": hash_pw(p)})
            return '<h3>Registered! <a href="/ai_auth">Login Now</a></h3>'
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;"><h2>AI Login / Register</h2><form method="POST"><input name="m" placeholder="User/Mobile" style="width:100%;padding:10px;margin-bottom:10px;"><br><input name="pw" type="password" placeholder="Password" style="width:100%;padding:10px;"><br><br><button name="act" value="log" class="btn btn-jio" style="width:48%;">LOGIN</button> <button name="act" value="reg" class="btn btn-outline" style="width:48%; color:var(--jio-blue);">SIGN UP</button></form></div></body>'

# --- AI CHATTER (Question & Answer Logic) ---
@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        u_msg = request.form.get("msg")
        ai_resp = f"Atif bhai, Joya AI yahan hai! Aapka sawaal: '{u_msg}'... Iska jawab naye page par save ho gaya hai."
        chat_col.insert_one({"u": session['u'], "msg": u_msg, "resp": ai_resp, "t": time.time()})
    
    chats = list(chat_col.find({"u": session['u']}).sort("t", -1))
    h = "".join([f'<div class="chat-bubble user-q"><b>Me:</b> {c["msg"]}</div><div class="chat-bubble ai-a"><b>Joya:</b> {c["resp"]}</div><hr style="border:0; border-top:1px solid #333;">' for c in chats])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>AI Chatter</b></div><div style="padding:15px;"><form method="POST" style="display:flex;gap:10px;"><input name="msg" placeholder="Ask Joya..." style="flex:1;padding:12px;border-radius:8px;background:#1c1e26;color:#fff;border:1px solid #333;"><button class="btn btn-jio">ASK</button></form></div><div style="padding:15px; display:flex; flex-direction:column;">{h}</div>'

# --- (Other standard routes: Upload, View PDF, Modify kept as fixed before) ---
@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); next_c = request.args.get("next")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=next_c)
    pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"><div style="padding:10px;"><a href="{p["secure_url"]}" download class="btn btn-jio" style="width:100%;">DOWNLOAD PAGE</a></div></div>' for p in pages])
    nb = f'<a href="/view_pdf?name={name}&next={res.get("next_cursor")}" class="btn btn-outline" style="display:block;margin:15px;text-align:center;">NEXT PAGES</a>' if res.get("next_cursor") else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">← BACK</a><b>{name.split("__")[0]}</b></div>{h}{nb}'

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string("""<style>:root{--bg:#0f1014;--card:#16181f;--jio-blue:#0072ef}body{background:var(--bg);color:#fff;font-family:sans-serif}.card{background:var(--card);margin:50px auto;padding:30px;width:80%;border-radius:12px;text-align:center}</style><div class="card"><h3>Confirm {{t|upper}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=='rename' %}<input name="new" placeholder="New Name" required style="width:100%;padding:10px;margin-bottom:10px;"><br>{% endif %}<input name="pw" type="password" placeholder="PIN" required style="width:100%;padding:10px;"><br><br><button class="btn" style="background:#e50914;color:#fff;width:100%;padding:10px;border:none;border-radius:6px;">PROCEED</button></form></div>""", t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "delete": cloudinary.uploader.destroy(p, resource_type="video", invalidate=True)
            elif t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video", invalidate=True)
            return redirect("/")
        else: # PDF Folder Logic
            if t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type="image", invalidate=True)
                try: cloudinary.api.delete_resources([f"pdf_data/{p}/source"], resource_type="raw", invalidate=True)
                except: pass
                time.sleep(2); cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect(url_for('pdf_home'))
    return "Wrong PIN"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
