import os, time, hashlib, certifi, requests, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_ultimate_v45_fix"

# --- API & DB Setup ---
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, chat_col, ai_col = db['users'], db['chat_history'], db['ai_history']
except: print("Database Error")

ADMIN_PIN = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    :root { --jio: #0072ef; --bg: #f4f7f6; }
    body { margin:0; font-family: sans-serif; background: var(--bg); }
    .header { background: var(--jio); padding:12px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:8px; border: 1px solid #ddd; overflow:hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .btn { padding:8px 12px; border-radius:5px; text-decoration:none; color:#fff; font-size:12px; cursor:pointer; border:none; font-weight:bold; display:inline-block; }
    .btn-jio { background: var(--jio); } .btn-del { background: #e50914; } .btn-edit { background: #ff9800; } .btn-down { background: #28a745; }
    .thumb { width:100%; height:160px; object-fit: cover; background:#000; }
    .search-bar { display:flex; margin:10px; gap:5px; }
    .search-bar input { flex:1; padding:10px; border-radius:5px; border:1px solid #ccc; }
    .chat-container { padding:15px; display:flex; flex-direction:column; gap:12px; background:#fff; min-height:70vh; }
    .m-u { align-self:flex-end; background:#e1f5fe; padding:12px; border-radius:12px 12px 0 12px; max-width:85%; font-size:14px; border:1px solid #b3e5fc; }
    .m-ai { align-self:flex-start; background:#f1f1f1; padding:12px; border-radius:12px 12px 12px 0; max-width:85%; font-size:14px; border:1px solid #e0e0e0; }
</style>"""

@app.route("/")
@app.route("/video_home")
def index():
    q = request.args.get("q", "").lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20)
        vids = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
    except: vids = []
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:10px;"><b>{v["public_id"]}</b><div style="margin-top:10px; display:flex; gap:5px;"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}&tp=video" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}&tp=video" class="btn btn-del">DELETE</a></div></div></div>''' for v in vids])
    return f'{STYLE}<div class="header"><b>JioTube</b><div><a href="/pdf_home" class="btn" style="border:1px solid #fff">PDF</a> <a href="/ai_home" class="btn" style="border:1px solid #fff">AI</a></div></div><form class="search-bar"><input name="q" placeholder="Search Videos..." value="{q}"><button class="btn btn-jio">SEARCH</button></form>{v_html}<div style="padding:15px; text-align:center;"><button class="btn btn-jio" style="width:100%;">NEXT VIDEOS</button></div>'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").lower()
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><div style="margin-top:10px; display:flex; gap:5px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:1; text-align:center;">OPEN</a><a href="/modify?t=rename&p={f["name"]}&tp=pdf" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={f["name"]}&tp=pdf" class="btn btn-del">DELETE</a></div></div>' for f in folds if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioPDF</b></div><form class="search-bar"><input name="q" placeholder="Search Books..." value="{q}"><button class="btn btn-jio">FIND</button></form>{f_html}<div style="padding:15px; text-align:center;"><button class="btn btn-jio" style="width:100%;">NEXT BOOKS</button></div>'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioAI</b><a href="/logout" class="btn btn-del">OUT</a></div><div style="padding:20px;"><a href="/ai_chatter" class="btn btn-jio" style="display:block; text-align:center; background:#28a745; padding:15px; margin-bottom:15px;">AI JOYA (CHAT)</a><a href="/ai_enhance" class="btn btn-jio" style="display:block; text-align:center; padding:15px;">PHOTO ENHANCER</a></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        try:
            # Background processing and redirecting to answer page
            resp = model.generate_content(f"Hindi mein jawab do: {msg}")
            ai_text = resp.text
        except: ai_text = "Server Busy. Try again."
        chat_col.insert_one({"u": session['u'], "msg": msg, "resp": ai_text, "t": time.time()})
        return redirect(url_for('ai_chatter'))

    history = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="m-u">{c["msg"]}</div><div class="m-ai"><b>Joya:</b> {c["resp"]}</div>' for c in history])
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn">←</a><b>Joya AI</b></div><div class="chat-container" id="cb">{c_html}</div><div style="height:80px;"></div><form method="POST" style="position:fixed; bottom:0; width:100%; background:#eee; padding:10px; display:flex; gap:5px; box-sizing:border-box;"><input name="msg" style="flex:1; padding:12px; border-radius:5px; border:1px solid #ccc;" placeholder="Sawaal likhein..." required><button class="btn btn-jio">SEND</button></form><script>var b=document.getElementById("cb"); window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/ai_enhance")
def ai_enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(5))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" class="thumb"><div style="padding:10px; text-align:center;"><a href="{i["url"]}" download class="btn btn-down">DOWNLOAD PHOTO</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn">←</a><b>Enhancer</b></div><div class="card" style="padding:20px; text-align:center;"><form action="/do_enhance" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><button class="btn btn-jio" style="width:100%;">UPLOAD & FIX</button></form></div>{h_html}'

@app.route("/do_enhance", methods=["POST"])
def do_enhance():
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_fixed", transformation=[{"effect": "improve"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_enhance'))

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if users_col.find_one({"m": m}): return "User exists!"
            users_col.insert_one({"m": m, "p": hash_pw(p)})
            return 'Registered! <a href="/ai_auth">Login</a>'
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<div style="padding:50px; text-align:center;"><div class="card" style="padding:20px;"><h3>Jio Login</h3><form method="POST"><input name="m" placeholder="User" required style="width:100%; padding:10px; margin-bottom:10px;"><br><input name="pw" type="password" placeholder="Pass" required style="width:100%; padding:10px;"><br><br><button name="act" value="log" class="btn btn-jio" style="width:100%;">LOGIN</button><br><br><button name="act" value="reg" style="background:none; border:none; color:var(--jio); cursor:pointer;">New? Signup</button></form></div></div>'

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("t"), request.args.get("p"), request.args.get("tp")
    return render_template_string(f'''{STYLE}<div style="padding:50px; text-align:center;"><div class="card" style="padding:20px;"><h3>{t.upper()} {tp.upper()}</h3><p>{p}</p><form action="/confirm" method="POST"><input type="hidden" name="t" value="{t}"><input type="hidden" name="p" value="{p}"><input type="hidden" name="tp" value="{tp}"><input name="pin" placeholder="Admin PIN" type="password" required style="width:100%; padding:10px;"><br><br><button class="btn btn-del" style="width:100%;">CONFIRM</button></form></div></div>''')

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pin") != ADMIN_PIN: return "Wrong PIN"
    t, p, tp = request.form.get("t"), request.form.get("p"), request.form.get("tp")
    if t == "delete":
        if tp == "video": cloudinary.uploader.destroy(p, resource_type="video")
        else: cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/"); cloudinary.api.delete_folder(f"pdf_data/{p}")
    return redirect("/")

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=50)
    pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%;"> ' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>BOOK</b></div>{h}'

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
