import os, time, hashlib, certifi, requests, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_chat_save_v44"

# --- API & DB ---
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col = db['users']
    chat_col = db['chat_history'] # Yahan saari chatting save hogi
    ai_col = db['ai_history']
except: print("DB Connection Error")

ADMIN_PIN = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    :root { --jio: #0072ef; --bg: #f4f7f6; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color: #333; }
    .header { background: var(--jio); padding:12px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:8px; border: 1px solid #ddd; overflow:hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .btn { padding:8px 12px; border-radius:5px; text-decoration:none; color:#fff; font-size:12px; cursor:pointer; border:none; font-weight:bold; }
    .btn-jio { background: var(--jio); }
    .btn-del { background: #e50914; }
    .btn-edit { background: #ff9800; }
    .btn-down { background: #28a745; }
    .thumb { width:100%; height:160px; object-fit: cover; background:#000; }
    .search-engine { display:flex; margin:10px; gap:5px; }
    .search-engine input { flex:1; padding:10px; border-radius:5px; border:1px solid #ccc; }
    .chat-box { height:60vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:12px; background:#fff; }
    .m-u { align-self:flex-end; background:#e1f5fe; padding:10px; border-radius:10px 10px 0 10px; max-width:85%; font-size:13px; border:1px solid #b3e5fc; }
    .m-ai { align-self:flex-start; background:#f1f1f1; padding:10px; border-radius:10px 10px 10px 0; max-width:85%; font-size:13px; border:1px solid #e0e0e0; }
</style>"""

@app.route("/")
def home():
    q = request.args.get("q", "").lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=50)
        vids = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
    except: vids = []
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:10px;"><b>{v["public_id"]}</b><div style="margin-top:10px; display:flex; gap:5px;"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}&tp=video" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}&tp=video" class="btn btn-del">DELETE</a></div></div></div>''' for v in vids])
    return f'{STYLE}<div class="header"><b>JioTube</b><div><a href="/pdf_home" class="btn" style="border:1px solid #fff">BOOKS</a> <a href="/ai_home" class="btn" style="border:1px solid #fff">AI</a></div></div><form class="search-engine"><input name="q" placeholder="Search Videos..." value="{q}"><button class="btn btn-jio">GO</button></form>{v_html}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioAI</b><a href="/logout" class="btn btn-del">OUT</a></div><div style="padding:20px;"><a href="/ai_chatter" class="btn btn-jio" style="display:block; text-align:center; background:#28a745; padding:15px; margin-bottom:15px;">AI JOYA (CHATTING)</a><a href="/ai_enhance" class="btn btn-jio" style="display:block; text-align:center; padding:15px;">PHOTO ENHANCER</a></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        # Step 1: Save User Message first
        chat_col.insert_one({"u": session['u'], "role": "user", "text": msg, "t": time.time()})
        try:
            # Step 2: Get Gemini Response
            resp = model.generate_content(f"Hindi mein jawab do: {msg}")
            ai_text = resp.text
        except: ai_text = "Thoda intezar karein, Joya load ho rahi hai..."
        
        # Step 3: Save AI Response
        chat_col.insert_one({"u": session['u'], "role": "joya", "text": ai_text, "t": time.time()})
        return redirect(url_for('ai_chatter'))

    # Load Full History from Database
    history = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="{"m-u" if c["role"]=="user" else "m-ai"}">{"<b>Joya:</b> " if c["role"]=="joya" else ""}{c["text"]}</div>' for c in history])
    
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn">←</a><b>Joya History</b></div><div class="chat-box" id="cb">{c_html}</div><form method="POST" style="padding:10px; display:flex; gap:5px; background:#eee; position:fixed; bottom:0; width:100%; box-sizing:border-box;"><input name="msg" style="flex:1; padding:10px; border-radius:5px; border:1px solid #ccc;" placeholder="Talk to Joya..." required><button class="btn btn-jio">SEND</button></form><script>var b=document.getElementById("cb"); b.scrollTop=b.scrollHeight;</script>'''

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if users_col.find_one({"m": m}): return "User exists!"
            users_col.insert_one({"m": m, "p": hash_pw(p)})
            return 'Account Created! <a href="/ai_auth">Login Now</a>'
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<div style="padding:50px; text-align:center;"><div class="card" style="padding:20px;"><h3>Jio Login</h3><form method="POST"><input name="m" placeholder="Username" required style="width:100%; padding:10px; margin-bottom:10px;"><br><input name="pw" type="password" placeholder="Password" required style="width:100%; padding:10px;"><br><br><button name="act" value="log" class="btn btn-jio" style="width:100%;">LOGIN</button><br><br><button name="act" value="reg" style="background:none; border:none; color:var(--jio); cursor:pointer;">New? Signup</button></form></div></div>'

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"]}</b><div style="margin-top:10px; display:flex; gap:5px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:1; text-align:center;">OPEN</a><a href="/modify?t=delete&p={f["name"]}&tp=pdf" class="btn btn-del">DELETE</a></div></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Books</b></div>{f_html}<div style="text-align:center; padding:10px;"><button class="btn btn-jio">NEXT PAGE</button></div>'

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
