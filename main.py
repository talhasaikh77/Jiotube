import os
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

# --- HOME PAGE UI (Saare Buttons Mehfooz Hain) ---
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
            <a href="/login" class="btn-green">Upload</a>
            <a href="/fb-proxy" class="btn-fb">Facebook</a>
        </div>
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Video dhoondein..." value="{{ q }}">
            <button type="submit" style="background:#0078d7; color:#fff; border:none; padding:8px 12px; border-radius:2px;">Ok</button>
        </form>
    </div>

    {% for v in videos %}
    <div class="card">
        <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/320x180?text=Video+Loading...';">
        <div class="v-info">
            <span class="v-title">{{ v.public_id }}</span>
            <a href="{{ v.secure_url }}" class="btn btn-blue">PLAY VIDEO</a>
            <div class="btn-group">
                <a href="/rename-page?pid={{ v.public_id }}" class="btn-sm btn-edit">Rename</a>
                <a href="/delete-page?pid={{ v.public_id }}" class="btn-sm btn-del">Delete</a>
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

# --- NEW PROXY REDIRECT LOGIC ---
@app.route('/fb-proxy')
def fb_proxy():
    # Ye proxy Facebook ko pichka kar (compress) dikhayega
    # Hum 'mbasic' ko ek web-proxy ke through redirect kar rahe hain
    target = "https://mbasic.facebook.com/reels/"
    proxy_gateway = f"https://api.allorigins.win/get?url={target}" # Backup proxy method
    # Direct redirect to compressed mode with a special header
    return redirect(f"https://googleweblight.com/i?u={target}")

# --- REST OF THE CODE (No Changes to Search/Rename/Delete/Upload) ---
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return render_template_string('''<body style="text-align:center; padding:15px;"><h3>Upload</h3><form id="upForm"><input type="file" id="fInp" required><br><br><input type="text" id="vInp" placeholder="Name" required><br><br><button type="button" onclick="upNow()" id="upBtn" style="background:green; color:white; padding:15px;">START</button></form><script>function upNow(){var f=document.getElementById('fInp').files[0]; var n=document.getElementById('vInp').value; var fd=new FormData(); fd.append("file",f); fd.append("vname",n); var x=new XMLHttpRequest(); x.onreadystatechange=function(){if(x.readyState==4)window.location.href="/";}; x.open("POST","/do-upload",true); x.send(fd);}</script></body>''')
    return '<body style="text-align:center; padding:50px;"><form method="POST"><input type="password" name="pw"><button type="submit">Go</button></form></body>'

@app.route('/do-upload', methods=['POST'])
def do_upload():
    file = request.files.get('file'); vname = request.form.get('vname').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return "OK"

@app.route('/rename-page')
def rename_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:20px;"><form action="/confirm-rename" method="POST"><input type="hidden" name="old_pid" value="{{pid}}"><input type="text" name="new_pid" required><br><br><input type="password" name="pw" required><br><br><button type="submit">Update</button></form></body>''', pid=pid)

@app.route('/confirm-rename', methods=['POST'])
def confirm_rename():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.rename(request.form.get('old_pid'), request.form.get('new_pid').replace(' ','_'), resource_type="video")
    return redirect(url_for('index'))

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:20px;"><p>{{pid}}</p><form action="/confirm-del" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" required><br><br><button type="submit" style="background:red; color:white;">Delete</button></form></body>''', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
