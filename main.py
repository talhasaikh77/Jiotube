import os, time, hashlib, certifi, requests, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v58_ultra_fast"

# --- Gemini Configuration ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DB & Cloud ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    chat_col = db['chat_history']
    ai_col = db['ai_fixed']
except: print("DB Error")

STYLE = """<style>
    :root { --jio: #0072ef; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; padding: 10px; }
    .btn { padding:10px; border-radius:5px; text-decoration:none; color:#fff; font-size:11px; text-align:center; font-weight:bold; border:none; cursor:pointer; }
    .btn-jio { background: var(--jio); } .btn-del { background: #d00; } .btn-edit { background: #f80; } .btn-down { background: #28a745; }
    .thumb { width:100%; height:180px; object-fit: cover; }
    .search-box { padding:10px; display:flex; gap:5px; background:#fff; }
    .search-box input { flex:1; padding:10px; border:1px solid #ccc; border-radius:5px; }
    .msg-box { position:relative; margin:10px; padding:12px; border-radius:10px; max-width:85%; font-size:14px; }
    .u-msg { align-self: flex-end; background: #dcf8c6; margin-left: auto; }
    .ai-msg { align-self: flex-start; background: #fff; border: 1px solid #ddd; }
    .del-icon { position:absolute; top:-5px; right:-5px; background:red; color:#fff; border-radius:50%; width:20px; height:20px; text-align:center; cursor:pointer; text-decoration:none; line-height:20px; font-size:12px; }
</style>"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids = res.get("resources", [])
        new_curs = res.get("next_cursor")
    except: vids, new_curs = [], None
    
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb"><div style="padding:10px;"><b>{v["public_id"]}</b></div><div class="btn-grid"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}" class="btn btn-del">DELETE</a><a href="{v["secure_url"]}" download class="btn btn-down">DOWNLOAD</a></div></div>''' for v in vids if q.lower() in v["public_id"].lower()])
    
    next_html = f'<a href="/?next={new_curs}&q={q}" style="display:block; text-align:center; padding:15px; background:#fff; margin:10px; border-radius:10px; text-decoration:none; color:var(--jio); font-weight:bold;">NEXT 10 VIDEOS →</a>' if new_curs else ""
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_login" class="btn">AI</a></div></div><form class="search-box"><input name="q" placeholder="Advanced Search..." value="{q}"><button class="btn btn-jio">GO</button></form>{v_html}{next_html}'

@app.route("/ai_login", methods=["GET", "POST"])
def ai_login():
    if request.method == "POST":
        session['user'] = request.form.get("u")
        return redirect("/ai_chatter")
    return f'{STYLE}<div style="padding:50px; text-align:center;"><h3>AI Registration</h3><form method="POST"><input name="u" placeholder="Your Name" required style="width:80%; padding:10px;"><br><br><button class="btn btn-jio" style="width:80%;">LOGIN</button></form></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'user' not in session: return redirect("/ai_login")
    if request.method == "POST":
        q = request.form.get("q")
        try:
            resp = model.generate_content(q)
            chat_col.insert_one({"u": session['user'], "q": q, "a": resp.text, "t": time.time()})
        except: pass
        return redirect("/ai_chatter")
    
    chats = list(chat_col.find({"u": session['user']}).sort("t", 1))
    c_html = "".join([f'<div class="msg-box u-msg"><a href="/del_chat?id={c["_id"]}" class="del-icon">x</a>{c["q"]}</div><div class="msg-box ai-msg"><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">←</a><b>Joya AI</b><a href="/ai_enhance" class="btn">ENHANCE</a></div><div style="display:flex; flex-direction:column; padding-bottom:80px;">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box;"><input name="q" style="flex:1; padding:12px; border-radius:5px; border:1px solid #ccc;" placeholder="Ask me..." required><button class="btn btn-jio">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/ai_enhance", methods=["GET", "POST"])
def ai_enhance():
    if request.method == "POST":
        f = request.files.get("file")
        if f:
            up = cloudinary.uploader.upload(f, folder="ai_fixed", transformation=[{"effect": "improve"}])
            ai_col.insert_one({"u": session.get('user','guest'), "url": up['secure_url'], "t": time.time()})
        return redirect("/ai_enhance")
    imgs = list(ai_col.find().sort("t", -1).limit(5))
    i_html = "".join([f'<div class="card"><img src="{i["url"]}" class="thumb"><a href="{i["url"]}" download class="btn btn-down" style="display:block; margin:10px;">DOWNLOAD FIXED PHOTO</a></div>' for i in imgs])
    return f'{STYLE}<div class="header"><a href="/ai_chatter" class="btn">←</a><b>Enhancer</b></div><div class="card" style="padding:20px; text-align:center;"><form method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><button class="btn btn-jio">ENHANCE PHOTO</button></form></div>{i_html}'

@app.route("/del_chat")
def del_chat():
    chat_col.delete_one({"_id": ObjectId(request.args.get("id"))})
    return redirect("/ai_chatter")

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><div class="btn-grid"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a><a href="/modify?t=delete&p={f["name"]}&tp=pdf" class="btn btn-del">DELETE</a></div></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">←</a><b>JioBooks</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=100)
    pages = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg","png","jpeg"]], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; margin-bottom:2px;">' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{name}</b></div>{h if pages else "<h3>Folder Empty or No JPGs!</h3>"}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
