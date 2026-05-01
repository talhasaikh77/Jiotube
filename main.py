import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, hashlib, certifi, requests
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jio_full_final_v42"

# --- API & DB Setup ---
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, ai_col, chat_col = db['users'], db['ai_history'], db['chat_history']
except: print("DB Connection Error")

ADMIN_PASSWORD = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# --- CSS Style (Clean White Theme) ---
STYLE = """<style>
    :root { --jio: #0072ef; --bg: #f4f7f6; --card: #ffffff; --border: #ddd; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color: #333; }
    .header { background: var(--jio); padding:12px; text-align:center; position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; color:#fff; }
    .logo { color: #fff; font-weight: bold; font-size: 18px; text-decoration:none; }
    .card { background: var(--card); margin:10px; border-radius:10px; overflow:hidden; border: 1px solid var(--border); box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .btn { display:inline-block; padding:10px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:600; color:#fff; border:none; cursor:pointer; }
    .btn-jio { background: var(--jio); }
    .btn-danger { background: #e50914; }
    .btn-outline { background:transparent; border:1px solid #fff; color:#fff; }
    .thumb-img { width:100%; height:170px; object-fit: cover; background:#000; }
    .search-box { background: #fff; display:flex; margin:10px; border-radius:8px; border: 1px solid var(--border); overflow:hidden; }
    .search-box input { flex:1; border:none; padding:10px; outline:none; }
    .search-box button { background: var(--jio); color:#fff; border:none; padding:0 15px; }
    .chat-box { height:55vh; overflow-y:auto; padding:10px; display:flex; flex-direction:column; gap:10px; background:#fff; }
    .m-u { align-self:flex-end; background:#e1f5fe; padding:10px; border-radius:12px 12px 0 12px; max-width:80%; font-size:13px; border:1px solid #b3e5fc; }
    .m-ai { align-self:flex-start; background:#f5f5f5; padding:10px; border-radius:12px 12px 12px 0; max-width:80%; font-size:13px; border:1px solid #e0e0e0; }
</style>"""

# --- All App Routes ---

@app.route("/")
@app.route("/video_home")
def index():
    q = request.args.get("q", "").strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
    except: videos = []
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb-img"><div style="padding:10px;"><b>{v["public_id"]}</b><div style="margin-top:10px; display:flex; gap:5px;"><a href="{v["secure_url"]}" class="btn btn-jio" style="flex:1;">WATCH</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn btn-danger">DEL</a></div></div></div>''' for v in videos])
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioTube</a><div><a href="/pdf_home" class="btn btn-outline">PDF</a> <a href="/ai_home" class="btn btn-outline">AI</a></div></div><form class="search-box"><input name="q" placeholder="Search videos..." value="{q}"><button>GO</button></form><div style="padding:0 10px;"><a href="/admin_upload" class="btn btn-jio" style="width:100%; text-align:center;">+ UPLOAD VIDEO</a></div>{v_html}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:15px;"><b>{f["name"].upper()}</b><div style="margin-top:10px; display:flex; gap:5px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:1; text-align:center;">OPEN</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn btn-danger">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/video_home" class="btn btn-outline">TUBE</a><b class="logo">JioPDF</b><a href="/ai_home" class="btn btn-outline">AI</a></div><form class="search-box"><input name="q" placeholder="Search books..." value="{q}"><button>FIND</button></form>{f_list}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-outline">HOME</a><b class="logo">JioAI</b><a href="/logout" class="btn btn-danger">OUT</a></div><div style="padding:20px; text-align:center;"><a href="/ai_enhance" class="btn btn-jio" style="width:100%; margin-bottom:12px; padding:15px;">PHOTO ENHANCER</a><a href="/ai_chatter" class="btn btn-jio" style="width:100%; background:#28a745; padding:15px;">AI CHATTER (JOYA)</a></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        try:
            response = model.generate_content(f"Reply briefly in Hindi/Urdu like a helpful AI named Joya: {msg}")
            ai_resp = response.text
        except: ai_resp = "API Error. Check Gemini Key."
        chat_col.insert_one({"u": session['u'], "msg": msg, "resp": ai_resp, "t": time.time()})
        return redirect(url_for('ai_chatter'))
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="m-u">{c["msg"]}</div><div class="m-ai"><b>Joya:</b> {c["resp"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>AI Chatter</b></div><div class="chat-box" id="cb">{c_html}</div><div style="padding:10px; background:#f4f4f4;"><form method="POST" style="display:flex; gap:5px;"><input name="msg" style="flex:1; padding:10px; border-radius:5px; border:1px solid #ccc;" placeholder="Ask Joya..." required><button class="btn btn-jio">SEND</button></form></div><script>var b=document.getElementById("cb"); b.scrollTop=b.scrollHeight;</script>'''

@app.route("/ai_enhance")
def ai_enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(5))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" class="thumb-img"><div style="padding:10px;text-align:center;"><a href="{i["url"]}" download class="btn btn-jio">DOWNLOAD</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>Enhancer</b></div><div class="card" style="padding:20px;text-align:center;"><form action="/do_enhance" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><button class="btn btn-jio" style="width:100%;">FIX PHOTO</button></form></div>{h_html}'

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
            if not users_col.find_one({"m": m}): users_col.insert_one({"m": m, "p": hash_pw(p)})
            return 'Registered! <a href="/ai_auth">Login</a>'
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<div style="padding:50px; text-align:center;"><div class="card" style="padding:20px;"><h2>Login</h2><form method="POST"><input name="m" placeholder="User" required style="width:100%; padding:10px; margin-bottom:10px;"><br><input name="pw" type="password" placeholder="Pass" required style="width:100%; padding:10px;"><br><br><button name="act" value="log" class="btn btn-jio" style="width:100%;">LOGIN</button></form></div></div>'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=50)
    pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%;"> ' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">←</a><b>BOOK</b></div>{h}'

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string("""<div style="background:#f4f7f6;height:100vh;display:flex;align-items:center;justify-content:center;font-family:sans-serif;"><div style="background:#fff;padding:30px;width:80%;border-radius:12px;text-align:center;border:1px solid #ddd"><h3>Confirm {{t|upper}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}"><input name="pw" type="password" placeholder="PIN" required style="width:100%;padding:10px;"><br><br><button style="background:#e50914;color:#fff;width:100%;padding:10px;border:none;border-radius:6px;">CONFIRM</button></form></div></div>""", t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "delete": cloudinary.uploader.destroy(p, resource_type="video", invalidate=True)
            return redirect("/")
        else:
            if t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type="image", invalidate=True)
                cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect(url_for('pdf_home'))
    return "Wrong PIN"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
