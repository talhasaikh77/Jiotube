import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
import requests

app = Flask(__name__)
app.secret_key = "jiotube_v79_secure"

# --- API Setup ---
genai.configure(api_key="AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk")
model = genai.GenerativeModel('gemini-1.5-flash')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.get_database('Atif_AI_Database')
user_col = db['users']

# Global Password
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
    q = request.args.get("q", "").strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20)
        vids = [v for v in res.get("resources", []) if q in v["public_id"].lower()]
    except: vids = []
    
    v_html = "".join([f'''<div class="card">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px; display:flex; gap:5px;">
            <a href="{v["secure_url"]}" class="btn btn-jio" style="flex:2;">WATCH</a>
            <a href="/rename_page?old={v["public_id"]}" class="btn" style="background:#f39c12; flex:1;">RENAME</a>
            <a href="/delete_confirm?p={v["public_id"]}" class="btn" style="background:#d9534f; flex:1;">DEL</a>
        </div>
    </div>''' for v in vids])

    return f'''{STYLE}
    <div class="header"><b>JioTube</b><div style="display:flex; gap:4px;"><a href="/yt_search" class="btn btn-yt">YOUTUBE</a><a href="/ai_chatter" class="btn btn-jio">AI</a></div></div>
    {v_html if vids else '<p style="text-align:center; color:gray; padding:20px;">No videos found.</p>'}'''

@app.route("/yt_search", methods=["GET", "POST"])
def yt_search():
    if 'u' not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        if request.form.get("pass") == SECURE_PASS:
            msg = "Searching & Uploading initiated..."
        else:
            msg = "Wrong Password! Action Denied."
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-jio" style="background:rgba(255,255,255,0.2);">BACK</a><b>YouTube Search</b></div>
    <div class="card" style="padding:20px;">
        <form method="POST">
            <input name="v_name" placeholder="Enter video name..." required>
            <input name="pass" type="password" placeholder="Enter Upload Password (809047)" required>
            <button class="btn btn-yt" style="width:100%; margin-top:10px;">SEARCH & UPLOAD</button>
        </form>
        <p style="text-align:center; color:red; font-size:12px;">{msg}</p>
    </div>'''

@app.route("/rename_page")
def rename_page():
    old = request.args.get("old")
    return f'''{STYLE}<div class="card" style="padding:20px;">
        <h3>Secure Rename</h3>
        <form action="/modify" method="GET">
            <input type="hidden" name="t" value="rename">
            <input type="hidden" name="p" value="{old}">
            <input name="new_name" placeholder="New Name" required>
            <input name="pass" type="password" placeholder="Enter Password (809047)" required>
            <button class="btn btn-jio" style="width:100%; margin-top:10px;">CONFIRM RENAME</button>
        </form>
    </div>'''

@app.route("/delete_confirm")
def delete_confirm():
    p = request.args.get("p")
    return f'''{STYLE}<div class="card" style="padding:20px; text-align:center;">
        <h3>Secure Delete</h3>
        <form action="/modify" method="GET">
            <input type="hidden" name="t" value="delete">
            <input type="hidden" name="p" value="{p}">
            <input name="pass" type="password" placeholder="Enter Password (809047)" required>
            <button class="btn" style="background:#d9534f; width:100%; margin-top:10px;">CONFIRM DELETE</button>
        </form>
    </div>'''

@app.route("/modify")
def modify():
    if 'u' not in session: return redirect("/login")
    t, p, pw = request.args.get("t"), request.args.get("p"), request.args.get("pass")
    if pw != SECURE_PASS: return redirect("/")
    try:
        if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
        elif t == "rename":
            new_n = request.args.get("new_name")
            cloudinary.uploader.rename(p, f"{new_n}", resource_type="video")
    except: pass
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}): session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin:60px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio">LOGIN</button></form></div>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
