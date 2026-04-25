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

# --- HOME PAGE TEMPLATE ---
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
        .btn-nav { background: #333; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-size: 14px; }
        .btn-group { display: flex; gap: 5px; margin-top: 10px; }
        .btn-del { background: #dc3545; flex: 1; font-size: 11px; }
        .btn-edit { background: #f39c12; flex: 1; font-size: 11px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="color:#0078d7; font-size: 20px;">JioTube Pro</b><br><br>
        <a href="/login" class="btn btn-green">Upload Video 📤</a>
        
        <form action="/" method="GET" class="search-box">
            <input type="text" name="q" placeholder="Video dhoondein..." value="{{ search_query }}">
            <button type="submit" style="background:#0078d7; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">Search</button>
        </form>
    </div>

    <div align="center">
        {% if not videos %}
            <p style="margin-top:20px; color:#666;">Koi video nahi mili!</p>
        {% endif %}
        
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/300x150?text=Video';">
            <h4 style="margin: 10px 0; font-size:14px;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-blue">Watch Video</a>
            <div class="btn-group">
                <a href="/rename-page?pid={{ v.public_id }}" class="btn btn-edit">Rename</a>
                <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="pagination">
        {% if next_cursor %}
            <a href="/?next_cursor={{ next_cursor }}&q={{ search_query }}" class="btn-nav">Next Page >></a>
        {% endif %}
        {% if request.args.get('next_cursor') %}
            <a href="/" class="btn-nav">First Page</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    cursor = request.args.get('next_cursor')
    query = request.args.get('q', '')
    try:
        # Search query ke saath resources load karna
        if query:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor, prefix=query)
        else:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor)
            
        videos = res.get('resources', [])
        nxt = res.get('next_cursor')
    except:
        videos, nxt = [], None
        
    return render_template_string(HOME_HTML, videos=videos, next_cursor=nxt, search_query=query)

# --- LOGIN & UPLOAD (No JS) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PASSWORD:
            return render_template_string('''
                <body style="text-align:center; padding:30px; font-family:sans-serif;">
                    <h3>Admin Upload</h3>
                    <form action="/do-upload" method="POST" enctype="multipart/form-data">
                        <input type="file" name="file" required><br><br>
                        <input type="text" name="vname" placeholder="Video Name" required style="padding:10px; width:80%;"><br><br>
                        <button type="submit" style="background:#28a745; color:white; padding:15px; width:85%; border:none; border-radius:5px; font-weight:bold;">UPLOAD</button>
                    </form>
                    <br><a href="/">Cancel</a>
                </body>
            ''')
        return "Wrong Password! <a href='/login'>Try Again</a>"
    return '''
        <body style="text-align:center; padding:50px; font-family:sans-serif;">
            <h3>Login</h3>
            <form method="POST">
                <input type="password" name="pw" placeholder="Admin Pass" required style="padding:10px; width:70%;"><br><br>
                <button type="submit" style="background:#333; color:white; padding:10px; border-radius:5px; border:none; width:50%;">Login</button>
            </form>
        </body>
    '''

@app.route('/do-upload', methods=['POST'])
def do_upload():
    file = request.files['file']
    vname = request.form.get('vname').replace(' ', '_')
    if file:
        cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
        return redirect(url_for('index'))
    return "Fail! <a href='/login'>Back</a>"

# --- RENAME & DELETE ---
@app.route('/rename-page')
def rename_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:40px;"><h3>Rename: {{pid}}</h3><form action="/confirm-rename" method="POST"><input type="hidden" name="old_pid" value="{{pid}}"><input type="text" name="new_pid" placeholder="New Name" required><br><br><input type="password" name="pw" placeholder="Admin Pass" required><br><br><button type="submit">Rename</button></form></body>''', pid=pid)

@app.route('/confirm-rename', methods=['POST'])
def confirm_rename():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.rename(request.form.get('old_pid'), request.form.get('new_pid').replace(' ','_'), resource_type="video")
    return redirect(url_for('index'))

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('''<body style="text-align:center;padding:50px;"><h3>Delete {{pid}}?</h3><form action="/confirm-del" method="POST"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass" required><br><br><button type="submit" style="background:red;color:white;padding:10px;">Confirm</button></form></body>''', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
