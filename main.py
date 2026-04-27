import os
import requests
from flask import Flask, request, render_template_string, redirect
import cloudinary
import cloudinary.api
import cloudinary.uploader
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# --- Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- PROFESSIONAL PROXY ENGINE (FIXED) ---
@app.route('/proxy_page')
def proxy_page():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pro Proxy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #1a1a1a; color: #fff; text-align: center; padding: 20px; }
            .box { background: #333; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            input { width: 85%; padding: 12px; border-radius: 5px; border: none; margin-bottom: 10px; color:#000; }
            button { background: #e74c3c; color: #fff; padding: 10px 20px; border: none; border-radius: 5px; font-weight: bold; width: 90%; }
            .links { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }
            .l-btn { background: #444; padding: 15px; color: #fff; text-decoration: none; border-radius: 5px; font-size: 14px; border: 1px solid #555; font-weight:bold; }
            .home-btn { display: block; margin-top: 30px; color: #0078d7; text-decoration: none; font-weight:bold; }
        </style>
    </head>
    <body>
        <h2>Proxy Browser</h2>
        <div class="box">
            <form action="/proxy_go" method="GET">
                <input type="text" name="u" placeholder="https://google.com" required><br>
                <button type="submit">KHOLEN (OPEN)</button>
            </form>
        </div>
        <p>Direct Access:</p>
        <div class="links">
            <a href="/proxy_go?u=https://mbasic.facebook.com" class="l-btn" style="border-left: 5px solid #1877f2;">FACEBOOK</a>
            <a href="/proxy_go?u=https://www.google.com" class="l-btn" style="border-left: 5px solid #ea4335;">GOOGLE</a>
            <a href="/proxy_go?u=https://m.youtube.com" class="l-btn" style="border-left: 5px solid #ff0000;">YOUTUBE</a>
            <a href="/proxy_go?u=https://www.bing.com" class="l-btn" style="border-left: 5px solid #00a4ef;">BING</a>
        </div>
        <a href="/" class="home-btn">← WAPAS JIOTUBE HOME</a>
    </body>
    </html>
    """)

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/proxy_page')
    if not u.startswith('http'): u = 'https://' + u
    return proxy_engine(u)

def proxy_engine(url):
    headers = {"User-Agent": "Mozilla/5.0 (Android 10; Mobile; rv:122.0) Gecko/122.0 Firefox/122.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        content = resp.text
        
        # Link Rewriting Logic: Taaki links 404 na dein
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        # Ye line har link ko hamare proxy route pe bhejegi
        content = content.replace('href="/', f'href="/proxy_go?u={base_url}/')
        content = content.replace('action="/', f'action="/proxy_go?u={base_url}/')
        
        # Proxy Navigation Bar
        nav = f'''<div style="background:#000;padding:10px;text-align:center;position:sticky;top:0;z-index:999;">
                    <a href="/proxy_page" style="color:#fff;text-decoration:none;font-weight:bold;">[ ← PROXY MENU ]</a>
                    <span style="color:#aaa;margin-left:10px;font-size:10px;">{url[:20]}...</span>
                  </div>'''
        return render_template_string(nav + content)
    except:
        return redirect('/proxy_page')

# --- JIOTUBE HOME ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: sans-serif; background: #eee; margin: 0; }
        .header { background: #fff; padding: 10px; text-align: center; border-bottom: 3px solid #0078d7; }
        .nav { display: flex; gap: 5px; margin: 10px 0; }
        .btn { flex: 1; padding: 12px; color: #fff; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center; font-size: 14px; }
        .card { background: #fff; margin: 10px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .card img { width: 100%; display: block; }
        .play { display: block; background: #0078d7; color: #fff; text-align: center; padding: 12px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <b style="font-size: 20px; color: #0078d7;">JioTube Pro</b>
        <div class="nav">
            <a href="/admin_upload" class="btn" style="background:#28a745;">UPLOAD</a>
            <a href="/proxy_page" class="btn" style="background:#e74c3c;">PROXY</a>
        </div>
        <form action="/" method="GET" style="display:flex;gap:5px;">
            <input type="text" name="q" placeholder="Video..." style="flex:1;padding:10px;">
            <button type="submit" style="background:#0078d7;color:#fff;border:none;padding:10px;">OK</button>
        </form>
    </div>
    {% for v in videos %}
    <div class="card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" onerror="this.src='https://via.placeholder.com/300x150';">
        <div style="padding:10px;">
            <b style="display:block;margin-bottom:10px;">{{ v.public_id }}</b>
            <a href="{{ v.secure_url }}" class="play">PLAY</a>
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

# Admin Routes
@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('<form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="vname"><button>Up</button></form>')
    return '<form method="POST"><input type="password" name="pw"><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
