import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v61_fixed"

# --- Gemini Config (Safe Mode) ---
try:
    genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Gemini Init Error: {e}")

# --- DB & Cloud (Retry Logic) ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

db, chat_col = None, None
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = client.get_database('Atif_AI_Database')
    chat_col = db['chat_history']
except Exception as e:
    print(f"DB Error: {e}")

STYLE = """<style>
    :root { --jio: #0072ef; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:12px; overflow:hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 10px; }
    .btn { padding:12px; border-radius:8px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; }
    .btn-jio { background: var(--jio); } .btn-del { background: #e63946; } .btn-edit { background: #fca311; } .btn-down { background: #2a9d8f; }
    .msg { position:relative; margin:10px; padding:15px; border-radius:15px; max-width:85%; font-size:14px; line-height:1.5; }
    .u-msg { align-self: flex-end; background: #dcf8c6; margin-left: auto; }
    .ai-msg { align-self: flex-start; background: #fff; border: 1px solid #eee; }
    .chat-area { position:fixed; bottom:0; width:100%; display:flex; padding:12px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box; gap:8px; }
</style>"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids = [v for v in res.get("resources", []) if q.lower() in v["public_id"].lower()]
        new_curs = res.get("next_cursor")
    except: vids, new_curs = [], None
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:190px; object-fit:cover;"><div style="padding:12px;"><b>{v["public_id"]}</b></div><div class="btn-grid"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}" class="btn btn-del">DELETE</a><a href="{v["secure_url"]}" download class="btn btn-down">DOWNLOAD</a></div></div>''' for v in vids])
    p_btn = f'<a href="/?next={new_curs}&q={q}" style="display:block; text-align:center; padding:15px; background:#fff; margin:10px; border-radius:10px; text-decoration:none; color:var(--jio); font-weight:bold;">NEXT 10</a>' if new_curs else ""
    return f'{STYLE}<div class="header"><b>JioTube</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_auth" class="btn">AI</a></div></div>{v_html}{p_btn}'

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if 'u' in session: return redirect(url_for('ai_chatter'))
    if request.method == "POST":
        session['u'] = request.form.get("name")
        return redirect(url_for('ai_chatter'))
    return f'{STYLE}<div style="padding:60px 20px; text-align:center;"><div class="card" style="padding:30px;"><h2>Login</h2><form method="POST"><input name="name" placeholder="Name" required style="width:100%; padding:15px; margin-bottom:15px;"><button class="btn btn-jio" style="width:100%;">START</button></form></div></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        p = request.form.get("q")
        try:
            r = model.generate_content(p)
            chat_col.insert_one({"u": session['u'], "q": p, "a": r.text, "t": time.time()})
        except Exception as e:
            chat_col.insert_one({"u": session['u'], "q": p, "a": "AI Busy or Offline. Try again.", "t": time.time()})
        return redirect(url_for('ai_chatter'))
    
    chats = []
    if chat_col:
        chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="msg u-msg">{c["q"]}</div><div class="msg ai-msg"><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Joya AI</b><a href="/logout" class="btn btn-del">OUT</a></div><div style="display:flex; flex-direction:column; padding-bottom:100px;">{c_html}</div><form method="POST" class="chat-area"><input name="q" style="flex:1; padding:12px; border-radius:10px; border:1px solid #ccc;" placeholder="Ask..." required><button class="btn btn-jio">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"]}</b><div class="btn-grid"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=100)
    pages = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg","png","jpeg"]], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%;">' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{n}</b></div>{h}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
