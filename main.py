import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jiotube_v76_final_fix"

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
    .header { background: var(--jio); padding:15px; display:flex; justify-content:space-between; align-items:center; color:#fff; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; }
    .upload-panel { background: #fff; padding:15px; margin:10px; border-radius:10px; border: 2px dashed var(--jio); }
    #progress-container { display:none; margin-top:10px; background:#eee; border-radius:10px; overflow:hidden; height:20px; }
    #progress-bar { width:0%; height:100%; background:var(--jio); transition: width 0.3s; text-align:center; color:#fff; font-size:11px; line-height:20px; }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:13px; text-align:center; font-weight:bold; border:none; cursor:pointer; display:block; }
    .btn-jio { background: var(--jio); } 
    .btn-save { background: #28a745; width: 100%; font-size: 15px; margin-top:5px; }
    .btn-nav { background: rgba(255,255,255,0.2); padding: 5px 10px; border: 1px solid #fff; font-size:12px; }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
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
    
    v_html = "".join([f'''<div class="card">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:180px; object-fit:cover;" onerror="this.src='https://via.placeholder.com/400x200?text=Video+Loading';">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px;">
            <a href="{v["secure_url"]}" class="btn btn-jio">WATCH VIDEO</a>
            <a href="{v["secure_url"]}" download class="btn btn-save">DOWNLOAD / SAVE</a>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:8px;">
                <a href="/modify?t=rename&p={v["public_id"]}" class="btn" style="background:#f39c12;">RENAME</a>
                <a href="/modify?t=delete&p={v["public_id"]}" class="btn" style="background:#d9534f;">DELETE</a>
            </div>
        </div>
    </div>''' for v in vids])

    n_btn = f'<div style="padding:10px;"><a href="/?next={nc}&q={q}" class="btn btn-jio">NEXT VIDEOS (LOAD MORE)</a></div>' if nc else ""
    
    upload_ui = f'''<div class="upload-panel">
        <input type="text" id="v-name" placeholder="Naam likhein...">
        <input type="file" id="file-input">
        <button type="button" onclick="startStableUpload()" class="btn btn-jio" style="width:100%; margin-top:10px;">UPLOAD VIDEO</button>
        <div id="progress-container"><div id="progress-bar">0%</div></div>
    </div>
    <script>
    async function startStableUpload() {{
        const file = document.getElementById('file-input').files[0];
        const vName = document.getElementById('v-name').value;
        const bar = document.getElementById('progress-bar');
        if(!file || !vName) return alert("Details bhariye!");

        document.getElementById('progress-container').style.display = 'block';
        const CHUNK_SIZE = 5 * 1024 * 1024;
        const total = Math.ceil(file.size / CHUNK_SIZE);

        for(let i=0; i<total; i++) {{
            const chunk = file.slice(i*CHUNK_SIZE, (i+1)*CHUNK_SIZE);
            const fd = new FormData();
            fd.append("file", chunk);
            fd.append("name", vName + (total > 1 ? "_P" + (i+1) : ""));
            await fetch("/upload_part", {{ method: "POST", body: fd }});
            let p = Math.round(((i+1)/total)*100);
            bar.style.width = p + '%'; bar.innerText = p + '%';
        }}
        window.location.reload();
    }}
    </script>'''

    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div style="display:flex; gap:5px;"><a href="/pdf_home" class="btn btn-nav">PDF</a><a href="/ai_chatter" class="btn btn-nav">AI</a></div></div>{upload_ui}<form style="padding:10px; display:flex; gap:5px;"><input name="q" placeholder="Search..." value="{q}"><button class="btn btn-jio" style="width:70px;">GO</button></form>{v_html}{n_btn}'

@app.route("/upload_part", methods=["POST"])
def upload_part():
    file = request.files.get("file"); name = request.form.get("name")
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=name)
    return "OK"

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect("/login")
    if request.method == "POST":
        p = request.form.get("q")
        if p:
            res = model.generate_content(p)
            chat_col.insert_one({"u": session['u'], "q": p, "a": res.text, "t": time.time()})
        return redirect("/ai_chatter")
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div style="background:#dcf8c6; margin:10px; padding:12px; border-radius:12px; margin-left:auto; max-width:80%; font-size:14px;">{c["q"]}</div><div style="background:#fff; margin:10px; padding:12px; border-radius:12px; border:1px solid #ddd; max-width:80%; font-size:14px;"><b>Joya:</b> {c["a"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn btn-nav">HOME</a><b>Joya AI</b></div><div style="padding-bottom:100px;">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; gap:5px; border-top:1px solid #ddd;"><input name="q" placeholder="Sawal..." required><button class="btn btn-jio" style="width:70px;">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/pdf_home")
def pdf_home():
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_html = "".join([f'<div class="card" style="padding:15px; display:flex; justify-content:space-between; align-items:center;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio">OPEN</a></div>' for f in folders])
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-nav">HOME</a><b>Library</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=100)
    pgs = sorted(res.get("resources", []), key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; display:block;">' for p in pgs])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-nav">← BACK</a><b>{n}</b></div>{h}'

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        if user_col.find_one({"p": p, "pw": pw}): session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin:60px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio">LOGIN</button></form></div>'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
