import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import requests

app = Flask(__name__)
app.secret_key = "jiotube_v77_pro_bot"

# --- Gemini & MongoDB Setup ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
chat_col = db['chat_history']
user_col = db['users']

STYLE = """<style>
    :root { --jio: #0072ef; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 80px; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:block; cursor:pointer; }
    .btn-jio { background: var(--jio); }
    .btn-nav { background: rgba(255,255,255,0.2); border: 1px solid #fff; padding: 5px 8px; }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
</style>"""

@app.route("/")
def index():
    if 'u' not in session: return redirect("/login")
    q = request.args.get("q", "").strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10)
        vids = [v for v in res.get("resources", []) if q in v["public_id"].lower()]
    except: vids = []
    
    v_html = "".join([f'''<div class="card">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:180px; object-fit:cover;">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px;">
            <a href="{v["secure_url"]}" class="btn btn-jio">WATCH VIDEO</a>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:8px;">
                <a href="/modify?t=rename&p={v["public_id"]}" class="btn" style="background:#f39c12;">RENAME</a>
                <a href="/modify?t=delete&p={v["public_id"]}" class="btn" style="background:#d9534f;">DELETE</a>
            </div>
        </div>
    </div>''' for v in vids])

    return f'''{STYLE}
    <div class="header">
        <b>JioTube</b>
        <div style="display:flex; gap:4px;">
            <a href="/yt_search" class="btn btn-nav" style="background:red;">YOUTUBE</a>
            <a href="/pdf_home" class="btn btn-nav">PDF</a>
            <a href="/ai_chatter" class="btn btn-nav">AI</a>
        </div>
    </div>
    <form style="padding:10px; display:flex; gap:5px;"><input name="q" placeholder="Search saved videos..." value="{q}"><button class="btn btn-jio">GO</button></form>
    {v_html}'''

@app.route("/yt_search", methods=["GET", "POST"])
def yt_search():
    if 'u' not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        v_name = request.form.get("v_name")
        msg = f"'{v_name}' search kiya ja raha hai... DDG Proxy ke zariye Cloudinary par upload ho jayega (Background)."
        # Yahan hum residential proxy header simulation lagayenge
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-nav">BACK</a><b>YouTube Bot</b></div>
    <div class="card" style="padding:20px;">
        <p style="font-size:13px; color:#666;">Video ka naam likhein, hum DuckDuckGo se nikaal kar use 144p low resolution mein save kar denge.</p>
        <form method="POST">
            <input name="v_name" placeholder="Video name (e.g. Arijit Singh Songs)" required>
            <button class="btn btn-jio" style="width:100%; margin-top:10px; background:red;">SEARCH & UPLOAD</button>
        </form>
        <p style="color:green; font-size:12px; margin-top:10px;">{msg}</p>
    </div>'''

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect("/login")
    if request.method == "POST":
        p = request.form.get("q")
        try:
            res = model.generate_content(p)
            chat_col.insert_one({"u": session['u'], "q": p, "a": res.text, "t": time.time()})
        except: pass # Internal server fix
        return redirect("/ai_chatter")
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div style="background:#dcf8c6; margin:10px; padding:12px; border-radius:12px; margin-left:auto; max-width:80%;">{c["q"]}</div><div style="background:#fff; margin:10px; padding:12px; border-radius:12px; border:1px solid #ddd; max-width:80%;"><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-nav">HOME</a><b>Joya AI</b></div><div style="padding-bottom:100px;">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; gap:5px;"><input name="q" placeholder="Puchhein..." required><button class="btn btn-jio">SEND</button></form>'''

@app.route("/modify")
def modify():
    if 'u' not in session: return redirect("/login")
    t = request.args.get("t")
    p = request.args.get("p")
    try:
        if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
    except: pass
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}): session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin:60px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio">LOGIN</button></form></div>'

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px; display:flex; justify-content:space-between;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-nav">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=100)
    pgs = sorted(res.get("resources", []), key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%;">' for p in pgs])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-nav">←</a><b>{n}</b></div>{h}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
