import os
from flask import Flask, request, render_template_string, jsonify
import cloudinary
import cloudinary.api

app = Flask(__name__)

# Cloudinary Config
cloudinary.config(
  cloud_name = "dawterffe",
  api_key = "258318685843824",
  api_secret = "NxTNXBeLmupMQ0S1FOPU9t6bcjo",
  secure = True
)

ADMIN_PASSWORD = "809047"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jiotube - Atif Khan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 10px; }
        .card { background: white; margin: 10px; padding: 10px; border-radius: 8px; width: 140px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: inline-block; vertical-align: top; }
        .thumb { width: 100%; height: 90px; object-fit: cover; border-radius: 5px; }
        .btn { text-decoration: none; display: block; margin: 5px 0; padding: 6px; border-radius: 4px; font-size: 12px; color: white; border: none; cursor: pointer; width: 100%; text-align:center; }
        .btn-watch { background: #0078d7; }
        .btn-del { background: #28a745; }
        input { width: 95%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        #progress-wrapper { display: none; margin-top: 10px; }
        #progress-bar-bg { background: #eee; border-radius: 10px; height: 15px; width: 100%; overflow: hidden; }
        #progress-bar-fill { background: #28a745; height: 100%; width: 0%; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">Atif Khan Video Manager</h3>
    
    <div style="background:white; padding:15px; border-radius:8px; margin-bottom:15px;">
        <b>Upload Large Video (Up to 500MB):</b><br><br>
        <input type="file" id="fileInput"><br>
        <input type="text" id="nameInput" placeholder="Naya naam..."><br>
        <button onclick="startUpload()" class="btn btn-watch" style="font-size:14px;">Upload Start</button>
        
        <div id="progress-wrapper">
            <div id="progress-bar-bg"><div id="progress-bar-fill"></div></div>
            <div id="status" style="font-size:12px; text-align:center;">0%</div>
        </div>
    </div>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.replace('.mp4', '.jpg').replace('.mkv', '.jpg') }}" class="thumb">
            <p style="font-size:10px; height:25px; overflow:hidden;">{{ v.public_id }}</p>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Watch</a>
            <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
        </div>
        {% endfor %}
    </div>

    <script>
    function startUpload() {
        const file = document.getElementById('fileInput').files[0];
        const name = document.getElementById('nameInput').value;
        if(!file) return alert("File chunein!");

        const url = "https://api.cloudinary.com/v1_1/dawterffe/video/upload";
        const fd = new FormData();
        fd.append("file", file);
        fd.append("upload_preset", "ml_default"); // Make sure this is enabled in Cloudinary
        if(name) fd.append("public_id", name);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        
        document.getElementById('progress-wrapper').style.display = 'block';

        xhr.upload.onprogress = (e) => {
            const percent = Math.round((e.loaded / e.total) * 100);
            document.getElementById('progress-bar-fill').style.width = percent + '%';
            document.getElementById('status').innerText = percent + "% Uploading...";
        };

        xhr.onload = () => {
            alert("Upload Successful!");
            location.reload();
        };
        xhr.send(fd);
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10)
        videos = res.get('resources', [])
    except: videos = []
    return render_template_string(HTML_TEMPLATE, videos=videos)

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<h3>Delete {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="809047"><button type="submit">Delete</button></form>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        import cloudinary.uploader
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong Password!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
