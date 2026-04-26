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

# --- HOME PAGE UI (Thumbnail Fit Logic) ---
HOME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 5px; width: 100%; overflow-x: hidden; box-sizing: border-box; }
        .header { background: white; padding: 8px; border-radius: 5px; text-align: center; margin-bottom: 10px; border: 1px solid #ddd; }
        .search-box { margin: 5px 0; display: flex; gap: 2px; }
        .search-box input { flex: 1; padding: 6px; border-radius: 3px; border: 1px solid #ccc; font-size: 12px; }
        
        .card { background: white; margin-bottom: 12px; padding: 5px; border-radius: 5px; text-align: center; border: 1px solid #ddd; width: 100%; box-sizing: border-box; }
        
        /* Image Fit Logic for Jio Bharat */
        .thumb-box { width: 100%; background: #000; border-radius: 3px; overflow: hidden; line-height: 0; }
        .thumb { 
            width: 100%; 
            height: 120px; /* Fixed height for keypad phones */
            object-fit: contain; /* Photo poori dikhegi, kategi nahi */
            background: #000;
        }
        
        .btn { text-decoration: none; display: block; margin: 4px 0; padding: 8px; border-radius: 3px; font-weight: bold; text-align:center; color: white; font-size: 12px; }
        .btn-blue { background: #0078d7; }
        .btn-green { background: #28a745; display: inline-block; padding: 5px 12px; font-size: 11px; }
        .btn-group { display: flex; gap: 3px; margin-top: 5px; }
        .btn-del { background: #dc3545; flex: 1; font-size: 10px; padding: 6px; }
        .btn-edit { background: #f39c12; flex: 1; font-size: 10px; padding: 6px; }
        
        .pagination { display: flex; justify-content: center; gap: 8px; padding: 15px; }
        .btn-nav { background: #333; color: white; padding: 8px 15px; text-decoration: none; border-radius: 3px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="color:#0078d7; font-size: 16px;">JioTube Pro</b><br>
        <a href="/login" class="btn btn-green">Upload Video</a>
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Dhoondein..." value="{{ q }}">
            <button type="submit" style="background:#0078d7; color:white; border:none; padding:6px; border-radius:3px;">Ok</button>
        </form>
    </div>

    <div align="center">
        {% if not videos %}
            <p style="font-size:12px; color:#666; padding:10px;">Kuch nahi mila!<br><a href="/">Home</a></p>
        {% endif %}
        {% for v in videos %}
        <div class="card">
            <div class="thumb-box">
                <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/150x100?text=Video';">
            </div>
            <h4 style="margin: 5px 0; font-size:11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 3px;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-blue">Watch Video</a>
            <div class="btn-group">
                <a href="/rename-page?pid={{ v.public_id }}" class="btn btn-edit">Rename</a>
                <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="pagination">
        {% if q or next_cursor or request.args.get('next_cursor') %}
            <a href="/" class="btn-nav">Main Page</a>
        {% endif %}
        {% if next_cursor and not q %}
            <a href="/?next_cursor={{ next_cursor }}" class="btn-nav">Next Page >></a>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ADMIN FUNCTIONS (Login, Upload, Rename, Delete) ---
@app.route('/')
def index():
    cursor = request.args.get('next_cursor')
    q = request.args.get('q', '').strip().lower()
    try:
        if q:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=100)
            all_vids = res.get('resources', [])
            videos = [v for v in all_vids if q in v.get('public_id', '').lower()]
            nxt = None
        else:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=11, next_cursor=cursor)
            all_vids = res.get('resources', [])
            videos = all_vids[:10]
            nxt = res.get('next_cursor') if len(all_vids) > 10 else None
    except:
        videos, nxt = [], None
    return render_template_string(HOME_HTML, videos=videos, next_cursor=nxt, q=q)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PASSWORD:
            return render_template_string('''
                <body style="text-align:center; padding:15px; font-family:sans-serif;">
                    <h3>Admin Panel</h3>
                    <form id="upForm">
                        <input type="file" id="fInp" required><br><br>
                        <input type="text" id="vInp" placeholder="Video Name" required style="width:85%; padding:10px;"><br><br>
                        <div id="pCont" style="display:none; width:100%; background:#ddd; height:15px; border-radius:5px; margin-bottom:10px;">
                            <div id="pBar" style="width:0%; height:100%; background:#28a745; border-radius:5px; color:white; font-size:10px; text-align:center;">0%</div>
                        </div>
                        <button type="button" onclick="upNow()" id="upBtn" style="background:#28a745; color:white; padding:12px; width:90%; border:none; border-radius:5px;">UPLOAD</button>
                    </form>
                    <script>
                    function upNow() {
                        var f = document.getElementById('fInp').files[0];
                        var n = document.getElementById('vInp').value;
                        if(!f || !n) return;
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
                        x.send(fd);
                    }
                    </script>
                    <br><a href="/">Back</a>
                </body>
            ''')
    return '''<body style="text-align:center; padding:50px;"><form method="POST"><input type="password" name="pw"><button type="submit">Go</button></form></body>'''

@app.route('/do-upload', methods=['POST'])
def do_upload():
    file = request.files.get('file')
    vname = request.form.get('vname').replace(' ', '_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return "OK"

@app.route('/rename-page')
def rename_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:20px;"><h3>Rename</h3><form action="/confirm-rename" method="POST"><input type="hidden" name="old_pid" value="{{pid}}"><input type="text" name="new_pid" placeholder="New Name" required style="width:80%; padding:10px;"><br><br><input type="password" name="pw" placeholder="Pass" required style="width:80%; padding:10px;"><br><br><button type="submit">Update</button></form></body>''', pid=pid)

@app.route('/confirm-rename', methods=['POST'])
def confirm_rename():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.rename(request.form.get('old_pid'), request.form.get('new_pid').replace(' ','_'), resource_type="video")
    return redirect(url_for('index'))

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:20px;"><h3>Delete?</h3><p>{{pid}}</p><form action="/confirm-del" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass" required style="width:80%; padding:10px;"><br><br><button type="submit" style="background:red; color:white;">Delete</button></form></body>''', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

