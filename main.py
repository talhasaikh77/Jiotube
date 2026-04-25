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

# --- HOME PAGE ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro - Atif Khan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 10px; }
        .header { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
        .search-box { margin: 15px 0; display: flex; gap: 5px; }
        .search-box input { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        .card { background: white; margin: 15px auto; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .thumb { width: 100%; height: auto; max-height: 180px; border-radius: 8px; background: #000; }
        .btn { text-decoration: none; display: block; margin: 5px 0; padding: 10px; border-radius: 5px; font-weight: bold; text-align:center; color: white; border: none; }
        .btn-blue { background: #0078d7; width: 100%; }
        .btn-green { background: #28a745; font-size: 12px; padding: 10px 20px; display: inline-block; }
        .pagination { display: flex; justify-content: center; gap: 10px; padding: 20px; }
        .btn-nav { background: #333; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-size: 13px; }
        .btn-group { display: flex; gap: 5px; margin-top: 10px; }
        .btn-del { background: #dc3545; flex: 1; font-size: 11px; padding: 8px; }
        .btn-edit { background: #f39c12; flex: 1; font-size: 11px; padding: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="color:#0078d7; font-size: 20px;">JioTube Pro</b><br><br>
        <a href="/login" class="btn btn-green">Upload Video 📤</a>
        
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Video dhoondein..." value="{{ q }}">
            <button type="submit" style="background:#0078d7; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">Search</button>
        </form>
    </div>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/300x150?text=Processing';">
            <h4 style="margin: 10px 0; font-size:14px;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-blue">Watch Video</a>
            <div class="btn-group">
                <a href="/rename-page?pid={{ v.public_id }}" class="btn btn-edit">Rename ✏️</a>
                <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete 🗑️</a>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="pagination">
        {% if request.args.get('next_cursor') %}
            <a href="/" class="btn-nav"><< Pehla Page</a>
        {% endif %}
        {% if next_cursor %}
            <a href="/?next_cursor={{ next_cursor }}&q={{ q }}" class="btn-nav">Agla Page >></a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    cursor = request.args.get('next_cursor')
    q = request.args.get('q', '')
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor, prefix=q if q else None)
        videos, nxt = res.get('resources', []), res.get('next_cursor')
    except: videos, nxt = [], None
    return render_template_string(HOME_HTML, videos=videos, next_cursor=nxt, q=q)

# --- UPLOAD PANEL (With Media-Style Progress Bar) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PASSWORD:
            return render_template_string('''
                <body style="text-align:center; padding:20px; font-family:sans-serif; background:#f4f4f4;">
                    <div style="background:white; padding:20px; border-radius:10px; border:1px solid #ccc; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                        <h3>Live Uploading 🚀</h3>
                        <form id="upForm">
                            <label>1. Video File Chunein:</label><br>
                            <input type="file" id="fInp" required style="margin:10px 0;"><br>
                            <label>2. Video Ka Naam:</label><br>
                            <input type="text" id="vInp" placeholder="Naam Likhein" required style="padding:10px; width:85%; margin-bottom:10px; border:1px solid #ccc; border-radius:5px;"><br>
                            
                            <div id="pCont" style="display:none; width:100%; background:#ddd; border-radius:10px; margin:15px 0;">
                                <div id="pBar" style="width:0%; height:20px; background:#28a745; border-radius:10px; color:white; font-size:12px; line-height:20px; text-align:center;">0%</div>
                            </div>
                            
                            <button type="button" onclick="upNow()" id="upBtn" style="background:#28a745; color:white; padding:15px; width:95%; border:none; border-radius:5px; font-weight:bold;">START UPLOAD</button>
                        </form>
                    </div>
                    <script>
                    function upNow() {
                        var f = document.getElementById('fInp').files[0];
                        var n = document.getElementById('vInp').value;
                        if(!f || !n) { alert("Dono bharo!"); return; }
                        var fd = new FormData(); fd.append("file", f); fd.append("vname", n);
                        var x = new XMLHttpRequest();
                        x.upload.onprogress = function(e) {
                            var p = Math.round((e.loaded/e.total)*100);
                            document.getElementById('pCont').style.display="block";
                            document.getElementById('pBar').style.width=p+"%";
                            document.getElementById('pBar').innerHTML=p+"%";
                        };
                        x.onreadystatechange = function() { if(x.readyState==4) window.location.href="/"; };
                        x.open("POST", "/do-upload", true);
                        document.getElementById('upBtn').disabled=true;
                        document.getElementById('upBtn').style.background="#ccc";
                        x.send(fd);
                    }
                    </script>
                    <br><a href="/" style="text-decoration:none; color:black;">← Wapas Jayein</a>
                </body>
            ''')
        return "Galat Password! <a href='/login'>Dobara Koshish Karein</a>"
    return '''<body style="text-align:center; padding:50px;"><form method="POST"><h3>Admin Login</h3><input type="password" name="pw" placeholder="Pass"><button type="submit">Login</button></form></body>'''

@app.route('/do-upload', methods=['POST'])
def do_upload():
    file = request.files.get('file')
    vname = request.form.get('vname').replace(' ', '_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return "SUCCESS"

# --- SECURE RENAME ---
@app.route('/rename-page')
def rename_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:40px; font-family:sans-serif;"><h3>Rename: {{pid}}</h3><form action="/confirm-rename" method="POST"><input type="hidden" name="old_pid" value="{{pid}}"><input type="text" name="new_pid" placeholder="Naya Naam" required style="padding:10px; width:80%;"><br><br><input type="password" name="pw" placeholder="Admin Security Password" required style="padding:10px; width:80%;"><br><br><button type="submit" style="background:#f39c12; color:white; padding:10px 30px; border:none; border-radius:5px;">Update Karein</button></form><br><a href="/">Cancel</a></body>''', pid=pid)

@app.route('/confirm-rename', methods=['POST'])
def confirm_rename():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.rename(request.form.get('old_pid'), request.form.get('new_pid').replace(' ','_'), resource_type="video")
        return redirect(url_for('index'))
    return "Galat Password! Rename nahi hua. <a href='/'>Wapas</a>"

# --- SECURE DELETE ---
@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:50px; font-family:sans-serif;"><h3>Delete Karein?</h3><p style="color:red;">Kya aap sach mein <b>{{pid}}</b> ko hatana chahte hain?</p><form action="/confirm-del" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Admin Security Password" required style="padding:10px; width:80%;"><br><br><button type="submit" style="background:#dc3545; color:white; padding:10px 30px; border:none; border-radius:5px;">Hamesha ke liye Delete</button></form><br><a href="/">Nahi, Wapas Jayein</a></body>''', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return redirect(url_for('index'))
    return "Galat Password! Delete nahi hua. <a href='/'>Wapas</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
