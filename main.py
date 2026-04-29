import os, hashlib, certifi, time
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import cloudinary, cloudinary.uploader, cloudinary.api
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "atif_jio_bharat_pdf_fix"
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

STYLE = """<style>
    body { margin:0; font-family:sans-serif; background:#f4f7f6; }
    .header { background: linear-gradient(135deg, #1e3c72, #2a5298); color:#fff; padding:15px; text-align:center; }
    .card { background:#fff; margin:10px; border-radius:8px; overflow:hidden; box-shadow:0 4px 10px rgba(0,0,0,0.1); }
    .btn { display:inline-block; padding:10px; border-radius:5px; text-decoration:none; font-size:11px; font-weight:bold; color:#fff; margin:2px; text-align:center; }
    .btn-blue { background:#0078d7; } .btn-green { background:#28a745; } .btn-red { background:#e74c3c; }
    .search-box { background:#fff; display:flex; margin:10px; border-radius:20px; border:1px solid #ddd; overflow:hidden; }
    .search-box input { flex:1; border:none; padding:10px; outline:none; }
    .search-box button { background:#333; color:#fff; border:none; padding:0 15px; }
    img { width:100%; display:block; }
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
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="height:150px;object-fit:cover;">
        <div style="padding:10px;"><b>{v["public_id"]}</b><br>
            <a href="{v["secure_url"]}" class="btn btn-blue">PLAY</a>
            <a href="{v["secure_url"]}" download class="btn btn-green">DOWNLOAD</a>
            <a href="/modify?task=delete&pid={v["public_id"]}" class="btn btn-red">DEL</a>
        </div>
    </div>""" for v in videos])
    
    return f"""{STYLE}<div class="header"><h2>JioTube Pro</h2>
    <a href="/pdf_home" class="btn btn-red">PDF SYSTEM</a>
    <a href="/ai_home" class="btn btn-blue" style="background:#9b59b6;">AI MACHINE</a>
    </div>
    <form class="search-box"><input name="q" placeholder="Search..." value="{q}"><button>GO</button></form>
    {v_html} {"<a href='/?next="+new_c+"' class='btn btn-blue' style='width:90%;margin:10px;'>NEXT PAGE</a>" if new_c else ""}"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="image", prefix="pdf_data/", type="upload", max_results=100)
        pdfs = [p for p in res.get("resources", []) if q in p.get("public_id", "").lower()]
    except: pdfs = []
    
    p_html = "".join([f"""<div class="card" style="padding:15px; border-left:5px solid red;">
        <b>{p["public_id"].replace("pdf_data/","")}</b><br><br>
        <a href="/view_pdf_pages?pid={p["public_id"]}" class="btn btn-blue">OPEN PDF (JPG MODE)</a>
        <a href="{p["secure_url"]}" download class="btn btn-green">DL PDF</a>
    </div>""" for p in pdfs])
    
    return f"{STYLE}<div class='header' style='background:red;'><h2>PDF Search</h2><a href='/' style='color:#fff;'>BACK</a></div><form class='search-box'><input name='q' placeholder='Search PDF...' value='{q}'><button>GO</button></form>{p_html}"

@app.route("/view_pdf_pages")
def view_pdf_pages():
    pid = request.args.get("pid")
    pg = int(request.args.get("pg", 1))
    
    # Jio Bharat Trick: PDF to JPG conversion using Cloudinary URL transformation
    # Har page ko alag se image banakar dikhayenge
    pages_html = ""
    for i in range(pg, pg + 10):
        # page_{i} transformation har page ko alag image bana deta hai
        img_url = cloudinary.utils.cloudinary_url(pid, page=i, format="jpg", resource_type="image")[0]
        pages_html += f"""<div class="card">
            <div style="background:#eee;padding:5px;font-size:10px;">PAGE {i}</div>
            <img src="{img_url}">
            <a href="{img_url}" download class="btn btn-green" style="display:block;margin:5px;">DOWNLOAD PAGE {i}</a>
        </div>"""
    
    next_pg = f"<a href='/view_pdf_pages?pid={pid}&pg={pg+10}' class='btn btn-blue' style='width:90%;margin:10px;'>NEXT 10 PAGES >></a>"
    
    return f"{STYLE}<div class='header'><h2>PDF Reader</h2><a href='/pdf_home' style='color:#fff;'>BACK</a></div>{pages_html}{next_pg}"

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('login'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(10))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}"><a href="{i["url"]}" download class="btn btn-green" style="display:block;">DOWNLOAD</a></div>' for i in history])
    return f"{STYLE}<div class='header' style='background:#8e44ad;'><h2>AI Enhancer</h2><a href='/' style='color:#fff;'>BACK</a></div><div class='card' style='padding:20px;'><form action='/enhance' method='POST' enctype='multipart/form-data'><input type='file' name='file'><br><br><button class='btn btn-blue' style='width:100%;border:none;'>ENHANCE</button></form></div>{h_html}"

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
    return f'{STYLE}<div style="padding:50px;text-align:center;"><h3>Login</h3><form method="POST"><input name="m" placeholder="Mobile"><br><input name="pw" type="password" placeholder="Pass"><br><button class="btn btn-blue">LOGIN</button></form></div>'

@app.route("/admin_upload")
def admin_upload():
    return f'{STYLE}<div class="header"><h2>Upload</h2></div><div class="card" style="padding:20px;"><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><br><input name="name" placeholder="Name"><br><input name="pw" placeholder="Admin Pass"><br><button class="btn btn-blue">UPLOAD</button></form></div>'

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PW:
        f = request.files.get("file"); n = request.form.get("name", "file").replace(" ","_")
        folder = "pdf_data" if f.filename.lower().endswith('.pdf') else "video_data"
        if f: cloudinary.uploader.upload(f, resource_type="auto", public_id=f"{folder}/{n}")
    return redirect("/")

@app.route("/modify")
def modify():
    return render_template_string(f'{STYLE}<form action="/confirm" method="POST" style="padding:20px;"><input type="hidden" name="pid" value="{{{{p}}}}"><input type="hidden" name="task" value="{{{{t}}}}">Pass: <input name="pw"><button>OK</button></form>', t=request.args.get("task"), p=request.args.get("pid"))

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PW:
        t, p = request.form.get("task"), request.form.get("pid")
        cloudinary.uploader.destroy(p, resource_type="auto")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
