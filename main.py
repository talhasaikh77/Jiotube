import os
from flask import Flask, request, render_template_string
import cloudinary
import cloudinary.api
import cloudinary.uploader

app = Flask(__name__)

# Cloudinary Config (Aapki details)
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
        .header { display: flex; justify-content: space-between; align-items: center; background: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .card { background: white; margin: 15px auto; padding: 15px; border-radius: 10px; width: 92%; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .thumb { width: 100%; height: auto; max-height: 180px; object-fit: cover; border-radius: 8px; background: #000; }
        .btn { text-decoration: none; display: block; margin: 5px 0; padding: 10px; border-radius: 5px; font-size: 14px; color: white; font-weight: bold; text-align:center; border:none; cursor:pointer; }
        .btn-blue { background: #0078d7; width: 100%; }
        .btn-upload { background: #28a745; padding: 8px 15px; font-size: 12px; }
        .btn-group { display: flex; justify-content: space-between; gap: 5px; margin-top: 10px; }
        .btn-del { background: #dc3545; flex: 1; font-size: 11px; }
        .btn-edit { background: #f39c12; flex: 1; font-size: 11px; }
    </style>
</head>
<body>
    <div class="header">
        <b style="color:#0078d7;">JioTube Pro</b>
        <a href="/upload-panel" class="btn btn-upload">Upload 📤</a>
    </div>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/300x150?text=Video';">
            <h4 style="margin: 10px 0; font-size:14px;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-blue">Watch Video</a>
            <div class="btn-group">
                <a href="/rename-page?pid={{ v.public_id }}" class="btn btn-edit">Rename ✏️</a>
                <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete 🗑️</a>
            </div>
        </div>
        {% endfor %}
    </div>

    <div style="text-align:center; padding:20px;">
        {% if next_cursor %}
        <a href="/?next_cursor={{ next_cursor }}" style="background:#333; color:white; padding:12px 25px; text-decoration:none; border-radius:5px;">Next Page >></a>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def index():
    cursor = request.args.get('next_cursor')
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor)
        videos, nxt = res.get('resources', []), res.get('next_cursor')
    except: videos, nxt = [], None
    return render_template_string(HOME_HTML, videos=videos, next_cursor=nxt)

# Upload Panel (Naam ke option ke saath)
@app.route('/upload-panel')
def upload_panel():
    return '''
    <body style="text-align:center; padding:20px; font-family:sans-serif; background:#f4f4f4;">
        <div style="background:white; padding:20px; border-radius:10px; border: 2px solid #28a745; max-width:400px; margin:auto;">
            <h3>Admin Login</h3>
            <input type="password" id="adminPw" placeholder="Password Dalein" style="padding:12px; width:90%; margin-bottom:10px; border-radius:5px; border:1px solid #ccc;">
            <button onclick="checkPw()" style="background:#333; color:white; padding:10px; border:none; border-radius:5px; width:95%;">Enter Panel</button>
            
            <div id="uploadBox" style="display:none; margin-top:20px; text-align:left;">
                <hr>
                <label><b>1. Video Chunein:</b></label><br>
                <input type="file" id="fileInput" style="margin:10px 0;"><br>
                
                <label><b>2. Video Ka Naam:</b></label><br>
                <input type="text" id="nameInput" placeholder="Ex: My_New_Video" style="padding:12px; width:90%; margin:10px 0; border-radius:5px; border:1px solid #ccc;"><br>
                
                <button onclick="startUpload()" style="background:#28a745; color:white; padding:15px; border:none; width:95%; border-radius:5px; font-weight:bold; cursor:pointer;">START UPLOAD 🚀</button>
                
                <div id="p-wrap" style="display:none; margin-top:15px;">
                    <div style="background:#eee; height:12px; border-radius:6px; overflow:hidden;">
                        <div id="p-fill" style="background:#28a745; width:0%; height:100%; transition:0.3s;"></div>
                    </div>
                    <small id="status" style="color:#28a745; font-weight:bold;">Wait...</small>
                </div>
            </div>
        </div>
        <br><a href="/" style="color:#333; text-decoration:none;">← Back to Home</a>

        <script>
        function checkPw() {
            if(document.getElementById('adminPw').value === "809047") {
                document.getElementById('uploadBox').style.display = 'block';
                document.getElementById('adminPw').disabled = true;
            } else { alert("Wrong Password!"); }
        }

        async function startUpload() {
            const file = document.getElementById('fileInput').files[0];
            const name = document.getElementById('nameInput').value.trim().replace(/ /g, '_');
            
            if(!file) return alert("Pehle file select karein!");
            if(!name) return alert("Video ka naam likhna zaroori hai!");

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
                formData.append("public_id", name);
                
                const res = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Unique-Upload-Id': uniqueId, 'Content-Range': `bytes ${start}-${end-1}/${file.size}` }
                });
                
                if(!res.ok) return alert("Upload Fail! (Size limit 100MB)");
                let percent = Math.round((end/file.size)*100);
                document.getElementById('p-fill').style.width = percent + "%";
                document.getElementById('status').innerText = "Uploading: " + percent + "%";
            }
            alert("Badhai ho! Video Upload ho gaya.");
            location.href = "/";
        }
        </script>
    </body>
    '''

@app.route('/rename-page')
def rename_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:40px;font-family:sans-serif;"><h3>Rename: {{pid}}</h3><form action="/confirm-rename" method="post"><input type="hidden" name="old_pid" value="{{pid}}"><input type="text" name="new_pid" placeholder="Naya naam..." required style="padding:10px;width:80%;"><br><br><input type="password" name="pw" placeholder="Admin Password" required style="padding:10px;width:80%;"><br><br><button type="submit" style="padding:10px;background:#f39c12;color:white;border:none;border-radius:5px;width:85%;">UPDATE NAME</button></form><br><a href="/">Cancel</a></body>', pid=pid)

@app.route('/confirm-rename', methods=['POST'])
def confirm_rename():
    if request.form.get('pw') == ADMIN_PASSWORD:
        old = request.form.get('old_pid')
        new = request.form.get('new_pid').replace(' ','_')
        cloudinary.uploader.rename(old, new, resource_type="video")
        return "Renamed! <a href='/'>Back</a>"
    return "Wrong Pass!"

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:50px;"><h3>Delete: {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass" required><br><br><button type="submit" style="background:red;color:white;padding:10px;">CONFIRM DELETE</button></form></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong Pass!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
