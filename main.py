import os, time, certifi, cloudinary, cloudinary.uploader, cloudinary.api
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jiotube_v74_chunked"

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
    #progress-container { display:none; margin-top:15px; background:#eee; border-radius:10px; overflow:hidden; height:24px; border: 1px solid #ccc; }
    #progress-bar { width:0%; height:100%; background:linear-gradient(90deg, #0072ef, #00d4ff); transition: width 0.3s; text-align:center; color:#fff; font-size:12px; line-height:24px; font-weight:bold; }
    .btn { padding:12px; border-radius:6px; text-decoration:none; color:#fff; font-size:13px; text-align:center; font-weight:bold; border:none; cursor:pointer; display:block; }
    .btn-jio { background: var(--jio); width:100%; } 
    .btn-save { background: #28a745; width: 100%; font-size: 15px; margin-top:5px; }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
</style>"""

@app.route("/")
def index():
    if 'u' not in session: return redirect("/login")
    q = request.args.get("q", "").strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=30)
        vids = [v for v in res.get("resources", []) if q in v["public_id"].lower()]
    except: vids = []
    
    v_html = "".join([f'''<div class="card">
        <img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%; height:200px; object-fit:cover;">
        <div style="padding:10px;"><b>{v["public_id"]}</b></div>
        <div style="padding:10px; display:flex; flex-direction:column; gap:5px;">
            <a href="{v["secure_url"]}" class="btn btn-jio">WATCH VIDEO</a>
            <a href="{v["secure_url"]}" download class="btn btn-save">DOWNLOAD / SAVE</a>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:5px;">
                <a href="/modify?t=rename&p={v["public_id"]}" class="btn" style="background:#f39c12;">RENAME</a>
                <a href="/modify?t=delete&p={v["public_id"]}" class="btn" style="background:#d9534f;">DELETE</a>
            </div>
        </div>
    </div>''' for v in vids])
    
    upload_ui = f'''<div class="upload-panel">
        <input type="text" id="v-name" placeholder="Video ka naam..." required>
        <input type="file" id="file-input" required>
        <button type="button" onclick="startChunkedUpload()" class="btn btn-jio" style="margin-top:10px;">UPLOAD VIDEO</button>
        <div id="progress-container"><div id="progress-bar">0%</div></div>
        <p id="status-text" style="font-size:11px; color:#666; margin-top:5px; text-align:center;"></p>
    </div>
    <script>
    function startChunkedUpload() {{
        const fileInput = document.getElementById('file-input');
        const nameInput = document.getElementById('v-name');
        const bar = document.getElementById('progress-bar');
        const status = document.getElementById('status-text');
        
        if (fileInput.files.length === 0 || !nameInput.value) {{ alert("Naam aur file chunein!"); return; }}
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("name", nameInput.value);
        
        document.getElementById('progress-container').style.display = 'block';
        status.innerText = "Processing chunks...";

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload", true);

        xhr.upload.onprogress = (e) => {{
            if (e.lengthComputable) {{
                const percent = Math.round((e.loaded / e.total) * 100);
                bar.style.width = percent + '%';
                bar.innerText = percent + '%';
                if(percent > 95) status.innerText = "Finishing... please wait.";
            }}
        }};

        xhr.onload = () => {{
            if (xhr.status === 200) {{ window.location.reload(); }}
            else {{ alert("Error: Badi file hai, net check karein."); }}
        }};
        
        xhr.send(formData);
    }}
    </script>'''
    
    return f'{STYLE}<div class="header"><b>JioTube Pro</b><div><a href="/pdf_home" class="btn">PDF</a> <a href="/ai_chatter" class="btn">AI</a></div></div>{upload_ui}<form style="padding:10px; display:flex; gap:5px;"><input name="q" placeholder="Search..." value="{q}"><button class="btn btn-jio" style="width:70px;">GO</button></form>{v_html}'

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    v_name = request.form.get("name")
    if file and v_name:
        # Use upload_large for files > 20MB
        cloudinary.uploader.upload_large(file, resource_type="video", public_id=v_name, chunk_size=6000000)
    return "OK"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        p, pw = request.form.get("p"), request.form.get("pw")
        user = user_col.find_one({"p": p, "pw": pw})
        if user: session['u'] = p; return redirect("/")
    return f'{STYLE}<div class="card" style="margin:50px 20px; padding:20px;"><h3>Login</h3><form method="POST"><input name="p" placeholder="Mobile"><input name="pw" type="password" placeholder="Pass"><button class="btn btn-jio">LOGIN</button></form></div>'

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
    c_html = "".join([f'<div style="background:#dcf8c6; margin:10px; padding:10px; border-radius:10px; margin-left:auto; max-width:80%;">{c.get("q")}</div><div style="background:#fff; margin:10px; padding:10px; border-radius:10px; border:1px solid #ddd; max-width:80%;"><b>Joya:</b> {c.get("a")}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/" class="btn">HOME</a><b>Joya AI</b></div><div style="padding-bottom:100px;">{c_html}</div><form method="POST" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:#fff; gap:5px;"><input name="q" placeholder="Sawal..." required><button class="btn btn-jio" style="width:70px;">SEND</button></form>'''

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
