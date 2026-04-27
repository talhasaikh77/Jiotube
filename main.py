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

# --- SUPER PROXY ENGINE (Facebook & Image Fix) ---
@app.route('/proxy_page')
def proxy_page():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pro Proxy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #121212; color: #fff; text-align: center; padding: 20px; }
            .box { background: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; }
            input { width: 85%; padding: 12px; border-radius: 6px; border: 1px solid #444; background:#000; color:#fff; margin-bottom: 10px; }
            button { background: #e74c3c; color: #fff; padding: 12px; border: none; border-radius: 6px; font-weight: bold; width: 90%; cursor: pointer; }
            .links { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 25px; }
            .l-btn { background: #252525; padding: 15px; color: #fff; text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: bold; border: 1px solid #333; }
        </style>
    </head>
    <body>
        <h2 style="color:#e74c3c;">PROXY BROWSER</h2>
        <div class="box">
            <form action="/proxy_go" method="GET">
                <input type="text" name="u" placeholder="https://google.com" required><br>
                <button type="submit">SEARCH / OPEN</button>
            </form>
        </div>
        <div class="links">
            <a href="/proxy_go?u=https://mbasic.facebook.com" class="l-btn" style="border-bottom: 3px solid #1877f2;">FACEBOOK</a>
            <a href="/proxy_go?u=https://www.google.com" class="l-btn" style="border-bottom: 3px solid #ea4335;">GOOGLE</a>
            <a href="/proxy_go?u=https://m.youtube.com" class="l-btn" style="border-bottom: 3px solid #ff0000;">YOUTUBE</a>
            <a href="/proxy_go?u=https://www.bing.com" class="l-btn" style="border-bottom: 3px solid #00a4ef;">BING</a>
        </div>
        <br><a href="/" style="color:#666; text-decoration:none;">← Back to Home</a>
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
    # Professional Headers taaki "Something went wrong" na aaye
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        content = resp.text
        
        # Absolute URL system taaki Images aur Links sahi chalein
        base_parsed = urlparse(url)
        base_url = f"{base_parsed.scheme}://{base_parsed.netloc}"
        
        # Fixing Links, Forms, and IMAGES (Sabse zaroori)
        content = content.replace('href="/', f'href="/proxy_go?u={base_url}/')
        content = content.replace('src="/', f'src="/proxy_go?u={base_url}/')
        content = content.replace('action="/', f'action="/proxy_go?u={base_url}/')
        
        # Agar image ka direct URL hai toh use bhi proxy se guzarna
        content = content.replace('https://', '/proxy_go?u=https://')

        nav = f'''<div style="background:#000;padding:10px;text-align:center;position:sticky;top:0;z-index:9999;border-bottom:1px solid #333;">
                    <a href="/proxy_page" style="color:#fff;text-decoration:none;font-weight:bold;font-size:14px;">[ ← EXIT PROXY ]</a>
                  </div>'''
        return render_template_string(nav + content)
    except Exception as e:
        return f"Proxy Error: {str(e)}"

# --- JIOTUBE HOME UI ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
    except: videos = []
    
    HOME_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JioTube Pro</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #f0f2f5; margin: 0; }
            .top { background: #fff; padding: 15px; text-align: center; border-bottom: 3px solid #0078d7; }
            .nav { display: flex; gap: 10px; margin: 15px 0; }
            .btn { flex: 1; padding: 12px; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; text-align: center; }
            .v-card { background: #fff; margin: 15px; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            .v-card img { width: 100%; display: block; }
            .play { display: block; background: #0078d7; color: #fff; text-align: center; padding: 15px; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="top">
            <b style="font-size: 24px; color:#0078d7;">JioTube Pro</b>
            <div class="nav">
                <a href="/admin_upload" class="btn" style="background:#2ecc71;">UPLOAD</a>
                <a href="/proxy_page" class="btn" style="background:#e74c3c;">PROXY</a>
            </div>
            <form action="/" method="GET" style="display:flex;gap:5px;">
                <input type="text" name="q" placeholder="Video Search..." style="flex:1;padding:12px;border:1px solid #ddd;border-radius:6px;">
                <button type="submit" style="background:#0078d7;color:#fff;border:none;padding:10px 15px;border-radius:6px;">OK</button>
            </form>
        </div>
        {% for v in videos %}
        <div class="v-card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}">
            <div style="padding:15px;">
                <b style="display:block;margin-bottom:10px;font-size:16px;">{{ v.public_id }}</b>
                <a href="{{ v.secure_url }}" class="play">WATCH VIDEO</a>
            </div>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(HOME_HTML, videos=videos, q=q)

# Admin upload logic
@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('<form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="vname"><button>Start</button></form>')
    return '<form method="POST"><input type="password" name="pw"><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
