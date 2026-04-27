import os
import requests
from flask import Flask, request, redirect, Response, render_template_string
import cloudinary
import cloudinary.api
import cloudinary.uploader
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

# --- Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- GITHUB PROXY LOGIC ---
def github_proxy_engine(content, target_url):
    parsed = urlparse(target_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    content = content.replace('href="/', f'href="/proxy_go?u={base}/')
    content = content.replace('src="/', f'src="/proxy_go?u={base}/')
    content = content.replace('action="/', f'action="/proxy_go?u={base}/')
    content = content.replace('href="https://', '/proxy_go?u=https://')
    nav = f'<div style="background:#000;padding:15px;text-align:center;border-bottom:2px solid red;"><a href="/proxy_page" style="color:#fff;text-decoration:none;font-weight:bold;">[ EXIT PROXY ]</a></div>'
    return nav + content

@app.route('/proxy_page')
def proxy_page():
    return '''
    <body style="background:#000;color:#fff;text-align:center;font-family:sans-serif;padding:30px;">
        <h1 style="color:red;">GitHub Proxy Pro</h1>
        <form action="/proxy_go" method="GET">
            <input type="text" name="u" placeholder="https://mbasic.facebook.com" style="width:85%;padding:15px;border-radius:10px;"><br><br>
            <button style="width:90%;padding:15px;background:red;color:#fff;border:none;border-radius:10px;font-weight:bold;">OPEN</button>
        </form>
        <div style="margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <a href="/proxy_go?u=https://mbasic.facebook.com" style="background:#222;padding:15px;color:#fff;text-decoration:none;border-radius:10px;">Facebook</a>
            <a href="/proxy_go?u=https://www.google.com" style="background:#222;padding:15px;color:#fff;text-decoration:none;border-radius:10px;">Google</a>
        </div>
        <br><a href="/" style="color:#555;">← JioTube Home</a>
    </body>
    '''

@app.route('/proxy_go')
def proxy_go():
    u = request.args.get('u')
    if not u: return redirect('/proxy_page')
    if not u.startswith('http'): u = 'https://' + u
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"}
    try:
        r = requests.get(u, headers=headers, timeout=15, allow_redirects=True)
        if "text/html" in r.headers.get("Content-Type", ""):
            fixed = github_proxy_engine(r.text, u)
            return Response(fixed, mimetype="text/html")
        return Response(r.content, mimetype=r.headers.get("Content-Type"))
    except: return redirect('/proxy_page')

# --- JIOTUBE HOME (Buttons Added) ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
    except: videos = []
    
    v_cards = ""
    for v in videos:
        v_cards += f'''
        <div style="background:#fff;margin-bottom:20px;border-radius:10px;overflow:hidden;box-shadow:0 2px 5px rgba(0,0,0,0.1);">
            <img src="{v['secure_url'].rsplit('.', 1)[0] + '.jpg'}" style="width:100%;">
            <div style="padding:15px;">
                <b style="display:block;margin-bottom:10px;">{v['public_id']}</b>
                <a href="{v['secure_url']}" style="display:block;background:#0078d7;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:5px;font-weight:bold;margin-bottom:10px;">PLAY</a>
                <div style="display:flex;gap:5px;">
                    <a href="/modify?task=rename&pid={v['public_id']}" style="flex:1;background:#f39c12;color:#fff;text-align:center;padding:8px;text-decoration:none;border-radius:4px;font-size:12px;">RENAME</a>
                    <a href="/modify?task=delete&pid={v['public_id']}" style="flex:1;background:#e74c3c;color:#fff;text-align:center;padding:8px;text-decoration:none;border-radius:4px;font-size:12px;">DELETE</a>
                </div>
            </div>
        </div>
        '''

    return f'''
    <body style="background:#f4f4f4;margin:0;font-family:sans-serif;">
        <div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #0078d7;position:sticky;top:0;z-index:10;">
            <h2 style="margin:0;color:#0078d7;">JioTube Pro</h2>
            <div style="margin-top:10px;display:flex;gap:5px;">
                <a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:10px;text-decoration:none;border-radius:5px;font-size:13px;">UPLOAD</a>
                <a href="/proxy_page" style="flex:1;background:red;color:#fff;padding:10px;text-decoration:none;border-radius:5px;font-size:13px;">PROXY</a>
            </div>
            <form action="/" method="GET" style="margin-top:10px;display:flex;gap:5px;">
                <input type="text" name="q" placeholder="Video Search..." style="flex:1;padding:8px;" value="{q}">
                <button type="submit" style="background:#0078d7;color:#fff;border:none;padding:8px 15px;">OK</button>
            </form>
        </div>
        <div style="padding:10px;">{v_cards}</div>
    </body>
    '''

# --- Admin & Modify Routes ---
@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return '<form action="/do_up" method="POST" enctype="multipart/form-data"><input type="file" name="file"><input type="text" name="vname" placeholder="Name"><button>Up</button></form>'
    return '<form method="POST"><input type="password" name="pw" placeholder="Pass"><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname', 'video').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    task = request.args.get('task'); pid = request.args.get('pid')
    return render_template_string('''
        <form action="/confirm" method="POST" style="padding:20px;text-align:center;">
            <h3>{{task.upper()}} : {{pid}}</h3>
            <input type="hidden" name="pid" value="{{pid}}">
            <input type="hidden" name="task" value="{{task}}">
            {% if task=="rename" %}<input type="text" name="new_name" placeholder="New Name"><br><br>{% endif %}
            <input type="password" name="pw" placeholder="Password"><br><br>
            <button type="submit">CONFIRM</button>
        </form>
    ''', task=task, pid=pid)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new_name').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
