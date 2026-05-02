import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "jiotube_v84_fix"

# --- Cloudinary & DB Setup ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
SECURE_PASS = "809047"

STYLE = """<style>
    :root { --jio: #0072ef; --yt: #ff0000; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 80px; }
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; padding:15px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:block; cursor:pointer; }
    .btn-jio { background: var(--jio); }
    .btn-yt { background: var(--yt); }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; }
    iframe { width:100%; height:400px; border:none; border-radius:10px; }
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
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:160px; object-fit:cover; border-radius:8px;">
        <div style="margin-top:10px;"><b>{v["public_id"]}</b></div>
        <div style="display:flex; gap:5px; margin-top:10px;">
            <a href="{v["secure_url"]}" class="btn btn-jio" style="flex:2;">WATCH</a>
            <a href="/rename_page?old={v["public_id"]}" class="btn" style="background:#f39c12; flex:1;">RENAME</a>
            <a href="/delete_confirm?p={v["public_id"]}" class="btn" style="background:#d9534f; flex:1;">DEL</a>
        </div>
    </div>''' for v in vids])
    n_btn = f'<div style="padding:10px;"><a href="/?next={next_c}" class="btn btn-jio">NEXT PAGE</a></div>' if next_c else ""
    return f'{STYLE}<div class="header"><b>JioTube</b><div style="display:flex; gap:4px;"><a href="/yt_search" class="btn btn-yt">YOUTUBE</a><a href="/pdf_home" class="btn btn-jio">PDF</a></div></div>{v_html}{n_btn}'

# --- FIXED DELETE & RENAME ROUTES ---
@app.route("/delete_confirm")
def delete_confirm():
    p = request.args.get("p")
    return f'{STYLE}<div class="card"><h3>Delete Video?</h3><p>{p}</p><form action="/modify"><input type="hidden" name="t" value="delete"><input type="hidden" name="p" value="{p}"><input name="pass" type="password" placeholder="Password" required><button class="btn btn-yt" style="width:100%;">CONFIRM DELETE</button></form></div>'

@app.route("/rename_page")
def rename_page():
    old = request.args.get("old")
    return f'{STYLE}<div class="card"><h3>Rename Video</h3><form action="/modify"><input type="hidden" name="t" value="rename"><input type="hidden" name="p" value="{old}"><input name="new_name" placeholder="New Name" required><input name="pass" type="password" placeholder="Password" required><button class="btn btn-jio" style="width:100%;">SAVE RENAME</button></form></div>'

@app.route("/modify")
def modify():
    t, p, pw = request.args.get("t"), request.args.get("p"), request.args.get("pass")
    if pw != SECURE_PASS: return "Wrong Password! <a href='/'>Go Back</a>"
    if t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
    elif t == "rename": cloudinary.uploader.rename(p, request.args.get("new_name"), resource_type="video")
    return redirect("/")

# --- YOUTUBE DUCKDUCKGO FIX ---
@app.route("/yt_search", methods=["GET", "POST"])
def yt_search():
    q = request.form.get("q", "")
    search_frame = ""
    if q:
        search_frame = f'<h3>Results for: {q}</h3><iframe src="https://duckduckgo.com/?q={q}+youtube&iar=videos"></iframe>'
    
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-jio">BACK</a><b>YT Downloader</b></div>
    <div style="padding:10px;">
        <form method="POST"><input name="q" placeholder="Search Video..."><button class="btn btn-yt" style="width:100%;">SEARCH ENGINE</button></form>
        {search_frame}
        <hr>
        <div class="card">
            <h4>Real Downloader Engine</h4>
            <form action="/start_engine" method="POST">
                <input name="vid_url" placeholder="Paste YouTube Link Here..." required>
                <button class="btn btn-yt" style="width:100%;">DOWNLOAD 144P</button>
            </form>
        </div>
    </div>'''

@app.route("/pdf_home")
def pdf_home():
    # PDF Logic (Same as V82/83)
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-jio">HOME</a><b>Books</b></div><p style="padding:20px;">PDF Library Active.</p>'

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST": session['u'] = "user"; return redirect("/")
    return f'{STYLE}<form method="POST" style="padding:50px;"><input name="p" placeholder="Mobile"><button class="btn btn-jio">LOGIN</button></form>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
