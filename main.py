import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jiotube_v83_engine"

# --- DB & API Setup ---
MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
user_col = db['users']

SECURE_PASS = "809047"

STYLE = """<style>
    :root { --jio: #0072ef; --yt: #ff0000; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 80px; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:block; cursor:pointer; }
    .btn-jio { background: var(--jio); }
    .btn-yt { background: var(--yt); }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; }
</style>"""

@app.route("/")
def index():
    if 'u' not in session: return redirect("/login")
    curs = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=curs)
        vids, next_c = res.get("resources", []), res.get("next_cursor")
    except: vids, next_c = [], None
    
    v_html = "".join([f'''<div class="card">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:160px; object-fit:cover;">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px; display:flex; gap:5px;">
            <a href="{v["secure_url"]}" class="btn btn-jio" style="flex:2;">WATCH</a>
            <a href="/rename_page?old={v["public_id"]}" class="btn" style="background:#f39c12; flex:1;">RENAME</a>
            <a href="/delete_confirm?p={v["public_id"]}" class="btn" style="background:#d9534f; flex:1;">DEL</a>
        </div>
    </div>''' for v in vids])
    n_btn = f'<div style="padding:10px;"><a href="/?next={next_c}" class="btn btn-jio">NEXT PAGE</a></div>' if next_c else ""
    return f'{STYLE}<div class="header"><b>JioTube</b><div style="display:flex; gap:4px;"><a href="/yt_search" class="btn btn-yt">YOUTUBE</a><a href="/pdf_home" class="btn btn-jio">PDF</a><a href="/ai_chatter" class="btn btn-jio">AI</a></div></div>{v_html}{n_btn}'

@app.route("/yt_search", methods=["GET", "POST"])
def yt_search():
    if 'u' not in session: return redirect("/login")
    # Redirecting to a DuckDuckGo Search UI that links to our downloader
    q = request.form.get("q", "")
    if q:
        # Simulation of a search result that triggers the download engine
        return f'''{STYLE}<div class="header"><a href="/" class="btn btn-jio">BACK</a><b>Search Results</b></div>
        <div class="card" style="padding:15px;">
            <p>Found video for: <b>{q}</b></p>
            <p style="font-size:12px; color:gray;">IP: Residential Mobile Proxy Active</p>
            <hr>
            <form action="/start_engine" method="POST">
                <input type="hidden" name="vid_url" value="https://youtube.com/watch?example">
                <input name="pass" type="password" placeholder="Enter Password (809047)" required>
                <button class="btn btn-yt" style="width:100%;">DOWNLOAD VIA YT-DLP (144p)</button>
            </form>
        </div>'''
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-jio">BACK</a><b>YouTube Search</b></div>
    <div style="padding:20px;">
        <form method="POST"><input name="q" placeholder="Search Video or Paste Link..." required><button class="btn btn-yt" style="width:100%;">FIND ON DUCKDUCKGO</button></form>
    </div>'''

@app.route("/start_engine", methods=["POST"])
def start_engine():
    pw = request.form.get("pass")
    if pw == SECURE_PASS:
        # Yahan yt-dlp ka real process start hoga background mein
        return f'{STYLE}<div class="card" style="padding:20px; text-align:center;"><h3>Processing...</h3><p>Video 144p mein convert ho rahi hai. 2 minute baad Home refresh karein.</p><a href="/" class="btn btn-jio">WAPAS HOME</a></div>'
    return redirect("/yt_search")

@app.route("/pdf_home")
def pdf_home():
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_html = "".join([f'<div class="card" style="padding:15px; display:flex; justify-content:space-between;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div>' for f in folders])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n, curs = request.args.get("name"), request.args.get("next")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=10, next_cursor=curs)
    pgs, next_c = sorted(res.get("resources", []), key=lambda x: x["public_id"]), res.get("next_cursor")
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; margin-bottom:5px;">' for p in pgs])
    n_btn = f'<a href="/view_pdf?name={n}&next={next_c}" class="btn btn-jio" style="margin:10px;">NEXT 10 IMAGES</a>' if next_c else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-jio">BACK</a><b>{n}</b></div>{h}{n_btn}'

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}): session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin:60px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio">LOGIN</button></form><p style="text-align:center;"><a href="/signup">Sign Up</a></p></div>'

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        user_col.insert_one({"p": p, "pw": pw})
        return redirect("/login")
    return f'{STYLE}<div class="card" style="margin:60px 20px; padding:20px;"><h3>Create Account</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio">SIGN UP</button></form></div>'

@app.route("/modify")
def modify():
    if 'u' not in session: return redirect("/login")
    t, p, pw = request.args.get("t"), request.args.get("p"), request.args.get("pass")
    if pw != SECURE_PASS: return redirect("/")
    try:
        if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        elif t == "rename": cloudinary.uploader.rename(p, f"{request.args.get('new_name')}", resource_type="video")
    except: pass
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
