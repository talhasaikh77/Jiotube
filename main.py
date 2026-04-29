import os, hashlib, certifi, time
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "atif_mega_pro_v3"
app.permanent_session_lifetime = timedelta(days=30)

# Database & Cloudinary
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

# CSS Styles
STYLE = """<style>
    body { margin:0; font-family:sans-serif; background:#f4f7f6; }
    .header { background: linear-gradient(135deg, #0078d7, #9b59b6); color:#fff; padding:15px; text-align:center; position:sticky; top:0; z-index:100; box-shadow:0 2px 10px rgba(0,0,0,0.2); }
    .card { background:#fff; margin:10px; border-radius:8px; overflow:hidden; box-shadow:0 2px 5px rgba(0,0,0,0.1); border-bottom:3px solid #0078d7; }
    .btn { padding:10px; border-radius:4px; text-decoration:none; font-size:11px; font-weight:bold; text-align:center; color:#fff; flex:1; }
    .search-box { display:flex; margin-top:10px; background:#fff; border-radius:5px; overflow:hidden; }
    .search-box input { flex:1; border:none; padding:10px; outline:none; }
    .search-box button { background:#333; color:#fff; border:none; padding:10px 20px; }
    .grid-btns { display:flex; gap:5px; padding:10px; background:#fafafa; }
    .pdf-item { background:#fff; margin:5px 10px; padding:15px; border-left:5px solid #e74c3c; border-radius:4px; display:block; text-decoration:none; color:#333; font-weight:bold; }
</style>"""

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
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:180px; object-fit:cover; background:#000;">
        <div style="padding:10px;"><b style="font-size:14px; color:#333;">{v["public_id"]}</b></div>
        <div class="grid-btns">
            <a href="{v["secure_url"]}" class="btn" style="background:#0078d7;">PLAY / DL</a>
            <a href="/modify?task=rename&pid={v["public_id"]}" class="btn" style="background:orange;">RENAME</a>
            <a href="/modify?task=delete&pid={v["public_id"]}" class="btn" style="background:red;">DELETE</a>
        </div>
    </div>""" for v in videos])
    
    pagination = f'<a href="/?next={new_c}&q={q}" style="display:block; background:#333; color:#fff; text-align:center; padding:15px; margin:10px; text-decoration:none; border-radius:5px;">LOAD NEXT VIDEOS ↓</a>' if new_c else ""
    
    return f"""{STYLE}<div class="header">
        <h2 style="margin:0;">JioTube Pro Max</h2>
        <div style="display:flex; gap:5px; margin-top:10px;">
            <a href="/admin_upload" class="btn" style="background:#28a745;">+ UPLOAD</a>
            <a href="/pdf_home" class="btn" style="background:#e74c3c;">PDF VIEWER</a>
            <a href="/ai_home" class="btn" style="background:#f1c40f; color:#000;">AI ENHANCE</a>
        </div>
        <form class="search-box"><input name="q" placeholder="Search videos..." value="{q}"><button>GO</button></form>
    </div>{v_html}{pagination}"""

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('login'))
    page = int(request.args.get("p", 0))
    # Fetch user's history with pagination
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).skip(page*10).limit(10))
    
    h_html = "".join([f'<div class="card" style="padding:5px;"><img src="{i["url"]}" style="width:100%;"><br><a href="{i["url"]}" download style="display:block; text-align:center; padding:10px; color:green; text-decoration:none; font-weight:bold;">DOWNLOAD</a></div>' for i in history])
    
    next_btn = f'<a href="/ai_home?p={page+1}" style="display:block; background:#9b59b6; color:#fff; text-align:center; padding:15px; margin:10px; text-decoration:none; border-radius:5px;">VIEW OLDER PHOTOS ↓</a>' if len(history) == 10 else ""
    
    return f"""{STYLE}<div class="header" style="background:#9b59b6;">
        <h2 style="margin:0;">AI Text Enhancer</h2>
        <a href="/" style="color:#fff; font-size:12px;">← Back to Home</a>
    </div>
    <div style="padding:15px; text-align:center;">
        <form action="/enhance" method="POST" enctype="multipart/form-data" style="background:#fff; padding:20px; border-radius:10px; border:2px dashed #9b59b6;">
            <input type="file" name="file" required><br><br>
            <button style="width:100%; padding:15px; background:#9b59b6; color:#fff; border:none; border-radius:5px; font-weight:bold;">START AI ENHANCE & CROP</button>
        </form>
    </div>
    <div style="padding:10px;"><h4>Your History</h4>{h_html}{next_btn}</div>
    <div style="text-align:center; padding:20px;"><a href="/logout" style="color:red;">Logout Account</a></div>"""

@app.route("/enhance", methods=["POST"])
def enhance():
    if 'u' not in session: return redirect(url_for('login'))
    f = request.files.get("file")
    if f:
        # AI Logic: Grayscale + Auto Crop + Sharpen + Contrast Level
        up = cloudinary.uploader.upload(f, folder="ai_enhanced", 
            transformation=[
                {"effect": "grayscale"},
                {"effect": "improve:outdoor"},
                {"effect": "vibrance:100"},
                {"contrast": "auto"},
                {"sharpen": 300},
                {"crop": "trim", "gravity": "auto"} # Auto Crop White Edges
            ])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
        return redirect(url_for('ai_home'))
    return "Error"

@app.route("/pdf_home")
def pdf_home():
    try: 
        res = cloudinary.api.subfolders("pdf_data")
        folders = res.get("folders", [])
    except: folders = []
    
    f_list = "".join([f'<a href="/view_pdf?name={f["name"]}" class="pdf-item">📂 {f["name"]}</a>' for f in folders])
    return f"{STYLE}<div class='header' style='background:#e74c3c;'><h2>PDF Library</h2><a href='/' style='color:#fff;'>← Back</a></div><div style='padding-top:10px;'>{f_list}</div>"

@app.route("/ai_login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = users_col.find_one({"m": request.form.get("m")})
        if u and u['p'] == hash_pw(request.form.get("pw")):
            session.permanent = True
            session['u'] = str(u['_id']); return redirect(url_for('ai_home'))
        return "Wrong Details!"
    return f'{STYLE}<body style="display:flex; align-items:center; justify-content:center; height:100vh; background:#9b59b6;"><div style="background:#fff; padding:30px; border-radius:10px; width:80%; text-align:center;"><h3>AI Login</h3><form method="POST"><input name="m" placeholder="Mobile Number" style="width:100%; padding:12px; margin-bottom:10px; border:1px solid #ddd;"><br><input name="pw" type="password" placeholder="Password" style="width:100%; padding:12px; margin-bottom:15px; border:1px solid #ddd;"><br><button style="width:100%; padding:15px; background:#9b59b6; color:#fff; border:none; border-radius:5px;">LOGIN</button></form><br><a href="/ai_register">Create New Account</a></div></body>'

@app.route("/ai_register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        m = request.form.get("m"); p = request.form.get("pw")
        if users_col.find_one({"m": m}): return "Number already exists!"
        users_col.insert_one({"m": m, "p": hash_pw(p)})
        return 'Done! <a href="/ai_login">Login Now</a>'
    return f'{STYLE}<body style="display:flex; align-items:center; justify-content:center; height:100vh; background:#28a745;"><div style="background:#fff; padding:30px; border-radius:10px; width:80%; text-align:center;"><h3>Create Account</h3><form method="POST"><input name="m" placeholder="Mobile Number" style="width:100%; padding:12px; margin-bottom:10px;"><br><input name="pw" type="password" placeholder="Set Password" style="width:100%; padding:12px; margin-bottom:15px;"><br><button style="width:100%; padding:15px; background:#28a745; color:#fff; border:none; border-radius:5px;">REGISTER</button></form></div></body>'

@app.route("/modify")
def modify():
    return render_template_string(f'{STYLE}<div class="header"><h2>Confirm Action</h2></div><div style="padding:20px; text-align:center;"><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{{{p}}}}"><input type="hidden" name="task" value="{{{{t}}}}">{{% if t=="rename" %}}<input name="new" placeholder="Enter New Name" style="width:100%; padding:10px; margin-bottom:10px;"><br>{{% endif %}}<input name="pw" type="password" placeholder="Admin Password" style="width:100%; padding:10px; margin-bottom:10px;"><br><button style="width:100%; padding:15px; background:orange; border:none; color:#fff;">EXECUTE</button></form></div>', t=request.args.get("task"), p=request.args.get("pid"))

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PW:
        t, p = request.form.get("task"), request.form.get("pid")
        if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
        elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        return redirect("/")
    return "Invalid Admin Password"

@app.route("/admin_upload")
def admin_upload():
    return f'{STYLE}<div class="header"><h2>Admin Upload</h2></div><div style="padding:20px;"><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><br><br><input name="name" placeholder="File Name"><br><br><input name="pw" type="password" placeholder="Admin Pass"><br><br><button style="width:100%; padding:15px; background:#28a745; color:#fff; border:none;">UPLOAD NOW</button></form></div>'

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PW:
        f = request.files.get("file"); n = request.form.get("name", "vid").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=n)
        return redirect("/")
    return "Auth Error"

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
