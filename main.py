import os, time, hashlib, certifi, requests, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v57_ultra"

# --- AI Configuration ---
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DB & Cloud ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    chat_col = db['chat_history']
    user_col = db['users']
except: print("DB Connection Failed")

STYLE = """<style>
    :root { --jio: #0072ef; --bg: #f0f2f5; }
    body { margin:0; font-family: sans-serif; background: var(--bg); }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:12px; overflow:hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 10px; }
    .btn { padding:10px; border-radius:5px; text-decoration:none; color:#fff; font-size:11px; text-align:center; font-weight:bold; border:none; }
    .btn-jio { background: var(--jio); } .btn-del { background: #d00; } .btn-edit { background: #f80; } .btn-down { background: #28a745; }
    .thumb { width:100%; height:180px; object-fit: cover; }
    .search-box { padding:10px; background:#fff; display:flex; gap:5px; }
    .search-box input { flex:1; padding:10px; border:1px solid #ccc; border-radius:5px; }
    .chat-msg { position:relative; margin:10px; padding:12px; border-radius:10px; max-width:80%; font-size:14px; }
    .u-msg { align-self: flex-end; background: #dcf8c6; margin-left: auto; }
    .ai-msg { align-self: flex-start; background: #fff; border: 1px solid #ddd; }
    .del-chat { position:absolute; top:-5px; right:-5px; background:red; color:#fff; border-radius:50%; width:18px; height:18px; font-size:12px; text-align:center; cursor:pointer; text-decoration:none; line-height:18px; }
    .nav-btn { display:block; text-align:center; padding:15px; background:#fff; margin:10px; border-radius:10px; text-decoration:none; color:var(--jio); font-weight:bold; }
</style>"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    next_cursor = request.args.get("next")
    try:
        # Advanced Search Logic
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_cursor)
        all_vids = res.get("resources", [])
        vids = [v for v in all_vids if q.lower() in v["public_id"].lower()] if q else all_vids
        new_next = res.get("next_cursor")
    except: vids, new_next = [], None

    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:10px;"><b>{v["public_id"]}</b></div><div class="btn-grid"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}" class="btn btn-del">DELETE</a><a href="{v["secure_url"]}" download class="btn btn-down">DOWNLOAD</a></div></div>''' for v in vids])
    
    page_html = f'<a href="/?next={new_next}&q={q}" class="nav-btn">NEXT PAGE →</a>' if new_next else ""
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_home" class="btn">AI</a></div></div><form class="search-box"><input name="q" placeholder="Auto-correct Search..." value="{q}"><button class="btn btn-jio">GO</button></form>{v_html}{page_html}'

@app.route("/ai_home")
def ai_home():
    if 'user' not in session: return redirect("/ai_login")
    return redirect("/ai_chatter")

@app.route("/ai_login", methods=["GET", "POST"])
def ai_login():
    if request.method == "POST":
        user = request.form.get("user")
        session['user'] = user
        return redirect("/ai_chatter")
    return f'{STYLE}<div style="padding:50px; text-align:center;"><h3>AI Registration</h3><form method="POST"><input name="user" placeholder="Enter Name" required style="width:80%; padding:10px; margin-bottom:10px;"><br><button class="btn btn-jio" style="width:80%;">LOGIN / JOIN</button></form></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'user' not in session: return redirect("/ai_login")
    user = session['user']
    if request.method == "POST":
        msg = request.form.get("msg")
        try:
            # AI Fix: Better prompt to avoid busy
            response = model.generate_content(f"You are Joya, a friendly AI. User says: {msg}")
            bot_reply = response.text
        except: bot_reply = "AI is refreshing. Please send again."
        chat_col.insert_one({"user": user, "msg": msg, "bot": bot_reply, "time": time.time()})
        return redirect("/ai_chatter")

    chats = list(chat_col.find({"user": user}).sort("time", 1))
    c_html = "".join([f'''<div class="chat-msg u-msg"><a href="/del_chat?id={c["_id"]}" class="del-chat">x</a>{c["msg"]}</div><div class="chat-msg ai-msg"><b>Joya:</b> {c["bot"]}</div>''' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">←</a><b>Chat with Joya</b><a href="/logout" class="btn btn-del">OUT</a></div><div style="display:flex; flex-direction:column; padding-bottom:80px;">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box;"><input name="msg" style="flex:1; padding:12px; border-radius:5px; border:1px solid #ccc;" placeholder="Ask Joya anything..." required><button class="btn btn-jio">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/del_chat")
def del_chat():
    cid = request.args.get("id")
    chat_col.delete_one({"_id": ObjectId(cid)})
    return redirect("/ai_chatter")

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><div class="btn-grid"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN BOOK</a><a href="/modify?t=delete&p={f["name"]}&tp=pdf" class="btn btn-del">DELETE</a></div></div>' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/" class="btn">←</a><b>JioBooks</b></div><form class="search-box"><input name="q" placeholder="Search Books..." value="{q}"><button class="btn btn-jio">FIND</button></form>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=100)
        # Sahi URL logic for PDF images
        pages = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg", "png", "webp", "jpeg"]], key=lambda x: x["public_id"])
        if not pages: return "<h3>No pages found in this book!</h3>"
        h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; margin-bottom:5px;">' for p in pages])
        return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{name}</b></div>{h}'
    except: return "<h3>Error loading PDF folder!</h3>"

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
