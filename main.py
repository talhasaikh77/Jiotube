import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jiotube_v71_final_upload"

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
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .upload-panel { background: #fff; padding:15px; margin:10px; border-radius:10px; border: 2px dashed var(--jio); }
    .btn-container { padding: 10px; display: flex; flex-direction: column; gap: 8px; }
    .btn { padding:12px; border-radius:6px; text-decoration:none; color:#fff; font-size:13px; text-align:center; font-weight:bold; border:none; cursor:pointer; display:block; }
    .btn-jio { background: var(--jio); } 
    .btn-save { background: #28a745; width: 100%; font-size: 15px; }
    .btn-sub-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .btn-edit { background: #f39c12; }
    .btn-del { background: #d9534f; }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
    .chat-area { position:fixed; bottom:0; width:100%; display:flex; padding:12px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box; gap:8px; }
</style>"""

@app.route("/")
def index():
    if 'u' not in session: return redirect("/login")
    q = request.args.get("q", "").strip().lower()
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids = [v for v in res.get("resources", []) if q in v["public_id"].lower()]
        nc = res.get("next_cursor")
    except: vids, nc = [], None
    
    v_html = ""
    for v in vids:
        v_html += f'''<div class="card">
            <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:200px; object-fit:cover;">
            <div style="padding:10px;"><b>{v["public_id"]}</b></div>
            <div class="btn-container">
                <a href="{v["secure_url"]}" class="btn btn-jio">WATCH VIDEO</a>
                <a href="{v["secure_url"]}" download class="btn btn-save">DOWNLOAD / SAVE</a>
                <div class="btn-sub-grid">
                    <a href="/modify?t=rename&p={v["public_id"]}" class="btn btn-edit">RENAME</a>
                    <a href="/modify?t=delete&p={v["public_id"]}" class="btn btn-del">DELETE</a>
                </div>
            </div>
        </div>'''
    p_btn = f'<a href="/?next={nc}&q={q}" class="btn btn-jio" style="margin:15px;">LOAD NEXT</a>' if nc else ""
    
    upload_html = f'''<div class="upload-panel">
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit" class="btn btn-jio" style="width:100%; margin-top:10px;">UPLOAD VIDEO</button>
        </form>
    </div>'''
    
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_chatter" class="btn">AI</a></div></div>{upload_html}<form style="padding:10px; display:flex; gap:5px;"><input name="q" placeholder="Search..." value="{q}"><button class="btn btn-jio" style="width:70px;">GO</button></form>{v_html}{p_btn}'

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if file:
        cloudinary.uploader.upload(file, resource_type="video", public_id=file.filename.rsplit('.',1)[0])
    return redirect("/")

@app.route("/modify")
def modify():
    t, p = request.args.get("t"), request.args.get("p")
    if t == "delete":
        cloudinary.uploader.destroy(p, resource_type="video")
    elif t == "rename":
        # Rename logic can be expanded here with a form
        return f'{STYLE}<div class="card" style="padding:20px;"><h3>Rename: {p}</h3><form action="/do_rename" method="POST"><input name="old" type="hidden" value="{p}"><input name="new" placeholder="New Name" required><button class="btn btn-jio">RENAME NOW</button></form></div>'
    return redirect("/")

@app.route("/do_rename", methods=["POST"])
def do_rename():
    old, new = request.form.get("old"), request.form.get("new")
    cloudinary.uploader.rename(old, new, resource_type="video")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        user = user_col.find_one({"p": p, "pw": pw})
        if user: session['u'] = p; return redirect("/")
        return "Ghalat Info! <a href='/login'>Retry</a>"
    return f'{STYLE}<div class="card" style="margin:60px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile" required><input name="pw" type="password" placeholder="Pass" required><button class="btn btn-jio">LOGIN</button></form></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect("/login")
    if request.method == "POST":
        prompt = request.form.get("q")
        if prompt:
            res = model.generate_content(prompt)
            chat_col.insert_one({"u": session['u'], "q": prompt, "a": res.text, "t": time.time()})
        return redirect("/ai_chatter")
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="msg u-msg">{c.get("q","?")}</div><div class="msg ai-msg"><b>Joya:</b> {c.get("a","Thinking...")}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Joya AI</b><a href="/logout" class="btn btn-del">OUT</a></div><div style="display:flex; flex-direction:column; padding-top:10px;">{c_html}</div><form method="POST" class="chat-area"><input name="q" placeholder="Sawal..." required><button class="btn btn-jio" style="width:70px;">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><div class="btn-container"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN BOOK</a></div></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=100)
    pgs = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg","png","jpeg"]], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%;">' for p in pgs])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{n}</b></div>{h}'

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
