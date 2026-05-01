import os, fitz, cloudinary, cloudinary.uploader, cloudinary.api, time, hashlib, certifi, requests
import google.generativeai as genai
from flask import Flask, request, redirect, render_template_string, session, url_for
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "jio_gemini_v38_final"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30 

# Gemini API Configuration
GEMINI_KEY = "AIzaSyDtsD6jEyPXykeTsJvfkB9kk4YEqxf-mFk"
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

MONGO_URI = "mongodb+srv://talhasaikh77_db_user:AtifAI12345@cluster0.udiyfhu.mongodb.net/Atif_AI_Database?retryWrites=true&w=majority"
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.get_database('Atif_AI_Database')
    users_col, ai_col, chat_col = db['users'], db['ai_history'], db['chat_history']
except: print("DB Connection Error")

ADMIN_PASSWORD = "809047"
def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

STYLE = """<style>
    :root { --jio-blue: #0072ef; --bg: #f4f7f6; --card: #ffffff; --text: #333; --border: #ddd; }
    body { margin:0; font-family: sans-serif; background: var(--bg); color: var(--text); }
    .header { background: var(--jio-blue); padding:12px; text-align:center; position:sticky; top:0; z-index:1000; display:flex; justify-content:space-between; align-items:center; color:#fff; }
    .logo { color: #fff; font-weight: bold; font-size: 20px; text-decoration:none; }
    .card { background: var(--card); margin:12px; border-radius:10px; overflow:hidden; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .btn { display:inline-block; padding:10px 14px; border-radius:6px; text-decoration:none; font-size:12px; font-weight:600; color:#fff; border:none; cursor:pointer; }
    .btn-jio { background: var(--jio-blue); } .btn-outline { background:transparent; border:1px solid #fff; color:#fff; }
    .thumb-container { width:100%; height:180px; background:#000; display:flex; align-items:center; justify-content:center; overflow:hidden; }
    .thumb-img { width:100%; height:100%; object-fit: cover; }
    .search-box { background: #fff; display:flex; margin:10px; border-radius:8px; border: 1px solid var(--border); }
    .search-box input { flex:1; border:none; padding:10px; outline:none; }
    .search-box button { background: var(--jio-blue); color:#fff; border:none; padding:0 15px; }
    .chat-box { height:50vh; overflow-y:auto; padding:10px; display:flex; flex-direction:column; gap:10px; background:#fff; border-bottom:1px solid #ddd; }
    .m-u { align-self:flex-end; background:#e1f5fe; padding:10px; border-radius:12px 12px 0 12px; max-width:80%; font-size:13px; border:1px solid #b3e5fc; }
    .m-ai { align-self:flex-start; background:#f5f5f5; padding:10px; border-radius:12px 12px 12px 0; max-width:80%; font-size:13px; border:1px solid #e0e0e0; }
</style>"""

@app.route("/")
@app.route("/video_home")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_html = "".join([f'''<div class="card"><div class="thumb-container"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" class="thumb-img"></div><div style="padding:10px;"><b>{v["public_id"]}</b><div style="display:flex; gap:5px; margin-top:10px;"><a href="{v["secure_url"]}" class="btn btn-jio" style="flex:1;">WATCH</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" class="btn" style="background:#ff9900;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" class="btn" style="background:#e50914;">DEL</a></div></div></div>''' for v in videos])
    nb = f'<a href="/video_home?next={new_c}&q={q}" class="btn btn-jio" style="display:block; margin:10px; text-align:center;">LOAD NEXT</a>' if new_c else ""
    return f'{STYLE}<div class="header"><a href="/" class="logo">JioTube</a><div><a href="/pdf_home" class="btn btn-outline">PDF</a> <a href="/ai_home" class="btn btn-outline">AI</a></div></div><form class="search-box"><input name="q" placeholder="Search videos..." value="{q}"><button>GO</button></form><div style="padding:0 10px;"><a href="/admin_upload" class="btn btn-jio" style="width:100%; text-align:center;">+ UPLOAD VIDEO</a></div>{v_html}{nb}'

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f'''<div class="card"><div style="padding:15px;"><b>{f["name"].split("__")[0].upper()}</b><div style="display:flex; gap:5px; margin-top:10px;"><a href="/view_pdf?name={f["name"]}" class="btn btn-jio" style="flex:2;">OPEN</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" class="btn" style="background:#e50914;">DEL</a></div></div></div>''' for f in folders if q in f["name"].lower()])
    return f'{STYLE}<div class="header"><a href="/video_home" class="btn btn-outline">TUBE</a><b class="logo">JioPDF</b><a href="/ai_home" class="btn btn-outline">AI</a></div><form class="search-box"><input name="q" placeholder="Search books..." value="{q}"><button>FIND</button></form>{f_list}'

@app.route("/ai_home")
def ai_home():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    return f'{STYLE}<div class="header"><a href="/" class="btn btn-outline">HOME</a><b class="logo">JioAI</b><a href="/logout" class="btn" style="background:#e50914;">OUT</a></div><div style="padding:20px; text-align:center;"><a href="/ai_enhance" class="btn btn-jio" style="width:100%; margin-bottom:10px; padding:15px;">PHOTO ENHANCER</a><a href="/ai_chatter" class="btn btn-jio" style="width:100%; background:#28a745; padding:15px;">AI CHATTER (JOYA)</a></div>'

