import os
import requests
from flask import Flask, request, render_template_string, redirect, Response
import cloudinary
import cloudinary.api
import cloudinary.uploader
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# --- Cloudinary Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- MINIPROXY PYTHON LOGIC (Fixed for Images & FB) ---
def miniproxy_fix(html, current_url):
    base_parsed = urlparse(current_url)
    base_url = f"{base_parsed.scheme}://{base_parsed.netloc}"
    
    # Har link, image aur form ko hamare proxy se guzaarna
    # MiniProxy ka asli jadoo yahi hai
    tags = {
        'href="': 'href="/proxy_go?u=',
        'src="': 'src="/proxy_go?u=',
        'action="': 'action="/proxy_go?u=',
        'url("': 'url("/proxy_go?u='
    }
    
    for tag, replacement in tags.items():
        # Relative links ko absolute banana phir replace karna
        html = html.replace(tag + '/', replacement + base_url + '/')
        html = html.replace(tag + 'http', replacement + 'http')
        
    return html

@app.route('/proxy_page')
def proxy_page():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MiniProxy Pro</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #0f0f0f; color: #fff; text-align: center; padding: 15px; }
            .search-box { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 1px solid #333; }
            input { width: 90%; padding: 15px; border-radius: 8px; border: none; background:#000; color:#0f0; margin-bottom: 10px; font-size:16px; }
            button { background: #ff4757; color: #fff; padding: 12px; border: none; border-radius: 8px; font-weight: bold; width: 95%; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px; }
            .tile { background: #2f3542; padding: 20px; color: #fff; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 14px; }
        </style>
    </head>
    <body>
        <h2 style="color:#ff4757;">MINIPROXY ENGINE</h2>
        <div class="search-box">
            <form action="/proxy_go" method="GET">
                <input type="text" name="u" placeholder="Enter URL (e.g. google.com)" required><br>
                <button type="submit">UNLOCK SITE</button>
            </form>
        </div>
        <div class="grid">
            <a href="/proxy_go?u=https://mbasic.facebook.com" class="tile" style="border-top: 4px solid #1e90ff;">FACEBOOK</a>
            <a href="/proxy_go?u=https://www.google.com" class="tile" style="border-top: 4px solid #2ed573;">GOOGLE</a>
            <a href="/proxy_go?u=https://m.youtube.com" class="tile" style="border-top: 4px solid #ff4757;">YOUTUBE</a>
            <a href="/proxy_go?u=https://www.wikipedia.org" class="tile" style="border-top: 4px solid #ffa502;">WIKI</a>
        </div>
        <br><a href="/" style="color:#57606f; text-decoration:none;">← EXIT TO JIOTUBE</a>
    </body>
    </html>
    """)

@app.route('/proxy_go')
def proxy_go():
    target = request.args.get('u')
    if not target: return redirect('/proxy_page')
    if not target.startswith('http'): target = 'https://' + target
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept-Encoding": "identity" # Taaki compression error na aaye
    }
    
    try:
        r = requests.get(target, headers=headers, timeout=20, allow_redirects=True)
        # Content-Type check karna (Image hai ya HTML)
        if 'text/html' in r.headers.get('Content-Type', ''):
            processed_html = miniproxy_fix(r.text, target)
            nav = f'<div style="background:#000;padding:10px;text-align:center;"><a href="/proxy_page" style="color:#fff;text-decoration:none;font-weight:bold;">[ ← BACK TO PROXY ]</a></div>'
            return render_template_string(nav + processed_html)
        else:
            # Agar image ya CSS hai toh direct bhej dena
            return Response(r.content, content_type=r.headers.get('Content-Type'))
    except Exception as e:
        return f"MiniProxy Error: {str(e)}"

# --- JIOTUBE HOME ---
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
            body { font-family: sans-serif; background: #eee; margin: 0; }
            .header { background: #fff; padding: 15px; text-align: center; border-bottom: 4px solid #0078d7; position:sticky; top:0; z-index:100; }
            .nav { display: flex; gap: 8px; margin-top: 10px; }
            .btn { flex: 1; padding: 12px; color: #fff; text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; }
            .v-card { background: #fff; margin: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .v-card img { width: 100%; display: block; }
            .play { display: block; background: #0078d7; color: #fff; text-align: center; padding: 15px; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <b style="font-size: 24px; color: #0078d7;">JioTube Pro</b>
            <div class="nav">
                <a href="/admin_upload" class="btn" style="background:#2ed573;">UPLOAD</a>
                <a href="/proxy_page" class="btn" style="background:#ff4757;">PROXY</a>
            </div>
            <form action="/" method="GET" style="display:flex;gap:5px;margin-top:10px;">
                <input type="text" name="q" placeholder="Search Videos..." style="flex:1;padding:10px;border:1px solid #ddd;border-radius:8px;">
                <button type="submit" style="background:#0078d7;color:#fff;border:none;padding:10px;border-radius:8px;">OK</button>
            </form>
        </div>
        {% for v in videos %}
        <div class="v-card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}">
            <div style="padding:15px;">
                <b style="display:block;margin-bottom:10px;">{{ v.public_id }}</b>
                <a href="{{ v.secure_url }}" class="play">WATCH NOW</a>
            </div>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(HOME_HTML, videos=videos, q=q)

# Admin Upload (Baki sab same)
@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('<form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="vname"><button>Upload</button></form>')
    return '<form method="POST"><input type="password" name="pw"><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
