import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api, requests
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, send_file, Response
from pymongo import MongoClient
from pytubefix import YouTube
from pytubefix.cli import on_progress
import io

app = Flask(__name__)
app.secret_key = "jiotube_v95_direct_download"

# --- MASTER CONFIG (RULE 1, 3 & 6) ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
user_col, chat_col = db['users'], db['chat_history']

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

@app.route("/")
def index():
    if 'u' not in session: return redirect("/login")
    curs, q = request.args.get("next"), request.args.get("q", "").strip()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs, prefix=q if q else None)
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
    
    # Upload Panel with Password (Rule 2)
    up_panel = f'''<div class="card"><b>Direct Phone Downloader</b>
        <form action="/start_engine" method="POST">
            <input name="url" placeholder="Paste YouTube Link" required>
            <input name="file_name" placeholder="Save As (Name)" required>
            <input name="pass" type="password" placeholder="Pass (809047)" required>
            <button class="btn btn-yt" style="width:100%;">DOWNLOAD TO PHONE</button>
        </form></div>'''
    
    n_btn = f'<div style="padding:10px;"><a href="/?next={next_c}&q={q}" class="btn btn-jio">NEXT PAGE</a></div>' if next_c else ""
    return f'{STYLE}<div class="header"><b>JioTube</b><div><a href="/yt_search" class="btn btn-yt">YT</a> <a href="/pdf_home" class="btn btn-jio">PDF</a> <a href="/ai_chatter" class="btn btn-jio">AI</a></div></div>{up_panel}{v_html}{n_btn}'

# --- ENGINE: DIRECT DOWNLOAD TO PHONE (NO CLOUDINARY UPLOAD) ---
@app.route("/start_engine", methods=["POST"])
def start_engine():
    yt_url, name, pw = request.form.get("url"), request.form.get("file_name"), request.form.get("pass")
    if pw == SECURE_PASS:
        try:
            yt = YouTube(yt_url, on_progress_callback=on_progress)
            stream = yt.streams.get_highest_resolution()
            
            # Streaming to browser so it downloads to phone
            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{name}.mp4",
                mimetype='video/mp4'
            )
        except Exception as e:
            return f"{STYLE}<div class='card'>Error: {str(e)}<br><a href='/'>BACK</a></div>"
    return "Invalid Password"

# --- PDF LOGIC (RULE 4: 1700x1600) ---
@app.route("/view_pdf")
def view_pdf():
    n, curs = request.args.get("name"), request.args.get("next")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=10, next_cursor=curs)
    pgs, next_c = res.get("resources", []), res.get("next_cursor")
    h = "".join([f'''<div class="card" style="padding:0;">
        <img src="https://res.cloudinary.com/dawterffe/image/upload/w_1700,h_1600,c_fill/{p["public_id"]}.jpg" style="width:100%;">
        <div style="padding:10px;"><a href="{p["secure_url"]}" download class="btn btn-jio">DOWNLOAD JPG</a></div>
    </div>''' for p in pgs])
    n_btn = f'<a href="/view_pdf?name={n}&next={next_c}" class="btn btn-jio" style="margin:15px;">NEXT</a>' if next_c else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-jio">BACK</a><b>{n}</b></div>{h}{n_btn}'

# --- LOGIN/SIGNUP (MASTER GUARD) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}): session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin-top:50px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio" style="width:100%;">LOGIN</button></form></div>'

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        user_col.insert_one({"p": p, "pw": pw}); return redirect("/login")
    return f'{STYLE}<div class="card" style="margin-top:50px;"><h3>Sign Up</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Set Pass"><button class="btn btn-jio" style="width:100%;">CREATE</button></form></div>'

# Other routes (yt_search, pdf_home, ai_chatter, modify) same as before...
@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="display:flex; justify-content:space-between; align-items:center;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>Books</b></div>{f_html}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
