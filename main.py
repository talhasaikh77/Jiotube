import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v67_full_system"

# --- Gemini Config ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DB & Cloud ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
chat_col = db['chat_history']
user_col = db['users']

STYLE = """<style>
    :root { --jio: #0072ef; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 70px; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 10px; }
    .btn { padding:10px; border-radius:5px; text-decoration:none; color:#fff; font-size:11px; text-align:center; font-weight:bold; border:none; display:block; }
    .btn-jio { background: var(--jio); } .btn-del { background: #d00; } .btn-down { background: #28a745; }
    .search-box { padding:10px; display:flex; gap:5px; background:#fff; border-bottom:1px solid #ddd; }
    .search-box input { flex:1; padding:10px; border:1px solid #ccc; border-radius:5px; }
    .msg { margin:10px; padding:12px; border-radius:10px; max-width:85%; font-size:14px; position:relative; }
    .u-msg { background: #dcf8c6; margin-left: auto; border: 1px solid #c3e6cb; }
    .ai-msg { background: #fff; border: 1px solid #ddd; }
    .chat-form { position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box; gap:5px; }
</style>"""

@app.route("/")
def index():
    if 'u' not in session: return redirect(url_for('login'))
    q = request.args.get("q", "").strip()
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids = [v for v in res.get("resources", []) if q.lower() in v["public_id"].lower()]
        new_curs = res.get("next_cursor")
    except: vids, new_curs = [], None
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:180px; object-fit:cover;"><div style="padding:10px;"><b>{v["public_id"]}</b></div><div class="btn-grid"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="{v["secure_url"]}" download class="btn btn-down">DOWNLOAD</a><a href="/modify?t=delete&p={v["public_id"]}" class="btn btn-del">DELETE</a></div></div>''' for v in vids])
    next_btn = f'<a href="/?next={new_curs}&q={q}" style="display:block; text-align:center; padding:15px; background:#fff; margin:10px; border-radius:10px; text-decoration:none; color:var(--jio); font-weight:bold; border:1px solid var(--jio);">LOAD NEXT 10</a>' if new_curs else ""
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_chatter" class="btn">AI</a></div></div><form class="search-box"><input name="q" placeholder="Video Search..." value="{q}"><button class="btn btn-jio" style="width:60px;">GO</button></form>{v_html}{next_btn}'

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}):
            session['u'] = p
            return redirect("/")
        return "Wrong Info! <a href='/login'>Retry</a>"
    return f'{STYLE}<div class="card" style="margin-top:50px;"><h2>Login</h2><form method="POST"><input name="p" placeholder="Phone" required style="width:100%; padding:10px; margin:5px 0;"><input name="pw" type="password" placeholder="Pass" required style="width:100%; padding:10px; margin:5px 0;"><button class="btn btn-jio">LOGIN</button></form><br><a href="/reg">New? Register</a></div>'

@app.route("/reg", methods=["GET", "POST"])
def reg():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p}): return "Exists!"
        user_col.insert_one({"p": p, "pw": pw})
        return "Done! <a href='/login'>Login</a>"
    return f'{STYLE}<div class="card" style="margin-top:50px;"><h2>Register</h2><form method="POST"><input name="p" placeholder="Phone" required style="width:100%; padding:10px; margin:5px 0;"><input name="pw" placeholder="Pass" required style="width:100%; padding:10px; margin:5px 0;"><button class="btn btn-jio">SIGN UP</button></form></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect("/login")
    if request.method == "POST":
        prompt = request.form.get("q")
        try:
            # Browser waits here until API response is ready
            res = model.generate_content(prompt)
            chat_col.insert_one({"u": session['u'], "q": prompt, "a": res.text, "t": time.time()})
        except: pass
        return redirect("/ai_chatter")
    
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="msg u-msg">{c.get("q","...")}</div><div class="msg ai-msg"><b>Joya:</b> {c.get("a","Thinking...")}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Joya AI</b><a href="/logout" class="btn btn-del" style="font-size:10px;">OUT</a></div><div style="display:flex; flex-direction:column;">{c_html}</div><form method="POST" class="chat-form"><input name="q" placeholder="Sawal likhein..." required style="flex:1; padding:10px; border-radius:5px; border:1px solid #ccc;"><button class="btn btn-jio" style="width:60px;">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><div class="btn-grid"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN BOOK</a></div></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=100)
    pgs = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg","png","jpeg"]], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; margin-bottom:2px;">' for p in pgs])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{n}</b></div>{h}'

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
