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

# --- SMART LINK FIXER ---
def miniproxy_logic(html, current_url):
    base_parsed = urlparse(current_url)
    base_url = f"{base_parsed.scheme}://{base_parsed.netloc}"
    
    # Absolute URL Injection
    html = html.replace('href="/', f'href="/proxy_go?u={base_url}/')
    html = html.replace('src="/', f'src="/proxy_go?u={base_url}/')
    html = html.replace('action="/', f'action="/proxy_go?u={base_url}/')
    
    # Navigation Bar (Simple HTML taaki Flask error na de)
    nav = f'<div style="background:#000;padding:12px;text-align:center;"><a href="/proxy_page" style="color:#fff;text-decoration:none;font-weight:bold;">[ ← EXIT PROXY ]</a></div>'
    return nav + html

@app.route('/proxy_page')
def proxy_page():
    # Home screen for Proxy
    return render_template_string("""
    <body style="background:#1a1a1a;color:#fff;text-align:center;font-family:sans-serif;padding:20px;">
        <h2>Proxy Engine</h2>
        <form action="/proxy_go" method="GET">
            <input type="text" name="u" placeholder="https://google.com" style="width:80%;padding:10px;border-radius:5px;"><br><br>
            <button style="padding:10px 20px;background:#e74c3c;color:#fff;border:none;border-radius:5px;">OPEN SITE</button>
        </form>
        <div style="margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <a href="/proxy_go?u=https://mbasic.facebook.com" style="padding:15px;background:#333;color:#fff;text-decoration:none;border-radius:5px;">Facebook</a>
            <a href="/proxy_go?u=https://www.google.com" style="padding:15px;background:#333;color:#fff;text-decoration:none;border-radius:5px;">Google</a>
        </div>
        <br><a href="/" style="color:#aaa;">Back to JioTube</a>
    </body>
    """)

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/proxy_page')
    if not u.startswith('http'): u = 'https://' + u
    
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"}
    
    try:
        r = requests.get(u, headers=headers, timeout=15)
        if 'text/html' in r.headers.get('Content-Type', ''):
            # Yahan hum render_template_string use NAHI kar rahe (Error Fix)
            fixed_content = miniproxy_logic(r.text, u)
            return Response(fixed_content, mimetype='text/html')
        else:
            return Response(r.content, mimetype=r.headers.get('Content-Type'))
    except:
        return redirect('/proxy_page')

# --- JIOTUBE HOME ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
    except: videos = []
    
    html = f"""
    <body style="font-family:sans-serif;background:#eee;margin:0;padding:10px;">
        <div style="text-align:center;background:#fff;padding:15px;border-bottom:3px solid #0078d7;">
            <b style="font-size:22px;color:#0078d7;">JioTube Pro</b><br><br>
            <a href="/admin_upload" style="padding:10px;background:green;color:#fff;text-decoration:none;border-radius:5px;">UPLOAD</a>
            <a href="/proxy_page" style="padding:10px;background:red;color:#fff;text-decoration:none;border-radius:5px;">PROXY</a>
        </div>
        {"".join([f'<div style="background:#fff;margin-top:10px;border-radius:8px;overflow:hidden;"><img src="{v["secure_url"].rsplit(".", 1)[0] + ".jpg"}" style="width:100%;"><div style="padding:10px;"><b>{v["public_id"]}</b><br><br><a href="{v["secure_url"]}" style="display:block;background:#0078d7;color:#fff;text-align:center;padding:12px;text-decoration:none;font-weight:bold;">PLAY</a></div></div>' for v in videos])}
    </body>
    """
    return html

@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return '<form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="vname"><button>Up</button></form>'
    return '<form method="POST"><input type="password" name="pw"><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
