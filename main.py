import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v66_secure_login"

# --- Gemini Config ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DB & Cloud ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
chat_col = db['chat_history']
user_col = db['users'] # New collection for login

STYLE = """<style>
    :root { --jio: #0072ef; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:20px auto; padding:20px; border-radius:12px; max-width:400px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .btn { padding:12px; border-radius:8px; text-decoration:none; color:#fff; font-size:14px; text-align:center; font-weight:bold; border:none; cursor:pointer; width:100%; display:block; }
    .btn-jio { background: var(--jio); } .btn-del { background: #e63946; }
    input { width:100%; padding:12px; margin:10px 0; border-radius:8px; border:1px solid #ccc; box-sizing:border-box; }
    .msg { position:relative; margin:10px; padding:15px; border-radius:15px; max-width:85%; font-size:14px; }
    .u-msg { align-self: flex-end; background: #dcf8c6; margin-left: auto; }
    .ai-msg { align-self: flex-start; background: #fff; border: 1px solid #eee; }
    .chat-input-area { position:fixed; bottom:0; width:100%; display:flex; padding:12px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box; gap:8px; }
    #loader { display:none; text-align:center; padding:10px; color: var(--jio); font-weight:bold; font-size:13px; }
</style>"""

@app.route("/")
def index():
    if 'user' in session: return redirect(url_for('ai_chatter'))
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        pw = request.form.get("pw")
        user = user_col.find_one({"phone": phone, "pw": pw})
        if user:
            session['user'] = phone
            return redirect(url_for('ai_chatter'))
        return "<h3>Galat Password ya Mobile No! <a href='/login'>Try Again</a></h3>"
    return f'{STYLE}<div class="header"><b>JioAI Login</b></div><div class="card"><h2>Login</h2><form method="POST"><input name="phone" placeholder="Mobile Number" required><input name="pw" type="password" placeholder="Password" required><button class="btn btn-jio">LOGIN</button></form><br><a href="/register" style="text-decoration:none; color:var(--jio);">Naya Account Banayein</a></div>'

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        phone = request.form.get("phone")
        pw = request.form.get("pw")
        if user_col.find_one({"phone": phone}): return "Mobile Number pehle se hai!"
        user_col.insert_one({"phone": phone, "pw": pw})
        return "<h3>Account Ban Gaya! <a href='/login'>Login Karein</a></h3>"
    return f'{STYLE}<div class="header"><b>JioAI Register</b></div><div class="card"><h2>Naya Account</h2><form method="POST"><input name="phone" placeholder="Mobile Number" required><input name="pw" type="password" placeholder="Password" required><button class="btn btn-jio">REGISTER</button></form></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'user' not in session: return redirect(url_for('login'))
    
    if request.method == "POST":
        q = request.form.get("q")
        try:
            r = model.generate_content(q)
            chat_col.insert_one({"u": session['user'], "q": q, "a": r.text, "t": time.time()})
        except: pass
        return redirect(url_for('ai_chatter'))
    
    chats = list(chat_col.find({"u": session['user']}).sort("t", 1))
    c_html = "".join([f'<div class="msg u-msg">{c.get("q", "...")}</div><div class="msg ai-msg"><b>Joya:</b> {c.get("a", "Thinking...")}</div>' for c in chats])
    
    return f'''{STYLE}
    <div class="header"><b>Joya AI</b><div style="display:flex; gap:10px;"><a href="/logout" style="color:#fff; text-decoration:none; font-size:12px;">LOGOUT</a></div></div>
    <div id="chat-box" style="display:flex; flex-direction:column; padding-bottom:120px;">{c_html}</div>
    <div id="loader">Joya jawab likh rahi hai...</div>
    <form method="POST" id="chat-form" class="chat-input-area" onsubmit="startLoading()">
        <input name="q" placeholder="Sawal puchei..." required>
        <button class="btn btn-jio" style="width:80px;">SEND</button>
    </form>
    <script>
        function startLoading() {{
            document.getElementById('loader').style.display = 'block';
            document.getElementById('chat-form').style.opacity = '0.5';
            window.scrollTo(0, document.body.scrollHeight);
        }}
        window.scrollTo(0, document.body.scrollHeight);
    </script>'''

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
