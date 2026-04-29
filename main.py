import os, hashlib, certifi
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api

app = Flask(__name__)
app.secret_key = "atif_secure_key_786"

# Configuration (Naya Password: AtifAI12345)
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

# Stable DB Connection
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client['Atif_AI_Database']
    users_col = db['users']
except Exception as e:
    print(f"Connection Error: {e}")

ADMIN_PASSWORD = "809047"

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    
    v_list = "".join([f"""<div style="background:#fff;border-bottom:2px solid #ddd;padding:5px;margin-bottom:10px;"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;max-height:150px;object-fit:fill;background:#000;display:block;"><b style="font-size:12px;display:block;padding:5px;color:#333;">{v["public_id"]}</b><div style="display:flex;gap:4px;padding:2px;"><a href="{v["secure_url"]}" style="flex:1;background:#0078d7;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">PLAY</a><a href="/ai_login" style="flex:1;background:#9b59b6;color:#fff;text-align:center;padding:8px;text-decoration:none;font-size:10px;border-radius:4px;font-weight:bold;">AI ENHANCE</a></div></div>""" for v in videos])
    next_btn = f"<a href='/?next={new_c}&q={q}' style='display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;font-weight:bold;margin:10px;border-radius:5px;'>LOAD NEXT ↓</a>" if new_c else ""
    
    return f"""<body style="margin:0;font-family:sans-serif;background:#eee;"><div style="background:#0078d7;color:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><h3 style="margin:0;">JioTube Pro</h3><div style="display:flex;gap:5px;margin-top:8px;"><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">PDF VIEWER</a><a href="/ai_login" style="flex:1;background:#9b59b6;color:#fff;padding:8px;text-decoration:none;font-size:11px;border-radius:4px;font-weight:bold;">AI ENHANCE</a></div></div>{v_list}{next_btn}</body>"""

@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        m = request.form.get("mobile"); p = request.form.get("pw")
        try:
            u = users_col.find_one({"mobile": m})
            if u and u['password'] == hash_pw(p):
                session['user_id'] = str(u['_id']); session.permanent = True
                return redirect(url_for('ai_home'))
        except: return "Database busy, try again!"
        return "Ghalat Details!"
    return render_template_string('<body style="padding:20px;text-align:center;background:#eee;"><h3>Login AI</h3><form method="POST"><input type="number" name="mobile" placeholder="Mobile" style="width:90%;padding:15px;margin-bottom:10px;"><br><input type="password" name="pw" placeholder="Pass" style="width:90%;padding:15px;margin-bottom:15px;"><br><button style="width:90%;padding:15px;background:#9b59b6;color:#fff;border:none;border-radius:5px;">LOGIN</button></form><p><a href="/ai_register">Register</a> | <a href="/">Home</a></p></body>')

@app.route("/ai_register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        m = request.form.get("mobile"); p = request.form.get("pw")
        if not m or not p: return "Fill all fields!"
        try:
            if users_col.find_one({"mobile": m}): return "Exists!"
            users_col.insert_one({"mobile": m, "password": hash_pw(p)})
            return 'OK! <a href="/ai_login">Login</a>'
        except Exception as e: return f"Error: {e}"
    return render_template_string('<body style="padding:20px;text-align:center;background:#eee;"><h3>Register</h3><form method="POST"><input type="number" name="mobile" placeholder="Mobile" style="width:90%;padding:15px;margin-bottom:10px;"><br><input type="password" name="pw" placeholder="Pass" style="width:90%;padding:15px;margin-bottom:15px;"><br><button style="width:90%;padding:15px;background:#28a745;color:#fff;border:none;border-radius:5px;">CREATE</button></form></body>')

@app.route("/ai_home")
def ai_home():
    if 'user_id' not in session: return redirect(url_for('login'))
    return "AI Panel coming soon! <a href='/logout'>Logout</a>"

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

@app.route("/pdf_home")
def pdf_home(): return "PDF Viewer logic here... <a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
