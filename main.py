import os
import requests
from flask import Flask, request, render_template_string, redirect
import cloudinary
import cloudinary.api
import cloudinary.uploader
from urllib.parse import urljoin

app = Flask(__name__)

# --- Cloudinary Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- GOPROXY STYLE ENGINE ---
@app.route('/fb_service')
def fb_service():
    return proxy_engine("https://mbasic.facebook.com/reels/")

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/')
    return proxy_engine(u)

def proxy_engine(url):
    headers = {"User-Agent": "Mozilla/5.0 (Android 10; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        html = resp.text
        # Goproxy logic: link badalna taaki 404 na aaye
        html = html.replace('href="/', '/proxy_go?u=https://mbasic.facebook.com/')
        html = html.replace('action="/', '/proxy_go?u=https://mbasic.facebook.com/')
        nav = '<div style="background:#000;padding:12px;text-align:center;"><a href="/" style="color:#fff;text-decoration:none;font-weight:bold;">[ ← WAPAS JIOTUBE ]</a></div>'
        return render_template_string(nav + html)
    except:
        return redirect('/')

# --- JIOTUBE PRO HOME UI ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding-bottom:20px; }
        .header { background: #fff; padding: 15px; text-align: center; border-bottom: 3px solid #0078d7; position: sticky; top:0; z-index:10; }
        .nav-buttons { display: flex; gap: 8px; margin-top: 10px; }
        .btn-link { flex: 1; padding: 10px; color: #fff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 13px; text-align: center; }
        .search-form { display: flex; gap: 5px; margin-top: 10px; }
        .search-form input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .video-card { background: #fff; margin: 15px 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow: hidden; }
        .video-card img { width: 100%; display: block; }
        .play-btn { display: block; background: #0078d7; color: #fff; text-align: center; padding: 12px; text-decoration: none; font-weight: bold; }
        .actions { display: flex; gap: 5px; padding: 10px; }
        .btn-small { flex: 1; padding: 8px; color: #fff; text-decoration: none; text-align: center; font-size: 11px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="color:#0078d7; font-size: 22px;">JioTube Pro</b>
        <div class="nav-buttons">
            <a href="/admin_upload" class="btn-link" style="background:#28a745;">UPLOAD</a>
            <a href="/fb_service" class="btn-link" style="background:#1877f2;">FACEBOOK</a>
        </div>
        <form action="/" method="GET" class="search-form">
            <input type="text" name="q" placeholder="Video search..." value="{{q}}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:10px 15px; border-radius:5px;">OK</button>
        </form>
    </div>
    {% for v in videos %}
    <div class="video-card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" onerror="this.src='https://via.placeholder.com/320x180?text=Video';">
        <div style="padding:10px;">
            <b style="display:block; margin-bottom:8px; font-size:14px;">{{ v.public_id }}</b>
            <a href="{{ v.secure_url }}" class="play-btn">PLAY VIDEO</a>
            <div class="actions">
                <a href="/modify?task=rename&pid={{v.public_id}}" class="btn-small" style="background:#f39c12;">RENAME</a>
                <a href="/modify?task=delete&pid={{v.public_id}}" class="btn-small" style="background:#dc3545;">DELETE</a>
            </div>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
    except: videos = []
    return render_template_string(HOME_HTML, videos=videos, q=q)

# --- Admin Functions ---
@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('<form action="/do_up" method="POST" enctype="multipart/form-data">Upload:<input type="file" name="file"><input type="text" name="vname" placeholder="Name"><button>OK</button></form>')
    return '<form method="POST">Password:<input type="password" name="pw"><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    task = request.args.get('task'); pid = request.args.get('pid')
    return render_template_string('<form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="hidden" name="task" value="{{task}}">{% if task=="rename" %}<input type="text" name="new_name">{% endif %}<input type="password" name="pw"><button>Confirm</button></form>', task=task, pid=pid)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new_name').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