@app.route("/ai_chatter", methods=["GET", "POST"])
def ai_chatter():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    if request.method == "POST":
        msg = request.form.get("msg")
        try:
            # Gemini Real-Time AI Response
            response = model.generate_content(f"User Atif asked: {msg}. Reply in Hindi/Urdu like a helpful assistant named Joya.")
            ai_resp = response.text
        except:
            ai_resp = "Maaf kijiyega Atif bhai, Gemini API mein koi dikkat aa rahi hai. Thodi der baad koshish karein."
        
        chat_col.insert_one({"u": session['u'], "msg": msg, "resp": ai_resp, "t": time.time()})
        return redirect(url_for('ai_chatter'))
    
    chats = list(chat_col.find({"u": session['u']}).sort("t", 1))
    c_html = "".join([f'<div class="m-u">{c["msg"]}</div><div class="m-ai"><b>Joya:</b> {c["resp"]}</div>' for c in chats])
    return f'''{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>AI Chatter</b></div><div class="chat-box" id="cb">{c_html}</div><div style="padding:10px; background:#f4f4f4; position:fixed; bottom:0; width:100%; box-sizing:border-box;"><form method="POST" style="display:flex; gap:5px;"><input name="msg" style="flex:1; padding:10px; border:1px solid #ccc; border-radius:5px;" placeholder="Ask Joya anything..." required><button class="btn btn-jio">SEND</button></form></div><script>var b=document.getElementById("cb"); b.scrollTop=b.scrollHeight;</script>'''

@app.route("/ai_enhance")
def ai_enhance():
    if 'u' not in session: return redirect(url_for('ai_auth'))
    history = list(ai_col.find({"u": session['u']}).sort("t", -1).limit(5))
    h_html = "".join([f'<div class="card"><img src="{i["url"]}" class="thumb-img"><div style="padding:10px;text-align:center;"><a href="{i["url"]}" download class="btn btn-jio">DOWNLOAD</a></div></div>' for i in history])
    return f'{STYLE}<div class="header"><a href="/ai_home" class="btn btn-outline">←</a><b>AI Enhancer</b></div><div class="card" style="padding:20px;text-align:center;"><form action="/do_enhance" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><button class="btn btn-jio" style="width:100%;">ENHANCE HD</button></form></div>{h_html}'

@app.route("/do_enhance", methods=["POST"])
def do_enhance():
    f = request.files.get("file")
    if f:
        up = cloudinary.uploader.upload(f, folder="ai_fixed", transformation=[{"effect": "improve"}])
        ai_col.insert_one({"u": session['u'], "url": up['secure_url'], "t": time.time()})
    return redirect(url_for('ai_enhance'))

@app.route("/ai_auth", methods=["GET", "POST"])
def ai_auth():
    if request.method == "POST":
        m, p, act = request.form.get("m"), request.form.get("pw"), request.form.get("act")
        if act == "reg":
            if not users_col.find_one({"m": m}): users_col.insert_one({"m": m, "p": hash_pw(p)})
            return '<h3>Success! <a href="/ai_auth">Login</a></h3>'
        u = users_col.find_one({"m": m})
        if u and u['p'] == hash_pw(p):
            session.permanent = True; session['u'] = str(u['_id'])
            return redirect(url_for('ai_home'))
    return f'{STYLE}<body style="display:flex;align-items:center;justify-content:center;height:100vh;"><div class="card" style="width:85%;padding:30px;text-align:center;"><h2>JioAI</h2><form method="POST"><input name="m" placeholder="Username" style="width:100%;padding:10px;margin-bottom:10px;"><br><input name="pw" type="password" placeholder="Password" style="width:100%;padding:10px;"><br><br><button name="act" value="log" class="btn btn-jio" style="width:48%;">LOGIN</button> <button name="act" value="reg" class="btn btn-jio" style="width:48%; background:#6c757d;">SIGN UP</button></form></div></body>'

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=50)
    pages = sorted([p for p in res.get("resources", []) if p["format"] != "pdf"], key=lambda x: x["public_id"])
    h = "".join([f'<img src="{p["secure_url"]}" style="width:100%; border-bottom:1px solid #ddd;">' for p in pages])
    return f'{STYLE}<div class="header"><a href="/pdf_home" class="btn btn-outline">←</a><b>BOOK</b></div>{h}'

@app.route("/modify")
def modify():
    t, p, tp = request.args.get("task"), request.args.get("pid"), request.args.get("type")
    return render_template_string("""<div style="background:#f4f7f6;font-family:sans-serif;height:100vh;display:flex;align-items:center;justify-content:center;"><div style="background:#fff;padding:30px;width:80%;border-radius:12px;text-align:center;border:1px solid #ddd"><h3>Confirm {{t|upper}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=='rename' %}<input name="new" placeholder="New Name" required style="width:100%;padding:10px;margin-bottom:10px;"><br>{% endif %}<input name="pw" type="password" placeholder="Admin PIN" required style="width:100%;padding:10px;"><br><br><button style="background:#e50914;color:#fff;width:100%;padding:10px;border:none;border-radius:6px;">CONFIRM</button></form></div></div>""", t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t, p, tp = request.form.get("task"), request.form.get("pid"), request.form.get("type")
        if tp == "video":
            if t == "delete": cloudinary.uploader.destroy(p, resource_type="video", invalidate=True)
            elif t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video", invalidate=True)
            return redirect("/")
        else:
            if t == "delete":
                cloudinary.api.delete_resources_by_prefix(f"pdf_data/{p}/", resource_type="image", invalidate=True)
                cloudinary.api.delete_folder(f"pdf_data/{p}")
            return redirect(url_for('pdf_home'))
    return "Wrong PIN"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
