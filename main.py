import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jiotube_v85_final_pro"

# --- API & DB SETUP ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
user_col = db['users']
chat_col = db['chat_history']

SECURE_PASS = "809047"

STYLE = """<style>
    :root { --jio: #0072ef; --yt: #ff0000; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 80px; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:block; cursor:pointer; }
    .btn-jio { background: var(--jio); }
    .btn-yt { background: var(--yt); }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
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
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:180px; object-fit:cover;">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px; display:flex; gap:5px;">
            <a href="{v["secure_url"]}" class="btn btn-jio" style="flex:2;">WATCH</a>
            <a href="/rename_page?old={v["public_id"]}" class="btn" style="background:#f39c12; flex:1;">RENAME</a>
            <a href="/delete_confirm?p={v["public_id"]}" class="btn" style="background:#d9534f; flex:1;">DEL</a>
        </div>
    </div>''' for v in vids])
    n_btn = f'<div style="padding:10px;"><a href="/?next={next_c}" class="btn btn-jio">NEXT PAGE (10+)</a></div>' if next_c else ""
    return f'{STYLE}<div class="header"><b>JioTube</b><div style="display:flex; gap:4px;"><a href="/yt_search" class="btn btn-yt">YOUTUBE</a><a href="/pdf_home" class="btn btn-jio">PDF</a><a href="/ai_chatter" class="btn btn-jio">AI</a></div></div>{v_html}{n_btn}'

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}): session['u'] = p; return redirect("/")
        else: msg = "Ghalat details!"
    return f'''{STYLE}<div class="card" style="margin:50px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile No" required><input name="pw" type="password" placeholder="Password" required><button class="btn btn-jio" style="width:100%; margin-top:10px;">LOGIN</button></form><p style="color:red;">{msg}</p><p>Naya account? <a href="/signup">Sign Up</a></p></div>'''

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        user_col.insert_one({"p": p, "pw": pw})
        return redirect("/login")
    return f'{STYLE}<div class="card" style="margin:50px 20px; padding:20px;"><h3>Sign Up</h3><form method="POST"><input name="p" placeholder="Mobile No" required><input name="pw" type="password" placeholder="Set Password" required><button class="btn btn-jio" style="width:100%; margin-top:10px;">CREATE</button></form></div>'

@app.route("/yt_search")
def yt_search():
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-jio">BACK</a><b>YouTube Search</b></div>
    <div style="padding:10px;">
        <div class="card" style="padding:15px; text-align:center;">
            <p>DuckDuckGo Engine for Videos</p>
            <a href="https://duckduckgo.com/?q=youtube+videos&iar=videos" target="_blank" class="btn btn-yt">OPEN DUCKDUCKGO SEARCH</a>
            <hr><p>Paste link below to Download</p>
            <form action="/start_engine" method="POST">
                <input name="url" placeholder="Paste Video Link" required>
                <input name="pass" type="password" placeholder="809047" required>
                <button class="btn btn-yt" style="width:100%;">DOWNLOAD 144P</button>
            </form>
        </div>
    </div>'''

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px; display:flex; justify-content:space-between;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n, curs = request.args.get("name"), request.args.get("next")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=10, next_cursor=curs)
    pgs, next_c = res.get("resources", []), res.get("next_cursor")
    h = "".join([f'<div class="card"><img src="{p["secure_url"]}" style="width:100%;"><a href="{p["secure_url"]}" download class="btn btn-jio" style="margin:5px;">DOWNLOAD JPG</a></div>' for p in pgs])
    n_btn = f'<a href="/view_pdf?name={n}&next={next_c}" class="btn btn-jio" style="margin:10px;">NEXT 10 PHOTOS</a>' if next_c else ""
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-jio">BACK</a><b>{n}</b></div>{h}{n_btn}'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if request.method == "POST":
        q = request.form.get("q")
        res = model.generate_content(q)
        chat_col.insert_one({"u": session['u'], "q": q, "a": res.text, "t": time.time()})
        return redirect("/ai_chatter")
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div style="background:#fff; margin:10px; padding:10px; border-radius:10px;"><b>Aap:</b> {c["q"]}<br><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>AI Chatter</b></div>{c_html}<form method="POST" style="padding:10px; position:fixed; bottom:0; width:100%; background:#eee; display:flex; gap:5px;"><input name="q" required><button class="btn btn-jio">SEND</button></form>'

@app.route("/delete_confirm")
def delete_confirm():
    p = request.args.get("p")
    return f'{STYLE}<div class="card" style="padding:20px;"><h3>Delete?</h3><form action="/modify"><input type="hidden" name="t" value="delete"><input type="hidden" name="p" value="{p}"><input name="pass" type="password" placeholder="809047" required><button class="btn" style="background:red; width:100%;">CONFIRM DELETE</button></form></div>'

@app.route("/rename_page")
def rename_page():
    old = request.args.get("old")
    return f'{STYLE}<div class="card" style="padding:20px;"><h3>Rename</h3><form action="/modify"><input type="hidden" name="t" value="rename"><input type="hidden" name="p" value="{old}"><input name="new_name" placeholder="New Name" required><input name="pass" type="password" placeholder="809047" required><button class="btn btn-jio" style="width:100%;">SAVE RENAME</button></form></div>'

@app.route("/modify")
def modify():
    t, p, pw = request.args.get("t"), request.args.get("p"), request.args.get("pass")
    if pw == SECURE_PASS:
        if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        elif t == "rename": cloudinary.uploader.rename(p, request.args.get("new_name"), resource_type="video")
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
