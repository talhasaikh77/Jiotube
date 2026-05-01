import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jiotube_v60_final_fix"

# --- Gemini Config ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

# --- MongoDB & Cloudinary ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    chat_col = db['chat_history']
except: print("DB Link Fail")

STYLE = """<style>
    :root { --jio: #0072ef; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:10px; border-radius:12px; overflow:hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 10px; }
    .btn { padding:12px; border-radius:8px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; }
    .btn-jio { background: var(--jio); } .btn-del { background: #e63946; } .btn-edit { background: #fca311; } .btn-down { background: #2a9d8f; }
    .search-bar { padding:10px; display:flex; gap:8px; background:#fff; }
    .search-bar input { flex:1; padding:12px; border:1px solid #ccc; border-radius:10px; outline:none; }
    .msg { position:relative; margin:10px; padding:15px; border-radius:15px; max-width:85%; font-size:14px; line-height:1.5; }
    .u-msg { align-self: flex-end; background: #dcf8c6; margin-left: auto; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    .ai-msg { align-self: flex-start; background: #fff; border: 1px solid #eee; }
    .del-x { position:absolute; top:-5px; right:-5px; background:red; color:#fff; border-radius:50%; width:22px; height:22px; text-align:center; line-height:22px; font-size:12px; text-decoration:none; font-weight:bold; }
    .chat-input-area { position:fixed; bottom:0; width:100%; display:flex; padding:12px; background:#fff; border-top:1px solid #ddd; box-sizing:border-box; gap:8px; }
</style>"""

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids = [v for v in res.get("resources", []) if q.lower() in v["public_id"].lower()]
        new_curs = res.get("next_cursor")
    except: vids, new_curs = [], None
    v_html = "".join([f'''<div class="card"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:190px; object-fit:cover;"><div style="padding:12px;"><b>{v["public_id"]}</b></div><div class="btn-grid"><a href="{v["secure_url"]}" class="btn btn-jio">WATCH</a><a href="/modify?t=rename&p={v["public_id"]}" class="btn btn-edit">RENAME</a><a href="/modify?t=delete&p={v["public_id"]}" class="btn btn-del">DELETE</a><a href="{v["secure_url"]}" download class="btn btn-down">DOWNLOAD</a></div></div>''' for v in vids])
    p_btn = f'<a href="/?next={new_curs}&q={q}" style="display:block; text-align:center; padding:15px; background:#fff; margin:10px; border-radius:10px; text-decoration:none; color:var(--jio); font-weight:bold; border:1px solid var(--jio);">LOAD NEXT 10 VIDEOS</a>' if new_curs else ""
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn" style="border:1px solid #fff">PDF</a> <a href="/ai_auth" class="btn" style="border:1px solid #fff">AI</a></div></div><form class="search-bar"><input name="q" placeholder="Search anything..." value="{q}"><button class="btn btn-jio">GO</button></form>{v_html}{p_btn}'

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if 'u' in session: return redirect(url_for('ai_chatter'))
    if request.method == "POST":
        session['u'] = request.form.get("name")
        return redirect(url_for('ai_chatter'))
    return f'{STYLE}<div style="padding:60px 20px; text-align:center;"><div class="card" style="padding:30px;"><h2>JioAI Register</h2><form method="POST"><input name="name" placeholder="Enter Your Name" required style="width:100%; padding:15px; border-radius:10px; border:1px solid #ccc; margin-bottom:15px;"><button class="btn btn-jio" style="width:100%;">START CHATTING</button></form></div></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        prompt = request.form.get("q")
        try:
            # Browser stays on loading until Gemini responds
            response = model.generate_content(prompt)
            chat_col.insert_one({"u": session['u'], "q": prompt, "a": response.text, "t": time.time()})
        except: pass
        return redirect(url_for('ai_chatter'))
    
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="msg u-msg"><a href="/del_chat?id={c["_id"]}" class="del-x">x</a>{c["q"]}</div><div class="msg ai-msg"><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Chat with Joya</b><a href="/logout" class="btn btn-del" style="font-size:10px;">OUT</a></div><div style="display:flex; flex-direction:column; padding-bottom:100px;">{c_html}</div><form method="POST" class="chat-input-area"><input name="q" style="flex:1; padding:12px; border-radius:10px; border:1px solid #ccc;" placeholder="Type here..." required><button class="btn btn-jio">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/del_chat")
def del_chat():
    chat_col.delete_one({"_id": ObjectId(request.args.get("id"))})
    return redirect(url_for('ai_chatter'))

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><div class="btn-grid"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN BOOK</a><a href="/modify?t=delete&p={f["name"]}&tp=pdf" class="btn btn-del">DELETE</a></div></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>JioBooks</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=100)
    pages = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg","png","jpeg"]], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; margin-bottom:2px;">' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{name}</b></div>{h if pages else "<h3>Book is Empty!</h3>"}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
