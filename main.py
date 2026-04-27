import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for
import cloudinary
import cloudinary.api
import cloudinary.uploader
from bs4 import BeautifulSoup # Ise use karne ke liye 'pip install beautifulsoup4' chahiye hoga

app = Flask(__name__)

# --- Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- SUPER MODIFIED PROXY ENGINE ---
def modify_content(html, base_url):
    # GitHub tools ki tarah ye HTML ko cheer-phaad karke links badal deta hai
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].startswith('/'):
            a['href'] = f"/proxy_go?u=https://m.facebook.com{a['href']}"
        elif 'facebook.com' in a['href']:
            a['href'] = f"/proxy_go?u={a['href']}"
            
    for form in soup.find_all('form', action=True):
        if form['action'].startswith('/'):
            form['action'] = f"/proxy_go?u=https://m.facebook.com{form['action']}"
            
    # Purana kachra saaf karna (Ads aur Scripts)
    for s in soup(['script', 'style', 'iframe']):
        s.decompose()
        
    return str(soup)

@app.route('/fb_service')
def fb_service():
    url = "https://m.facebook.com/reels/?locale2=en_US"
    return proxy_logic(url)

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/')
    return proxy_logic(u)

def proxy_logic(target_url):
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"}
    try:
        r = requests.get(target_url, headers=headers, timeout=15)
        # GitHub style modification
        clean_html = modify_content(r.text, target_url)
        nav = '<div style="background:#000;padding:12px;text-align:center;"><a href="/" style="color:#fff;text-decoration:none;font-weight:bold;">[ HOME ]</a></div>'
        return render_template_string(nav + clean_html)
    except:
        return redirect('/')

# --- HOME UI (All Buttons Safe) ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; }
        .top-bar { background: #fff; padding: 10px; text-align: center; border-bottom: 3px solid #0078d7; position: sticky; top: 0; }
        .nav-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; }
        .btn-main { padding: 12px; color: #fff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 14px; text-align: center; }
        .search-form { display: flex; gap: 5px; margin-top: 10px; }
        .search-form input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .video-card { background: #fff; margin: 15px 10px; border-radius: 8px; box-shadow: 0 2px 5px #ccc; }
        .video-card img { width: 100%; border-radius: 8px 8px 0 0; }
        .v-body { padding: 10px; }
        .play-btn { display: block; background: #0078d7; color: #fff; text-align: center; padding: 12px; text-decoration: none; font-weight: bold; border-radius: 4px; }
        .action-btns { display: flex; gap: 5px; margin-top: 10px; }
        .btn-s { flex: 1; padding: 8px; color: #fff; text-decoration: none; text-align: center; font-size: 11px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="top-bar">
        <b style="color:#0078d7; font-size: 20px;">JioTube Pro</b>
        <div class="nav-grid">
            <a href="/admin_upload" class="btn-main" style="background:#28a745;">UPLOAD</a>
            <a href="/fb_service" class="btn-main" style="background:#1877f2;">FACEBOOK</a>
        </div>
        <form action="/" method="GET" class="search-form">
            <input type="text" name="q" placeholder="Video name..." value="{{q}}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:10px 15px; border-radius:4px;">OK</button>
        </form>
    </div>
    {% for v in videos %}
    <div class="video-card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" onerror="this.src='https://via.placeholder.com/300x150';">
        <div class="v-body">
            <b style="display:block; margin-bottom:10px;">{{ v.public_id }}</b>
            <a href="{{ v.secure_url }}" class="play-btn">PLAY VIDEO</a>
            <div class="action-btns">
                <a href="/modify?task=rename&pid={{v.public_id}}" class="btn-s" style="background:#f39c12;">RENAME</a>
                <a href="/modify?task=delete&pid={{v.public_id}}" class="btn-s" style="background:#dc3545;">DELETE</a>
            </div>
        </div>
    </div>
    {% endfor %}
</body>
</html>
"""

# --- Rest of Backend (Same as before) ---
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
        return render_template_string('<form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="vname"><button type="submit">Up</button></form>')
    return '<form method="POST"><input type="password" name="pw"><button type="submit">Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    task = request.args.get('task'); pid = request.args.get('pid')
    return render_template_string('<form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="hidden" name="task" value="{{task}}">{% if task=="rename" %}<input type="text" name="new_name">{% endif %}<input type="password" name="pw"><button type="submit">Confirm</button></form>', task=task, pid=pid)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new_name').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
