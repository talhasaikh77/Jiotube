import os, time, hashlib, certifi, requests, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v55_final"

# --- Gemini API (Fast Version) ---
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Database & Cloudinary ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, chat_col = db['users'], db['chat_history']
except: print("DB Error")

ADMIN_PIN = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    :root { --jio: #0072ef; --bg: #f0f2f5; }
    body { margin:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .card { background: #fff; margin:12px; border-radius:12px; border: 1px solid #ddd; overflow:hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 12px; }
    .btn { padding:10px; border-radius:8px; text-decoration:none; color:#fff; font-size:12px; font-weight:bold; text-align:center; border:none; cursor:pointer; }
    .btn-jio { background: var(--jio); } .btn-del { background: #dc3545; } .btn-edit { background: #fd7e14; } .btn-down { background: #28a745; }
    .thumb { width:100%; height:190px; object-fit: cover; background:#000; }
    .search-container { padding: 10px; display: flex; gap: 5px; }
    .search-container input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #ccc; }
    .chat-container { padding:15px; display:flex; flex-direction:column; gap:12px; padding-bottom:100px; }
    .m-u { align-self:flex-end; background:#dcf8c6; padding:12px; border-radius:15px 15px 0 15px; max-width:85%; font-size:14px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    .m-ai { align-self:flex-start; background:#fff; padding:12px; border-radius:15px 15px 15px 0; max-width:85%; font-size:14px; border:1px solid #ddd; }
</style>"""

@app.route("/")
def index():
    q = request.args.get("q", "").lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20)
        vids = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
    except: vids = []
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:10px 12px 0;"><b>{v["public_id"]}</b></div><div class="btn-grid"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}&tp=video" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}&tp=video" class="btn btn-del">DELETE</a><a href="{v["secure_url"]}" download class="btn btn-down">DOWNLOAD</a></div></div>''' for v in vids])
    return f'{STYLE}<div class="header"><b>JioTube</b><div><a href="/pdf_home" class="btn btn-jio" style="border:1px solid #fff">PDF</a> <a href="/ai_home" class="btn btn-jio" style="border:1px solid #fff">AI</a></div></div><form class="search-container"><input name="q" placeholder="Search Videos..." value="{q}"><button class="btn btn-jio">GO</button></form>{v_html}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").lower()
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:10px;"><b>{f["name"].upper()}</b><div class="btn-grid"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a><a href="#" class="btn btn-edit">JPG FIX</a><a href="/modify?t=delete&p={f["name"]}&tp=pdf" class="btn btn-del">DELETE</a><a href="#" class="btn btn-down">INSTALL</a></div></div>' for f in folds if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioPDF</b></div><form class="search-container"><input name="q" placeholder="Search Books..." value="{q}"><button class="btn btn-jio">FIND</button></form>{f_html}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioAI</b><a href="/logout" class="btn btn-del">OUT</a></div><div style="padding:20px; display:flex; flex-direction:column; gap:15px;"><a href="/ai_chatter" class="btn btn-jio" style="padding:25px; background:#28a745; font-size:16px;">TALK TO JOYA</a></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        try:
            r = model.generate_content(f"Hindi/Urdu short reply: {msg}")
            txt = r.text
        except: txt = "Joya is resting. Try again in a bit."
        chat_col.insert_one({"u": session['u'], "msg": msg, "resp": txt, "t": time.time()})
        return redirect(url_for('ai_chatter'))
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="m-u">{c["msg"]}</div><div class="m-ai"><b>Joya:</b> {c["resp"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn">←</a><b>Joya</b><a href="/clear_chat" class="btn btn-del" style="font-size:10px;">CLEAR</a></div><div class="chat-container" id="cb">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; background:#fff; padding:10px; display:flex; gap:5px; border-top:1px solid #ddd; box-sizing:border-box;"><input name="msg" style="flex:1; padding:12px; border-radius:8px; border:1px solid #ccc;" placeholder="Write message..." required><button class="btn btn-jio">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m = request.form.get("m")
        session['u'] = m
        return redirect(url_for('ai_home'))
    return f'{STYLE}<div style="padding:50px; text-align:center;"><div class="card" style="padding:25px;"><h2>Jio Login</h2><form method="POST"><input name="m" placeholder="Your Name" required style="width:100%; padding:12px; margin-bottom:15px; border-radius:8px; border:1px solid #ccc;"><button class="btn btn-jio" style="width:100%; padding:12px;">START CHAT</button></form></div></div>'

@app.route("/clear_chat")
def clear_chat():
    if 'u' in session: chat_col.delete_many({"u": session['u']})
    return redirect(url_for('ai_chatter'))

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("t"), request.args.get("p"), request.args.get("tp")
    return render_template_string(f'''{STYLE}<div style="padding:50px; text-align:center;"><div class="card" style="padding:20px;"><h3>Confirm {t.upper()}</h3><p>{p}</p><form action="/confirm" method="POST"><input type="hidden" name="t" value="{t}"><input type="hidden" name="p" value="{p}"><input type="hidden" name="tp" value="{tp}"><input name="pin" placeholder="PIN" type="password" required style="width:100%; padding:10px; margin-bottom:10px;"><button class="btn btn-del" style="width:100%;">CONFIRM ACTION</button></form></div></div>''')

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pin") != ADMIN_PIN: return "Wrong PIN"
    t, p, tp = request.form.get("t"), request.form.get("p"), request.form.get("tp")
    if t == "delete":
        if tp == "video": cloudinary.uploader.destroy(p, resource_type="video")
        else: cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/"); cloudinary.api.delete_folder(f"pdf_data/{p}")
    return redirect("/")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
