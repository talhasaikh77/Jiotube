import os, hashlib, certifi, time
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "atif_mega_search_v5"
app.permanent_session_lifetime = timedelta(days=30)

# Database
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col = db['users']
    ai_col = db['ai_history']
except: print("DB Connection Error")

ADMIN_PW = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

# CSS for Premium Look
STYLE = """<style>
    body { margin:0; font-family:sans-serif; background:#f4f7f6; }
    .header { background: linear-gradient(135deg, #1e3c72, #2a5298); color:#fff; padding:15px; text-align:center; position:sticky; top:0; z-index:100; box-shadow:0 2px 10px rgba(0,0,0,0.3); }
    .card { background:#fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1); border-bottom:4px solid #0078d7; }
    .btn { display:inline-block; padding:10px 14px; border-radius:5px; text-decoration:none; font-size:11px; font-weight:bold; color:#fff; margin:2px; }
    .btn-dl { background:#28a745; } .btn-play { background:#0078d7; } .btn-del { background:#e74c3c; } .btn-ren { background:#f39c12; }
    .search-box { background:#fff; display:flex; margin:10px; border-radius:25px; overflow:hidden; border:1px solid #ddd; }
    .search-box input { flex:1; border:none; padding:12px 15px; outline:none; }
    .search-box button { background:#333; color:#fff; border:none; padding:0 20px; font-weight:bold; }
    .thumb { width:100%; height:180px; object-fit:cover; background:#000; }
</style>"""

# --- JIOTUBE (VIDEO SEARCH & DL) ---
@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    
    v_html = "".join([f"""<div class="card">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb">
        <div style="padding:10px;"><b style="color:#333;">{v["public_id"]}</b></div>
        <div style="padding:8px; background:#f9f9f9; display:flex; flex-wrap:wrap;">
            <a href="{v["secure_url"]}" class="btn btn-play">PLAY</a>
            <a href="{v["secure_url"]}" download class="btn btn-dl">DOWNLOAD</a>
            <a href="/modify?task=rename&pid={v["public_id"]}" class="btn btn-ren">RENAME</a>
            <a href="/modify?task=delete&pid={v["public_id"]}" class="btn btn-del">DELETE</a>
        </div>
    </div>""" for v in videos])
    
    return f"""{STYLE}<div class="header">
        <h2 style="margin:0;">JioTube Pro Max</h2>
        <div style="margin-top:10px;">
            <a href="/pdf_home" class="btn btn-del">PDF SYSTEM</a>
            <a href="/ai_home" class="btn btn-purple" style="background:#9b59b6;">AI MACHINE</a>
        </div>
    </div>
    <form class="search-box"><input name="q" placeholder="Search videos..." value="{q}"><button>GO</button></form>
    {v_html}
    {"<div style='text-align:center;'><a href='/?next="+new_c+"&q="+q+"' class='btn' style='background:#333;width:80%;padding:15px;'>LOAD NEXT ↓</a></div>" if new_c else ""}
    """

# --- PDF VIEWER (SEARCH & DL) ---
@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try:
        # Fetching PDFs from pdf_data/ folder
        res = cloudinary.api.resources(resource_type="image", prefix="pdf_data/", type="upload", max_results=100)
        pdfs = [p for p in res.get("resources", []) if q in p.get("public_id", "").lower()]
    except: pdfs = []
    
    p_html = "".join([f"""<div class="card" style="border-left:8px solid #e74c3c; padding:15px;">
        <div style="margin-bottom:10px;"><b style="color:#2c3e50;">📄 {p["public_id"].replace("pdf_data/","")}</b></div>
        <div style="display:flex;">
            <a href="{p["secure_url"]}" class="btn btn-play" style="flex:1;text-align:center;">VIEW PDF</a>
            <a href="{p["secure_url"]}" download class="btn btn-dl" style="flex:1;text-align:center;">DOWNLOAD</a>
            <a href="/modify?task=delete&pid={p["public_id"]}" class="btn btn-del">DEL</a>
        </div>
    </div>""" for p in pdfs])
    
    return f"""{STYLE}<div class="header" style="background:#c0392b;">
        <h2 style="margin:0;">PDF Search Engine</h2>
        <a href="/" style="color:#fff;text-decoration:none;font-size:12px;">← BACK TO VIDEOS</a>
    </div>
    <form class="search-box"><input name="q" placeholder="Search PDFs..." value="{q}"><button style="background:#c0392b;">SEARCH</button></form>
    <div style="padding:5px;">{p_html if p_html else "<p style='text-align:center;'>No PDF Found</p>"}</div>"""

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('login'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" style="width:100%;"><div style="padding:10px;text-align:center;"><a href="{i["url"]}" download class="btn btn-dl" style="width:90%;">DOWNLOAD ENHANCED</a></div></div>' for i in history])
    
    return f"""{STYLE}<div class="header" style="background:#8e44ad;"><h2>AI Enhancer</h2><a href="/" style="color:#fff;">← HOME</a></div>
    <div class="card" style="padding:20px;text-align:center;">
        <form action="/enhance" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required><br><br>
            <button class="btn" style="background:#8e44ad;width:100%;padding:15px;border:none;">ENHANCE NOW</button>
        </form>
    </div>
    <div style="padding:10px;">{h_html}</div>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('login'))
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", transformation=[{"effect": "grayscale"}, {"contrast": "auto"}, {"sharpen": 300}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_home'))

@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = users_col.find_one({"m": request.form.get("m")})
        if u and u['p'] == hash_pw(request.form.get("pw")):
            session.permanent = True; session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="background:#1e3c72;display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:80%;padding:30px;text-align:center;"><h3>AI Login</h3><form method="POST"><input name="m" placeholder="Mobile" style="width:100%;padding:10px;margin:5px 0;"><br><input name="pw" type="password" placeholder="Pass" style="width:100%;padding:10px;margin:5px 0;"><br><button class="btn btn-play" style="width:100%;border:none;padding:12px;">LOGIN</button></form></div></body>'

@app.route("/admin_upload")
def admin_upload():
    return f'{STYLE}<div class="header"><h2>Admin Upload</h2></div><div class="card" style="padding:20px;"><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><br><br><input name="name" placeholder="File Name"><br><br><input name="pw" placeholder="Admin Pass"><br><br><button class="btn btn-play" style="width:100%;border:none;padding:15px;">START UPLOAD</button></form></div>'

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PW:
        f = request.files.get("file"); n = request.form.get("name", "file").replace(" ","_")
        # Auto-Folder logic
        folder = "pdf_data" if f.filename.lower().endswith('.pdf') else "video_data"
        if f: cloudinary.uploader.upload(f, resource_type="auto", public_id=f"{folder}/{n}")
    return redirect("/")

@app.route("/modify")
def modify():
    return render_template_string(f'{STYLE}<div class="header"><h2>Confirm Action</h2></div><div class="card" style="padding:20px;text-align:center;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{{{p}}}}"><input type="hidden" name="task" value="{{{{t}}}}">{{% if t=="rename" %}}<input name="new" placeholder="New Name" style="width:100%;padding:10px;margin-bottom:10px;"><br>{{% endif %}}<input name="pw" placeholder="Admin Pass" style="width:100%;padding:10px;"><br><br><button class="btn btn-ren" style="width:100%;border:none;padding:15px;">EXECUTE</button></form></div>', t=request.args.get("task"), p=request.args.get("pid"))

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PW:
        t, p = request.form.get("task"), request.form.get("pid")
        if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"))
        elif t == "delete": cloudinary.uploader.destroy(p, resource_type="auto")
    return redirect("/")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
