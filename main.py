import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for, Response
import cloudinary
import cloudinary.api
import cloudinary.uploader
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# --- Cloudinary Config ---
cloudinary.config(
  cloud_name = "dawterffe",
  api_key = "258318685843824",
  api_secret = "NxTNXBeLmupMQ0S1FOPU9t6bcjo",
  secure = True
)

ADMIN_PASSWORD = "809047"
BASE_FB = "https://m.facebook.com"

# --- SMART PROXY LOGIC (GitHub Se Behtar) ---
@app.route('/fb_service')
def fb_service():
    # Force English and Modern Mobile View
    target = f"{BASE_FB}/reels/?locale2=en_US"
    return proxy_engine(target)

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/')
    return proxy_engine(u)

def proxy_engine(target_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        resp = requests.get(target_url, headers=headers, timeout=15)
        # Magic: Saare links ko hamare proxy route mein badalna
        content = resp.text
        content = content.replace('href="/', f'href="/proxy_go?u={BASE_FB}/')
        content = content.replace('action="/', f'action="/proxy_go?u={BASE_FB}/')
        content = content.replace('href="https://m.facebook.com', 'href="/proxy_go?u=https://m.facebook.com')
        
        # Back Button Inject Karna
        ui_fix = '<div style="background:#000;padding:10px;text-align:center;"><a href="/" style="color:#fff;text-decoration:none;font-weight:bold;">[ ← WAPAS HOME ]</a></div>'
        return render_template_string(ui_fix + content)
    except:
        return redirect('/')

# --- MAIN UI (SAARE FEATURES) ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #eee; margin: 0; padding: 0; }
        .header { background: #fff; padding: 10px; text-align: center; border-bottom: 3px solid #0078d7; position: sticky; top: 0; z-index: 100; }
        .nav { margin: 10px 0; display: flex; justify-content: center; gap: 10px; }
        .btn-up { background: #28a745; color: #fff; padding: 10px 15px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 13px; }
        .btn-fb { background: #1877f2; color: #fff; padding: 10px 15px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 13px; }
        .search-box { padding: 5px; display: flex; gap: 5px; }
        .search-box input { flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .card { background: #fff; margin: 10px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .thumb { width: 100%; height: auto; display: block; background: #000; }
        .v-info { padding: 10px; }
        .v-title { font-size: 15px; font-weight: bold; color: #333; margin-bottom: 10px; display: block; }
        .btn-play { background: #0078d7; color: #fff; text-align: center; display: block; padding: 12px; text-decoration: none; font-weight: bold; border-radius: 4px; }
        .actions { display: flex; gap: 5px; margin-top: 8px; }
        .btn-act { flex: 1; padding: 8px; color: #fff; text-decoration: none; text-align: center; font-size: 12px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <b style="font-size: 22px; color: #0078d7;">JioTube Pro</b>
        <div class="nav">
            <a href="/admin_upload" class="btn-up">UPLOAD</a>
            <a href="/fb_service" class="btn-fb">FACEBOOK</a>
        </div>
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Video search karein..." value="{{q}}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:10px 15px; border-radius:4px;">OK</button>
        </form>
    </div>
    {% for v in videos %}
    <div class="card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/320x180?text=JioTube';">
        <div class="v-info">
            <span class="v-title">{{ v.public_id }}</span>
            <a href="{{ v.secure_url }}" class="btn-play">CHALAYEIN (PLAY)</a>
            <div class="actions">
                <a href="/modify?task=rename&pid={{v.public_id}}" class="btn-act" style="background:#f39c12;">RENAME</a>
                <a href="/modify?task=delete&pid={{v.public_id}}" class="btn-act" style="background:#dc3545;">DELETE</a>
            </div>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

# --- BACKEND ROUTES ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
    except: videos = []
    return render_template_string(HOME_HTML, videos=videos, q=q)

@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('''<body style="text-align:center;padding:20px;background:#eee;"><h3>Upload</h3><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><input type="text" name="vname" placeholder="Video Name" required><br><br><button type="submit" style="background:green;color:white;padding:15px;width:100%;">START UPLOAD</button></form></body>''')
    return '<form method="POST" style="text-align:center;padding:50px;"><input type="password" name="pw" placeholder="Password"><button type="submit">Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    task = request.args.get('task'); pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:20px;"><h3>{{task}}: {{pid}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="hidden" name="task" value="{{task}}">{% if task=='rename' %}<input type="text" name="new_name" placeholder="New Name" required><br><br>{% endif %}<input type="password" name="pw" placeholder="Admin PW" required><br><br><button type="submit" style="padding:10px;">CONFIRM</button></form></body>''', task=task, pid=pid)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new_name').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
