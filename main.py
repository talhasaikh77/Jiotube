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
        input { width: 92%; padding: 8px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
        #progress-wrapper { display: none; margin-top: 10px; }
        #progress-bar-bg { background: #eee; border-radius: 10px; height: 15px; width: 100%; overflow: hidden; }
        #progress-bar-fill { background: #28a745; height: 100%; width: 0%; }
        .nav-btn { background: #333; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">Atif Khan Video Manager</h3>
    
    <div style="background:white; padding:15px; border-radius:8px; margin-bottom:15px;">
        <b>Fast Large Upload:</b><br><br>
        <input type="file" id="fileInput"><br>
        <input type="text" id="nameInput" placeholder="Save as (File Name)..."><br>
        <button onclick="startUpload()" class="btn btn-watch" style="font-size:14px;">Upload Start</button>
        
        <div id="progress-wrapper">
            <div id="progress-bar-bg"><div id="progress-bar-fill"></div></div>
            <div id="status" style="font-size:12px; text-align:center;">0% Uploading...</div>
        </div>
    </div>

    <form action="/" method="get" style="text-align:center; margin-bottom:20px;">
        <input type="text" name="q" placeholder="Video ka naam likhein..." style="width:60%; padding:8px;">
        <button type="submit" style="padding:8px; background:#0078d7; color:white; border:none; border-radius:4px;">Search</button>
    </form>

    <div align="center">
        {% if videos %}
            {% for v in videos %}
            <div class="card">
                <img src="{{ v.secure_url.replace('.mp4', '.jpg').replace('.mkv', '.jpg') }}" class="thumb">
                <p style="font-size:10px; height:25px; overflow:hidden;"><b>{{ v.public_id }}</b></p>
                <a href="{{ v.secure_url }}" class="btn btn-watch">Watch</a>
                <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
            </div>
            {% endfor %}
        {% else %}
            <p>Koi video nahi mili.</p>
        {% endif %}
    </div>

    <div align="center">
        {% if next_cursor %}
            <a href="/?next_cursor={{ next_cursor }}{% if query %}&q={{ query }}{% endif %}" class="nav-btn">Next Page >></a>
        {% endif %}
    </div>

    <script>
    function startUpload() {
        const file = document.getElementById('fileInput').files[0];
        const name = document.getElementById('nameInput').value;
        if(!file) return alert("Select Video!");

        const url = "https://api.cloudinary.com/v1_1/dawterffe/video/upload";
        const fd = new FormData();
        fd.append("file", file);
        fd.append("upload_preset", "ml_default"); 
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
            if (xhr.status === 200) { alert("Upload Done!"); location.reload(); }
            else { alert("Fail! Check Cloudinary Unsigned Preset."); }
        };
        xhr.send(fd);
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    search_query = request.args.get('q')
    cursor = request.args.get('next_cursor')
    try:
        if search_query:
            res = cloudinary.api.resources(resource_type="video", type="upload", prefix=search_query, max_results=10, next_cursor=cursor)
        else:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor)
        
        videos = res.get('resources', [])
        nxt = res.get('next_cursor')
    except: 
        videos, nxt = [], None
    return render_template_string(HTML_TEMPLATE, videos=videos, next_cursor=nxt, query=search_query)

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:50px;font-family:sans-serif;"><h3>Delete Video: {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Enter Password" required style="padding:10px;"><br><br><button type="submit" style="background:red;color:white;padding:10px;border:none;border-radius:5px;">Delete Permanent</button></form><br><a href="/">Cancel</a></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        import cloudinary.uploader
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back Home</a>"
    return "Wrong Password!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
