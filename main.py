import os
from flask import Flask, request, render_template_string
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)

# --- Cloudinary Configuration ---
cloudinary.config(
  cloud_name = "dawterffe",
  api_key = "258318685843824",
  api_secret = "NxTNXBeLmupMQ0S1FOPU9t6bcjo",
  secure = True
)

ADMIN_PASSWORD = "809047"

# --- HTML Template (Ab ye main.py ke andar hi hai) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jiotube - Atif Khan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 10px; }
        .card { background: white; margin: 10px; padding: 10px; border-radius: 8px; width: 150px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: inline-block; vertical-align: top; }
        .thumb { width: 100%; height: 100px; object-fit: cover; border-radius: 5px; }
        .btn { text-decoration: none; display: block; margin: 5px 0; padding: 6px; border-radius: 4px; font-size: 12px; color: white; border: none; cursor: pointer; width: 100%; }
        .btn-watch { background: #0078d7; }
        .btn-del { background: #28a745; }
        input[type="text"], input[type="file"], input[type="password"] { width: 90%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">Atif Khan Video Manager</h3>
    
    <div style="background:white; padding:15px; border-radius:8px; margin-bottom:15px;">
        <form action="/upload" method="post" enctype="multipart/form-data">
            <b>Upload & Rename:</b><br><br>
            <input type="file" name="file" required><br>
            <input type="text" name="filename" placeholder="Naya naam likhein..."><br>
            <button type="submit" class="btn btn-watch" style="width:100%; font-size:14px;">Upload Start</button>
        </form>
    </div>

    <form action="/" method="get" style="text-align:center; margin-bottom:20px;">
        <input type="text" name="q" placeholder="Video khojein..." style="width:60%;">
        <button type="submit" style="padding:8px;">Search</button>
    </form>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.replace('.mp4', '.jpg').replace('.mkv', '.jpg') }}" class="thumb">
            <p style="font-size:11px; height:30px; overflow:hidden;"><b>{{ v.public_id }}</b></p>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Download / Watch</a>
            
            <form action="/delete-page" method="get">
                <input type="hidden" name="public_id" value="{{ v.public_id }}">
                <button type="submit" class="btn btn-del">Delete Video</button>
            </form>
        </div>
        {% endfor %}
    </div>

    <div align="center" style="margin-top:20px;">
        {% if next_cursor %}
            <a href="/?next_cursor={{ next_cursor }}"><button style="padding:10px;">Next Page >> </button></a>
        {% endif %}
    </div>

    <div align="center" style="background:#333; color:white; padding:15px; margin-top:20px; border-radius:5px;">
        Developed by <b>Atif Khan</b>
    </div>
</body>
</html>
"""

DELETE_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Delete Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="font-family:sans-serif; text-align:center; padding:50px;">
    <h3>Admin Delete Panel</h3>
    <p>Video ID: <b>{{ public_id }}</b></p>
    <form action="/confirm-delete" method="post">
        <input type="hidden" name="public_id" value="{{ public_id }}">
        <input type="password" name="password" placeholder="Admin Password" required style="padding:10px; width:200px;"><br><br>
        <button type="submit" style="background:red; color:white; padding:10px 20px; border:none; border-radius:5px;">Delete From Cloud</button>
    </form>
    <br><a href="/">Back to Home</a>
</body>
</html>
"""

@app.route('/')
def index():
    next_cursor = request.args.get('next_cursor')
    search_query = request.args.get('q')
    try:
        if search_query:
            res = cloudinary.api.resources(resource_type="video", type="upload", prefix=search_query, max_results=10, next_cursor=next_cursor)
        else:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_cursor)
        videos = res.get('resources', [])
        nxt = res.get('next_cursor')
    except:
        videos, nxt = [], None
    return render_template_string(HTML_TEMPLATE, videos=videos, next_cursor=nxt)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    name = request.form.get('filename')
    if file:
        cloudinary.uploader.upload(file, resource_type="video", public_id=name if name else None)
    return "<h3>Success!</h3><a href='/'>Wapas Jayein</a>"

@app.route('/delete-page')
def delete_page():
    public_id = request.args.get('public_id')
    return render_template_string(DELETE_PAGE_TEMPLATE, public_id=public_id)

@app.route('/confirm-delete', methods=['POST'])
def confirm_delete():
    pid = request.form.get('public_id')
    pw = request.form.get('password')
    if pw == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(pid, resource_type="video")
        return "<h3>Deleted!</h3><a href='/'>Wapas Jayein</a>"
    return "<h3>Wrong Password!</h3><a href='/'>Wapas Jayein</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
