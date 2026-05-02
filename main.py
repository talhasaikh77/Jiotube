import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jiotube_v73_name_fix"

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
    #progress-container { display:none; margin-top:15px; background:#eee; border-radius:10px; overflow:hidden; height:22px; border: 1px solid #ccc; }
    #progress-bar { width:0%; height:100%; background:linear-gradient(to right, #0072ef, #00d4ff); transition: width 0.2s; text-align:center; color:#fff; font-size:12px; line-height:22px; font-weight:bold; }
    .btn { padding:12px; border-radius:6px; text-decoration:none; color:#fff; font-size:13px; text-align:center; font-weight:bold; border:none; cursor:pointer; display:block; }
    .btn-jio { background: var(--jio); width:100%; } 
    .btn-save { background: #28a745; width: 100%; font-size: 15px; margin-top:5px; }
    .btn-sub-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top:5px; }
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
    
    v_html = ""
    for v in vids:
        v_html += f'''<div class="card">
            <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:200px; object-fit:cover;">
            <div style="padding:10px;"><b>{v["public_id"]}</b></div>
            <div style="padding:10px; display:flex; flex-direction:column; gap:5px;">
                <a href="{v["secure_url"]}" class="btn btn-jio">WATCH VIDEO</a>
                <a href="{v["secure_url"]}" download class="btn btn-save">DOWNLOAD / SAVE</a>
                <div class="btn-sub-grid">
                    <a href="/modify?t=rename&p={v["public_id"]}" class="btn" style="background:#f39c12;">RENAME</a>
                    <a href="/modify?t=delete&p={v["public_id"]}" class="btn" style="background:#d9534f;">DELETE</a>
                </div>
            </div>
        </div>'''
    
    upload_html = f'''<div class="upload-panel">
        <form id="upload-form">
            <input type="text" id="v-name" placeholder="Video ka naam likhein..." required>
            <input type="file" id="file-input" required>
            <button type="button" onclick="uploadFile()" class="btn btn-jio" style="margin-top:10px;">UPLOAD VIDEO</button>
        </form>
        <div id="progress-container"><div id="progress-bar">0%</div></div>
    </div>
    <script>
    function uploadFile() {{
        var fileInput = document.getElementById('file-input');
        var nameInput = document.getElementById('v-name');
        if (fileInput.files.length === 0 || !nameInput.value) {{ alert("Naam aur File dono zaroori hain!"); return; }}
        
        var formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("name", nameInput.value);
        
        var xhr = new XMLHttpRequest();
        document.getElementById('progress-container').style.display = 'block';
        
        xhr.upload.addEventListener("progress", function(e) {{
            if (e.lengthComputable) {{
                var percent = Math.round((e.loaded / e.total) * 100);
                document.getElementById('progress-bar').style.width = percent + '%';
                document.getElementById('progress-bar').innerHTML = percent + '%';
            }}
        }}, false);
        
        xhr.onreadystatechange = function() {{
            if (xhr.readyState == 4) {{
                if(xhr.status == 200) {{ window.location.reload(); }}
                else {{ alert("Upload fail! Net check karein."); document.getElementById('progress-container').style.display='none'; }}
            }}
        }};
        
        xhr.open("POST", "/upload", true);
        xhr.send(formData);
    }}
    </script>'''
    
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_chatter" class="btn">AI</a></div></div>{upload_html}<form style="padding:10px; display:flex; gap:5px;"><input name="q" placeholder="Search..." value="{q}"><button class="btn btn-jio" style="width:70px;">GO</button></form>{v_html}'

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    v_name = request.form.get("name")
    if file and v_name:
        cloudinary.uploader.upload(file, resource_type="video", public_id=v_name)
    return "OK"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        user = user_col.find_one({"p": p, "pw": pw})
        if user: session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin:50px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile" required><input name="pw" type="password" placeholder="Pass" required><button class="btn btn-jio">LOGIN</button></form></div>'

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
    c_html = "".join([f'<div class="msg u-msg" style="background:#dcf8c6; margin:10px; padding:10px; border-radius:10px; margin-left:auto; max-width:80%;">{c.get("q")}</div><div class="msg ai-msg" style="background:#fff; margin:10px; padding:10px; border-radius:10px; border:1px solid #ddd; max-width:80%;"><b>Joya:</b> {c.get("a")}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Joya AI</b></div><div style="padding-bottom:100px;">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; gap:5px;"><input name="q" placeholder="Sawal..." required><button class="btn btn-jio" style="width:70px;">SEND</button></form><script>window.scrollTo(0,document.body.scrollHeight);</script>'''

@app.route("/pdf_home")
def pdf_home():
    try: folds = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folds = []
    f_html = "".join([f'<div class="card" style="padding:15px;"><b>{f["name"].upper()}</b><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="margin-top:10px;">OPEN BOOK</a></div>' for f in folds])
    return f'{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Books</b></div>{f_html}'

@app.route("/view_pdf")
def view_pdf():
    n = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{n}/", max_results=100)
    pgs = sorted([p for p in res.get("resources", []) if p["format"] in ["jpg","png","jpeg"]], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%;">' for p in pgs])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn">←</a><b>{n}</b></div>{h}'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
