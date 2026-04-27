import os
import requests
from flask import Flask, request, render_template_string, redirect, Response
import cloudinary
import cloudinary.api
import cloudinary.uploader
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

# --- Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- GITHUB STYLE PROXY ENGINE ---
def make_proxy_url(url):
    return f"/proxy_go?u={url}"

@app.route('/fb_service')
def fb_service():
    return proxy_logic("https://m.facebook.com/reels/?locale2=en_US")

@app.route('/proxy_go')
def proxy_go():
    target_url = request.args.get('u')
    if not target_url: return redirect('/')
    return proxy_logic(target_url)

def proxy_logic(url):
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"}
    try:
        # Step 1: GitHub Style Request
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')

        # Step 2: GitHub Style Link Correction (No more 404)
        for tag in soup.find_all(['a', 'form', 'link', 'img'], recursive=True):
            attr = 'href' if tag.name in ['a', 'link'] else 'action' if tag.name == 'form' else 'src'
            if tag.has_attr(attr):
                old_url = tag[attr]
                # Absolute URL banana
                full_url = urljoin(url, old_url)
                # Facebook ke links ko hamare proxy mein lapetna
                if "facebook.com" in full_url or full_url.startswith('/'):
                    tag[attr] = make_proxy_url(full_url)

        # Step 3: UI Inject (Home Button)
        nav = '<div style="background:#1877F2;padding:15px;text-align:center;position:fixed;top:0;width:100%;z-index:9999;"><a href="/" style="color:#fff;text-decoration:none;font-weight:bold;font-size:16px;">[ ← WAPAS JIO TUBE ]</a></div><div style="margin-top:60px;"></div>'
        
        return render_template_string(nav + str(soup))
    except Exception as e:
        return f"Proxy Error: {str(e)}"

# --- JIO TUBE UI (Search, Upload, Actions) ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding-bottom: 20px; }
        .header { background: #fff; padding: 15px; text-align: center; border-bottom: 3px solid #0078d7; }
        .nav-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
        .btn { padding: 12px; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; text-align: center; font-size: 14px; }
        .search-form { display: flex; gap: 5px; }
        .search-form input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }
        .v-card { background: #fff; margin: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }
        .v-card img { width: 100%; display: block; }
        .v-info { padding: 15px; }
        .btn-play { display: block; background: #0078d7; color: #fff; text-align: center; padding: 12px; text-decoration: none; font-weight: bold; border-radius: 6px; }
        .v-actions { display: flex; gap: 10px; margin-top: 15px; }
        .btn-s { flex: 1; padding: 10px; color: #fff; text-decoration: none; text-align: center; font-size: 12px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <span style="font-size: 24px; font-weight: bold; color: #0078d7;">JioTube Pro</span>
        <div class="nav-grid">
            <a href="/admin_upload" class="btn" style="background: #28a745;">VIDEO UPLOAD</a>
            <a href="/fb_service" class="btn" style="background: #1877f2;">FACEBOOK REELS</a>
        </div>
        <form action="/" method="GET" class="search-form">
            <input type="text" name="q" placeholder="Video search..." value="{{q}}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:10px 15px; border-radius:6px;">OK</button>
        </form>
    </div>
    {% for v in videos %}
    <div class="v-card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" onerror="this.src='https://via.placeholder.com/350x200?text=JioTube';">
        <div class="v-info">
            <b style="font-size: 16px; color: #333; display: block; margin-bottom: 10px;">{{ v.public_id }}</b>
            <a href="{{ v.secure_url }}" class="btn-play">PLAY VIDEO</a>
            <div class="v-actions">
                <a href="/modify?task=rename&pid={{v.public_id}}" class="btn-s" style="background:#f39c12;">RENAME</a>
                <a href="/modify?task=delete&pid={{v.public_id}}" class="btn-s" style="background:#dc3545;">DELETE</a>
            </div>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

# --- Backend Routes (Search, Up, Modify) ---
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
        return render_template_string('<body style="padding:20px; text-align:center;"><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><input type="text" name="vname" placeholder="Video Name" required><br><br><button type="submit" style="padding:15px; background:green; color:white; border:none; width:100%;">UPLOAD START</button></form></body>')
    return '<form method="POST" style="padding:50px; text-align:center;"><input type="password" name="pw" placeholder="Admin PW"><button type="submit">Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    task = request.args.get('task'); pid = request.args.get('pid')
    return render_template_string('<body style="padding:20px; text-align:center;"><h3>{{task}}: {{pid}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="hidden" name="task" value="{{task}}">{% if task=="rename" %}<input type="text" name="new_name" placeholder="New Name"><br><br>{% endif %}<input type="password" name="pw" placeholder="Admin PW" required><br><br><button type="submit">Confirm Action</button></form></body>', task=task, pid=pid)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new_name').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

