import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api, requests
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, send_file
from pymongo import MongoClient
from pytubefix import YouTube
import io

app = Flask(__name__)
app.secret_key = "jiotube_v99_clean_ui"

# --- MASTER CONFIG (RULE 1, 3 & 6) ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = client.get_database('Atif_AI_Database')
    user_col, chat_col = db['users'], db['chat_history']
except:
    user_col = chat_col = None

SECURE_PASS = "809047"
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

STYLE = """<style>
    :root { --jio: #0072ef; --yt: #ff0000; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 80px; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; padding:10px; }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:block; cursor:pointer; }
    .btn-jio { background: var(--jio); } .btn-yt { background: var(--yt); }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
</style>"""

# --- AUTH (RULE 1) - REDIRECTS TO LOGIN IF NO SESSION ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col and user_col.find_one({"p": p, "pw": pw}):
            session['u'] = p
            return redirect("/")
    return f'{STYLE}<div class="card" style="margin-top:50px;"><h3>Secure Login</h3><form method="POST"><input name="p" placeholder="Mobile" required><input name="pw" type="password" placeholder="Pass" required><button class="btn btn-jio" style="width:100%;">ENTER</button></form></div>'

# --- HOME UI (RULE 2) - LOGIN/REGISTER REMOVED FROM HEADER ---
@app.route("/")
def index():
    if 'u' not in session: return redirect("/login")
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids, next_c = res.get("resources", []), res.get("next_cursor")
    except: vids, next_c = [], None
    
    v_html = "".join([f'''<div class="card" style="padding:0; margin-bottom:15px;">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:180px; object-fit:cover;">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px; display:flex; gap:5px;">
            <a href="{v["secure_url"]}" class="btn btn-jio" style="flex:2;">WATCH</a>
            <a href="/rename_page?old={v["public_id"]}" class="btn" style="background:#f39c12; flex:1;">RENAME</a>
            <a href="/delete_confirm?p={v["public_id"]}" class="btn" style="background:#d9534f; flex:1;">DEL</a>
        </div>
    </div>''' for v in vids])
    
    up_panel = f'''<div class="card"><b>Direct Video Downloader</b>
        <form action="/start_engine" method="POST">
            <input name="url" placeholder="YouTube Link" required>
            <input name="file_name" placeholder="Name" required>
            <input name="pass" type="password" placeholder="809047" required>
            <button class="btn btn-yt" style="width:100%;">DOWNLOAD</button>
        </form></div>'''
    
    n_btn = f'<div style="padding:10px;"><a href="/?next={next_c}" class="btn btn-jio">NEXT PAGE</a></div>' if next_c else ""
    
    return f'''{STYLE}
    <div class="header">
        <b>JioTube Master</b>
        <div>
            <a href="/yt_search" class="btn btn-yt" style="display:inline; padding:5px;">YT</a>
            <a href="/pdf_home" class="btn btn-jio" style="display:inline; padding:5px; margin:0 3px;">PDF</a>
            <a href="/ai_chatter" class="btn btn-jio" style="display:inline; padding:5px;">JOYAS</a>
        </div>
    </div>
    {up_panel}{v_html}{n_btn}'''

# --- OTHER ROUTES (STRICT RULES INTACT) ---
@app.route("/start_engine", methods=["POST"])
def start_engine():
    url, name, pw = request.form.get("url"), request.form.get("file_name"), request.form.get("pass")
    if pw == SECURE_PASS:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        buffer = io.BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"{name}.mp4", mimetype='video/mp4')
    return "Wrong Pass"

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="display:flex; justify-content:space-between; align-items:center;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n, curs = request.args.get("name"), request.args.get("next")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=10, next_cursor=curs)
    pgs, next_c = res.get("resources", []), res.get("next_cursor")
    h = "".join([f'''<div class="card" style="padding:0;">
        <img src="https://res.cloudinary.com/dawterffe/image/upload/w_1700,h_1600,c_fill/{p["public_id"]}.jpg" style="width:100%;">
        <div style="padding:10px;"><a href="{p["secure_url"]}" download class="btn btn-jio">DOWNLOAD JPG</a></div>
    </div>''' for p in pgs])
    n_btn = f'<a href="/view_pdf?name={n}&next={next_c}" class="btn btn-jio">NEXT</a>' if next_c else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-jio">BACK</a><b>{n}</b></div>{h}{n_btn}'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if request.method == "POST":
        q = request.form.get("q"); res = model.generate_content(q)
        if chat_col: chat_col.insert_one({"u": session['u'], "q": q, "a": res.text, "t": time.time()})
        return redirect("/ai_chatter")
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1)) if chat_col else []
    c_html = "".join([f'<div class="card"><b>Aap:</b> {c["q"]}<br><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>AI</b></div>{c_html}<form method="POST" style="padding:10px; position:fixed; bottom:0; width:100%; background:#eee; display:flex; gap:5px;"><input name="q" required><button class="btn btn-jio">SEND</button></form>'

# --- RENAME/DELETE (RULE 3) ---
@app.route("/modify")
def modify():
    t, p, pw = request.args.get("t"), request.args.get("p"), request.args.get("pass")
    if pw == SECURE_PASS:
        if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        elif t == "rename": cloudinary.uploader.rename(p, request.args.get("new_name"), resource_type="video")
    return redirect("/")

@app.route("/rename_page")
def rename_page():
    return f'{STYLE}<div class="card"><h3>Rename</h3><form action="/modify"><input type="hidden" name="t" value="rename"><input type="hidden" name="p" value="{request.args.get("old")}"><input name="new_name" placeholder="New Name"><input name="pass" type="password" placeholder="809047"><button class="btn btn-jio" style="width:100%;">SAVE</button></form></div>'

@app.route("/delete_confirm")
def delete_confirm():
    return f'{STYLE}<div class="card"><h3>Delete?</h3><form action="/modify"><input type="hidden" name="t" value="delete"><input type="hidden" name="p" value="{request.args.get("p")}"><input name="pass" type="password" placeholder="809047"><button class="btn" style="background:red; width:100%;">DELETE</button></form></div>'

@app.route("/yt_search", methods=["GET", "POST"])
def yt_search():
    q = request.form.get("yt_query")
    res = f'<div class="card"><a href="https://duckduckgo.com/?q={q}+youtube" target="_blank" class="btn btn-yt">Search on YT</a></div>' if q else ""
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">BACK</a><b>YT</b></div><div style="padding:10px;"><form method="POST"><input name="yt_query" placeholder="Name..."><button class="btn btn-yt" style="width:100%;">FIND</button></form>{res}</div>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
