import os
import requests
from flask import Flask, request, render_template_string, redirect, url_for
import cloudinary
import cloudinary.api
import cloudinary.uploader

app = Flask(__name__)

# --- Cloudinary Config (Check Karein Yeh Sahi Ho) ---
cloudinary.config(
  cloud_name = "dawterffe",
  api_key = "258318685843824",
  api_secret = "NxTNXBeLmupMQ0S1FOPU9t6bcjo",
  secure = True
)

ADMIN_PASSWORD = "809047"

# --- INTERNAL PROXY LOGIC (Facebook Fix) ---
@app.route('/facebook') # Route ka naam simple kar diya
def fb_internal():
    url = "https://mbasic.facebook.com/reels/?locale=en_US"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 4.4.2; Jio Phone Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        resp = requests.get(url, headers=headers)
        content = resp.text.replace('href="https://mbasic.facebook.com', 'href="/fb-proxy-go?u=https://mbasic.facebook.com')
        # Simple Back button
        back_btn = f'<div style="background:#333;padding:10px;text-align:center;"><a href="/" style="color:white;text-decoration:none;font-weight:bold;">[ BACK TO HOME ]</a></div>'
        return render_template_string(back_btn + content)
    except:
        return "Facebook server busy. Please try again later."

@app.route('/fb-proxy-go')
def fb_proxy_go():
    target_url = request.args.get('u')
    # Link missing hone par direct main page par bhej de
    if not target_url:
        return redirect(url_for('index'))
    if "locale=" not in target_url:
        target_url += "&locale=en_US"
    headers = {"User-Agent": "Mozilla/5.0 (Jio Phone)", "Accept-Language": "en-US,en;q=0.9"}
    resp = requests.get(target_url, headers=headers)
    return render_template_string(resp.text.replace('href="https://mbasic.facebook.com', 'href="/fb-proxy-go?u=https://mbasic.facebook.com'))


