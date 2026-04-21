import os
from flask import Flask, request, render_template_string, jsonify
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

# --- HTML Template ---
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
        .btn { text-decoration: none; display: block; margin: 5px 0; padding: 6px; border-radius: 4px; font-size: 12px; color: white; border: none; cursor: pointer; width: 100%; text-align:center; }
        .btn-watch { background: #0078d7; }
        .btn-del { background: #28a745; }
        input[type="text"], input[type="file"] { width: 95%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        #upload-container { background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        #progress-wrapper { display: none; margin-top: 10px; }
        #progress-bar-bg { background: #eee; border-radius: 10px; height: 20px; width: 100%; overflow: hidden; }
        #progress-bar-fill { background: #28a745; height: 100%; width: 0%; transition: width 0.2s; }
        #status-text { font-size: 14px; color: #333; margin-top: 5px; text-align: center; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">Atif Khan Video Manager</h3>
    
    <div id="upload-container">
        <form id="upload-form">
            <b>Fast Upload:</b><br><br>
            <input type="file" id="fileInput" name="file" required><br>
            <input type="text" id="nameInput" name="filename" placeholder="Video Name..."><br>
            <button type="button" onclick="uploadVideo()" class="btn btn-watch" style="font-size:14px;">Upload Start</button>
        </form>

        <div id="progress-wrapper">
            <div id="progress-bar-bg">
                <div id="progress-bar-fill"></div>
            </div>
            <div id="status-text">Speeding up: 0%</div>
        </div>
    </div>

    <form action="/" method="get" style="text-align:center; margin-bottom:20px;">
        <input type="text" name="q" placeholder="Search..." style="width:60%; padding:8px;">
        <button type="submit" style="padding:8px;">Search</button>
    </form>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.replace('.mp4', '.jpg').replace('.mkv', '.jpg') }}" class="thumb">
            <p style="font-size:11px; height:30px; overflow:hidden;"><b>{{ v.public_id }}</b></p>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Watch</a>
            <form action="/delete-page" method="get">
                <input type="hidden" name="public_id" value="{{ v.public_id }}">
                <button type="submit" class="btn btn-del">Delete</button>
            </form>
        </div>
        {% endfor %}
    </div>

    <script>
    function uploadVideo() {
        const fileInput = document.getElementById('fileInput');
        const nameInput = document.getElementById('nameInput');
        const wrapper = document.getElementById('progress-wrapper');
        const fill = document.getElementById('progress-bar-fill');
        const status = document.getElementById('status-text');

        if (fileInput.files.length === 0) return alert("Select Video!");

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("filename", nameInput.value);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload", true);

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                wrapper.style.display = 'block';
                fill.style.width = percent + '%';
                status.innerText = "Speeding up: " + percent + "%";
            }
        };

        xhr.onload = () => {
            if (xhr.status === 200) {
                status.innerText = "Success! Refreshing...";
                setTimeout(() => { location.reload(); }, 1500);
            } else { alert("Upload Failed!"); }
        };
        xhr.send(formData);
    }
    </script>
</body>
</html>
"""

# Is page ka code main.py ke niche hi rehne dega
DELETE_PAGE_TEMPLATE = """
<body style="text-align:center; padding:50px; font-family:sans-serif;">
    <h3>Admin Delete</h3>
    <form action="/confirm-delete" method="post">
        <input type="hidden" name="public_id" value="{{ public_id }}">
        <input type="password" name="password" placeholder="Pass: 809047" required style="padding:10px;"><br><br>
        <button type="submit" style="background:red; color:white; padding:10px;">Confirm Delete</button>
    </form>
</body>
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
        # CHUNK UPLOAD ENABLED FOR SPEED
        cloudinary.uploader.upload_large(
            file, 
            resource_type="video", 
            public_id=name if name else None,
            chunk_size=6000000 # 6MB chunks for faster processing
        )
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

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
        return "<h3>Deleted!</h3><a href='/'>Back</a>"
    return "<h3>Wrong!</h3>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
