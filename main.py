import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for
import cloudinary
import cloudinary.api
import cloudinary.uploader

app = Flask(__name__)

# Cloudinary Config
cloudinary.config(
  cloud_name = "dawterffe",
  api_key = "258318685843824",
  api_secret = "NxTNXBeLmupMQ0S1FOPU9t6bcjo",
  secure = True
)

ADMIN_PASSWORD = "809047"

# --- INTERNAL PROXY (Language Fix) ---
@app.route('/fb_service')
def fb_service():
    url = "https://mbasic.facebook.com/reels/?locale=en_US"
    headers = {"User-Agent": "Mozilla/5.0 (Jio Phone)", "Accept-Language": "en-US,en;q=0.9"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        content = resp.text.replace('href="https://mbasic.facebook.com', 'href="/proxy_go?u=https://mbasic.facebook.com')
        back_header = '<div style="background:#000;padding:12px;text-align:center;"><a href="/" style="color:#fff;text-decoration:none;font-weight:bold;">[ HOME ]</a></div>'
        return render_template_string(back_header + content)
    except:
        return redirect('/')

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/')
    headers = {"User-Agent": "Mozilla/5.0 (Jio Phone)", "Accept-Language": "en-US,en;q=0.9"}
    resp = requests.get(u, headers=headers)
    return render_template_string(resp.text.replace('href="https://mbasic.facebook.com', 'href="/proxy_go?u=https://mbasic.facebook.com'))

# --- HOME UI ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #f0f0f0; margin: 0; padding: 0; }
        .header { background: #fff; padding: 10px; text-align: center; border-bottom: 2px solid #0078d7; }
        .nav { margin: 10px 0; display: flex; justify-content: center; gap: 10px; }
        .btn-up { background: #28a745; color: #fff; padding: 8px 15px; text-decoration: none; font-weight: bold; border-radius: 4px; }
        .btn-fb { background: #1877f2; color: #fff; padding: 8px 15px; text-decoration: none; font-weight: bold; border-radius: 4px; }
        .search-box { padding: 5px; display: flex; gap: 5px; }
        .search-box input { flex: 1; padding: 8px; border: 1px solid #ccc; }
        .card { background: #fff; margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #ddd; }
        .thumb { width: 100%; height: auto; display: block; background: #000; }
        .v-title { font-size: 14px; font-weight: bold; padding: 5px 0; display: block; }
        .btn-play { background: #0078d7; color: #fff; text-align: center; display: block; padding: 10px; text-decoration: none; font-weight: bold; margin: 5px 0; }
        .actions { display: flex; gap: 5px; }
        .btn-action { flex: 1; padding: 8px; color: #fff; text-decoration: none; text-align: center; font-size: 12px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="font-size: 18px; color: #0078d7;">JioTube Pro</b>
        <div class="nav">
            <a href="/admin_upload" class="btn-up">Upload</a>
            <a href="/fb_service" class="btn-fb">Facebook</a>
        </div>
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Dhoondein..." value="{{q}}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:8px 12px;">Ok</button>
        </form>
    </div>
    {% for v in videos %}
    <div class="card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb">
        <span class="v-title">{{ v.public_id }}</span>
        <a href="{{ v.secure_url }}" class="btn-play">PLAY VIDEO</a>
        <div class="actions">
            <a href="/modify?task=rename&pid={{v.public_id}}" class="btn-action" style="background:#f39c12;">Rename</a>
            <a href="/modify?task=delete&pid={{v.public_id}}" class="btn-action" style="background:#dc3545;">Delete</a>
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
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=50)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
    except: videos = []
    return render_template_string(HOME_HTML, videos=videos, q=q)

@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('''<body style="text-align:center;padding:20px;"><h3>Upload Video</h3><form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file" required><br><br><input type="text" name="vname" placeholder="Name" required><br><br><button type="submit" style="background:green;color:white;padding:10px;">START</button></form></body>''')
    return '<form method="POST" style="text-align:center;padding:50px;"><input type="password" name="pw"><button type="submit">Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    task = request.args.get('task'); pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:20px;"><h3>{{task}}: {{pid}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="hidden" name="task" value="{{task}}">{% if task=='rename' %}<input type="text" name="new_name" placeholder="New Name" required><br><br>{% endif %}<input type="password" name="pw" placeholder="PW" required><br><br><button type="submit">Confirm</button></form></body>''', task=task, pid=pid)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new_name').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