# --- HOME PAGE UI (Fixed Routes) ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { font-family: sans-serif; background: #eee; margin: 0; padding: 0; width: 100%; overflow-x: hidden; }
        .header { background: #fff; padding: 10px 5px; text-align: center; border-bottom: 2px solid #0078d7; margin-bottom: 5px; }
        .nav-buttons { display: flex; justify-content: center; gap: 8px; margin-bottom: 8px; }
        .search-box { display: flex; gap: 2px; padding: 0 5px 5px 5px; }
        .search-box input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 2px; font-size: 14px; }
        .card { background: #fff; margin-bottom: 15px; border-bottom: 1px solid #ddd; width: 100%; }
        .thumb { width: 100%; height: auto; max-height: 180px; object-fit: cover; background: #000; display: block; }
        .v-info { padding: 8px; text-align: left; }
        .v-title { font-size: 14px; font-weight: bold; color: #333; margin-bottom: 8px; display: block; }
        .btn { text-decoration: none; display: block; text-align: center; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px; }
        .btn-blue { background: #0078d7; color: #fff; }
        .btn-fb { background: #1877F2; color: #fff; padding: 6px 15px; font-size: 12px; border-radius: 3px; text-decoration: none; font-weight: bold; }
        .btn-green { background: #28a745; color: #fff; padding: 6px 15px; font-size: 12px; border-radius: 3px; text-decoration: none; font-weight: bold; }
        .btn-group { display: flex; gap: 5px; margin-top: 5px; }
        .btn-sm { flex: 1; padding: 8px; font-size: 11px; color: #fff; text-decoration: none; border-radius: 3px; text-align: center; font-weight: bold; }
        .btn-edit { background: #f39c12; }
        .btn-del { background: #dc3545; }
        .pagination { padding: 20px; text-align: center; }
        .btn-nav { background: #333; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="color:#0078d7; font-size: 20px;">JioTube Pro</b><br><br>
        <div class="nav-buttons">
            <a href="/login-admin" class="btn-green">Upload</a>
            <a href="/facebook" class="btn-fb">Facebook</a>
        </div>
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Video dhoondein..." value="{{ q }}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:8px 12px; border-radius:2px;">Ok</button>
        </form>
    </div>

    {% for v in videos %}
    <div class="card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/320x180?text=Video';">
        <div class="v-info">
            <span class="v-title">{{ v.public_id }}</span>
            <a href="{{ v.secure_url }}" class="btn btn-blue">PLAY VIDEO</a>
            <div class="btn-group">
                <a href="/video-action?task=rename&pid={{ v.public_id }}" class="btn-sm btn-edit">Rename</a>
                <a href="/video-action?task=delete&pid={{ v.public_id }}" class="btn-sm btn-del">Delete</a>
            </div>
        </div>
    </div>
    {% endfor %}

    <div class="pagination">
        {% if q or next_cursor %}<a href="/" class="btn-nav">Main Page</a>{% endif %}
        {% if next_cursor and not q %}
            <a href="/?next_cursor={{ next_cursor }}" class="btn-nav">Next Page >></a>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ADMIN ROUTES (Fixed to Prevent 404) ---
@app.route('/')
def index():
    cursor = request.args.get('next_cursor'); q = request.args.get('q', '').strip().lower()
    try:
        if q:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
            all_vids = res.get('resources', [])
            videos = [v for v in all_vids if q in v.get('public_id', '').lower()]; nxt = None
        else:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=11, next_cursor=cursor)
            all_vids = res.get('resources', [])
            videos = all_vids[:10]; nxt = res.get('next_cursor') if len(all_vids) > 10 else None
    except: videos, nxt = [], None
    return render_template_string(HOME_HTML, videos=videos, next_cursor=nxt, q=q)

@app.route('/login-admin', methods=['GET', 'POST']) # Route ka naam unique kiya
def login():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('''<body style="text-align:center; padding:15px; font-family:sans-serif;"><h3>Upload</h3><form id="upForm"><input type="file" id="fInp" required><br><br><input type="text" id="vInp" placeholder="Video Name" required><br><br><button type="button" onclick="upNow()" id="upBtn" style="background:#28a745; color:white; padding:10px 20px; font-weight:bold; border:none; border-radius:4px;">START UPLOAD</button></form><p id="v-status"></p><script>function upNow(){document.getElementById('upBtn').innerHTML='Uploading...'; var f=document.getElementById('fInp').files[0]; var n=document.getElementById('vInp').value; var fd=new FormData(); fd.append("file",f); fd.append("vname",n); var x=new XMLHttpRequest(); x.onreadystatechange=function(){if(x.readyState==4){if(x.status==200){window.location.href="/";}else{document.getElementById('v-status').innerHTML='Error uploading.';document.getElementById('upBtn').innerHTML='START UPLOAD';}}}; x.open("POST","/upload-api",true); x.send(fd);}</script></body>''')
    return '<body style="text-align:center; padding:50px; font-family:sans-serif;"><form method="POST"><input type="password" name="pw" placeholder="Admin PW" style="padding:10px; border-radius:4px;"><br><br><button type="submit" style="padding:10px 20px;">Submit</button></form></body>'

@app.route('/upload-api', methods=['POST'])
def do_upload():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return "OK"

# Combine Rename & Delete Route logic to reduce route number
@app.route('/video-action')
def video_action():
    task = request.args.get('task')
    pid = request.args.get('pid')
    
    if task == 'rename':
        return render_template_string('''<body style="text-align:center;padding:20px;font-family:sans-serif;"><h3>Rename: {{pid}}</h3><form action="/confirm-action" method="POST"><input type="hidden" name="old_pid" value="{{pid}}"><input type="hidden" name="task" value="rename"><input type="text" name="new_pid" placeholder="New Name" required style="padding:10px; border-radius:4px;"><br><br><input type="password" name="pw" placeholder="Admin PW" required style="padding:10px; border-radius:4px;"><br><br><button type="submit" style="background:#f39c12; color:white; padding:10px 20px; font-weight:bold; border:none; border-radius:4px;">Update</button><br><br><a href="/">Cancel</a></form></body>''', pid=pid)
    elif task == 'delete':
        return render_template_string('''<body style="text-align:center;padding:20px;font-family:sans-serif;"><h3 style="color:red;">Delete: {{pid}}</h3><p>Sure delete video?</p><form action="/confirm-action" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="hidden" name="task" value="delete"><input type="password" name="pw" placeholder="Admin PW" required style="padding:10px; border-radius:4px;"><br><br><button type="submit" style="background:red; color:white; padding:10px 20px; font-weight:bold; border:none; border-radius:4px;">Yes, Delete</button><br><br><a href="/">Cancel</a></form></body>''', pid=pid)
    return redirect(url_for('index'))

@app.route('/confirm-action', methods=['POST'])
def confirm_action():
    if request.form.get('pw') != ADMIN_PASSWORD:
        return redirect(url_for('index'))
        
    task = request.form.get('task')
    
    if task == 'rename':
        cloudinary.uploader.rename(request.form.get('old_pid'), request.form.get('new_pid').replace(' ','_'), resource_type="video")
    elif task == 'delete':
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
