import os
from flask import Flask, request, render_template_string
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>JioTube Pro - Atif Khan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 10px; }
        .card { background: white; margin: 15px auto; padding: 15px; border-radius: 10px; width: 92%; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .thumb { width: 100%; height: auto; max-height: 200px; object-fit: cover; border-radius: 8px; background: #000; }
        .btn { text-decoration: none; display: block; margin: 10px 0; padding: 12px; border-radius: 5px; font-size: 14px; color: white; border: none; cursor: pointer; width: 100%; text-align:center; font-weight: bold; }
        .btn-watch { background: #0078d7; }
        .btn-del { background: #dc3545; }
        .btn-chat { background: #25d366; padding: 12px 20px; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; }
        input { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        #p-wrap { display: none; margin-top: 10px; background:white; padding:10px; border-radius:10px; }
        #p-bg { background: #eee; border-radius: 10px; height: 15px; width: 100%; overflow: hidden; }
        #p-fill { background: #28a745; height: 100%; width: 0%; transition: 0.2s; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">JioTube Pro - Atif Khan</h3>
    
    <div style="background:white; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border: 2px solid #0078d7;">
        <b>🚀 All-Size Uploader</b><br><br>
        <input type="file" id="fileInput">
        <input type="text" id="nameInput" placeholder="Video name...">
        <button onclick="startUpload()" class="btn btn-watch">UPLOAD NOW</button>
        <div id="p-wrap">
            <div id="p-bg"><div id="p-fill"></div></div>
            <div id="status" style="font-size:12px; margin-top:5px; color:#0078d7;">Tayyari...</div>
        </div>
    </div>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/300x150?text=Video';">
            <h4 style="margin: 10px 0;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Watch Online</a>
            <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
        </div>
        {% endfor %}
    </div>

    <div style="text-align:center; padding:20px;">
        {% if next_cursor %}
        <a href="/?next_cursor={{ next_cursor }}" style="background:#333; color:white; padding:12px 25px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block; margin-right:5px;">Next Page >></a>
        {% endif %}
        <a href="https://wa.me/918090477000" class="btn-chat">Live Chat 💬</a>
    </div>

    <script>
    async function startUpload() {
        const file = document.getElementById('fileInput').files[0];
        if(!file) return alert("File chuno!");
        let safeName = document.getElementById('nameInput').value.trim().replace(/[^a-zA-Z0-9]/g, '_');
        document.getElementById('p-wrap').style.display = 'block';
        const url = `https://api.cloudinary.com/v1_1/dawterffe/video/upload`;
        const chunkSize = 6 * 1024 * 1024;
        const totalChunks = Math.ceil(file.size / chunkSize);
        const uniqueId = "atif_" + Date.now();

        for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(file.size, start + chunkSize);
            const formData = new FormData();
            formData.append("file", file.slice(start, end));
            formData.append("upload_preset", "ml_default");
            formData.append("resource_type", "video");
            if(safeName) formData.append("public_id", safeName);
            const res = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 'X-Unique-Upload-Id': uniqueId, 'Content-Range': `bytes ${start}-${end-1}/${file.size}` }
            });
            if(!res.ok) return alert("Upload Fail! (100MB Limit)");
            document.getElementById('p-fill').style.width = Math.round((end/file.size)*100) + "%";
        }
        location.reload();
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    cursor = request.args.get('next_cursor')
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor)
        videos, nxt = res.get('resources', []), res.get('next_cursor')
    except: videos, nxt = [], None
    return render_template_string(HTML_TEMPLATE, videos=videos, next_cursor=nxt)

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:50px;"><h3>Delete: {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Admin Pass" required><br><br><button type="submit" style="background:red; color:white; padding:10px; border:none; border-radius:5px;">CONFIRM DELETE</button></form></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong Password!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
