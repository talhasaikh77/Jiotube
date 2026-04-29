import os, hashlib, certifi, time
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api

app = Flask(__name__)
app.secret_key = "atif_mega_ai_key"

# Database Configuration (Update password if changed)
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col = db['users']
    history_col = db['ai_history']
except: print("DB Connection Error")

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

@app.route("/")
def index():
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;text-align:center;">
    <div style="background:#0078d7;color:#fff;padding:20px;"><h2>JioTube + AI Pro</h2></div>
    <div style="padding:20px;display:grid;gap:15px;">
        <a href="/pdf_home" style="background:#e74c3c;color:#fff;padding:20px;text-decoration:none;border-radius:10px;font-weight:bold;">PDF VIEWER</a>
        <a href="/ai_login" style="background:#9b59b6;color:#fff;padding:20px;text-decoration:none;border-radius:10px;font-weight:bold;">AI ENHANCER</a>
    </div></body>"""

@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = users_col.find_one({"mobile": request.form.get("mobile")})
        if u and u['password'] == hash_pw(request.form.get("pw")):
            session['user_id'] = str(u['_id']); return redirect(url_for('ai_home'))
        return "Wrong Details!"
    return '<body><form method="POST"><h3>Login</h3><input name="mobile" placeholder="Mobile"><br><input name="pw" type="password" placeholder="Pass"><br><button>Login</button></form><a href="/ai_register">Register</a></body>'

@app.route("/ai_register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        m = request.form.get("mobile"); p = request.form.get("pw")
        if users_col.find_one({"mobile": m}): return "Exists!"
        users_col.insert_one({"mobile": m, "password": hash_pw(p)})
        return 'Done! <a href="/ai_login">Login</a>'
    return '<body><form method="POST"><h3>Register</h3><input name="mobile" placeholder="Mobile"><br><input name="pw" type="password" placeholder="Pass"><br><button>Create</button></form></body>'

@app.route("/ai_home")
def ai_home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return f"""<body style="padding:20px;text-align:center;font-family:sans-serif;">
    <h3>AI Machine</h3>
    <form action="/enhance" method="POST" enctype="multipart/form-data" style="background:#fff;padding:20px;border-radius:10px;">
        <input type="file" name="file" style="margin-bottom:10px;"><br>
        <button style="background:#9b59b6;color:#fff;padding:15px 30px;border:none;border-radius:5px;">ENHANCE NOW</button>
    </form>
    <br><a href="/logout">Logout</a></body>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'user_id' not in session: return redirect(url_for('login'))
    f = request.files.get("file")
    if f:
        # AI Processing via Cloudinary (Auto Contrast + Sharpen + Grayscale)
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", 
            transformation=[
                {"effect": "grayscale"},
                {"effect": "improve:outdoor"},
                {"contrast": "auto"},
                {"sharpen": 100}
            ])
        history_col.insert_one({"user": session['user_id'], "url": up['secure_url'], "time": time.time()})
        return f'<h3>Enhanced!</h3><img src="{up["secure_url"]}" style="width:100%"><br><a href="{up["secure_url"]}" download>Download</a><br><a href="/ai_home">Back</a>'
    return "No File"

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

@app.route("/pdf_home")
def pdf_home(): return "PDF Viewer... <a href='/'>Home</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
