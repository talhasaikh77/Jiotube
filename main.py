import os
import time
import hashlib
import certifi
import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jio_final_stable_v41"

# --- Gemini Configuration ---
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- Database Setup ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col = db['users']
    chat_col = db['chat_history']
except Exception as e:
    print(f"DB Error: {e}")

ADMIN_PASSWORD = "809047"

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    :root { --jio: #0072ef; --bg: #f4f7f6; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color: #333; }
    .header { background: var(--jio); padding:12px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:100;}
    .card { background: #fff; margin:10px; border-radius:8px; border: 1px solid #ddd; overflow:hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; border:none; font-size:12px; cursor:pointer; display:inline-block; }
    .btn-jio { background: var(--jio); }
    .thumb { width:100%; height:170px; object-fit: cover; background:#000; }
    .chat-box { height:60vh; overflow-y:auto; padding:10px; display:flex; flex-direction:column; gap:10px; background:#fff; }
    .m-u { align-self:flex-end; background:#e1f5fe; padding:8px; border-radius:8px 8px 0 8px; max-width:80%; font-size:13px; border:1px solid #b3e5fc; }
    .m-ai { align-self:flex-start; background:#f1f1f1; padding:8px; border-radius:8px 8px 8px 0; max-width:80%; font-size:13px; border:1px solid #e0e0e0; }
</style>"""

@app.route("/")
def index():
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20)
        videos = res.get("resources", [])
    except: videos = []
    v_html = "".join([f'<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:10px;"><b>{v["public_id"]}</b><br><br><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a></div></div>' for v in videos])
    return f'{STYLE}<div class="header"><b>JioTube</b><div><a href="/ai_home" class="btn" style="border:1px solid #fff">AI</a></div></div>{v_html}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioAI</b><a href="/logout" class="btn" style="background:#e50914;">OUT</a></div><div style="padding:20px;"><a href="/ai_chatter" class="btn btn-jio" style="display:block; text-align:center; padding:15px;">AI CHATTER (JOYA)</a></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        try:
            response = model.generate_content(f"User asked: {msg}. Reply briefly in Hindi as Joya AI.")
            ai_resp = response.text
        except: ai_resp = "API Error. Check your Key."
        chat_col.insert_one({"u": session['u'], "msg": msg, "resp": ai_resp, "t": time.time()})
        return redirect(url_for('ai_chatter'))
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="m-u">{c["msg"]}</div><div class="m-ai"><b>Joya:</b> {c["resp"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn">←</a><b>Joya AI</b></div><div class="chat-box" id="cb">{c_html}</div><form method="POST" style="padding:10px; display:flex; gap:5px; background:#eee;"><input name="msg" style="flex:1; padding:10px; border-radius:5px; border:1px solid #ccc;" placeholder="Ask..." required><button class="btn btn-jio">SEND</button></form><script>var b=document.getElementById("cb"); b.scrollTop=b.scrollHeight;</script>'''

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

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
