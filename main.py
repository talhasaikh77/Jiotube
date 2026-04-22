import os
from flask import Flask, request, render_template_string
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
    <title>JioTube Pro - Atif Khan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 10px; }
        .card { background: white; margin: 15px auto; padding: 15px; border-radius: 10px; width: 92%; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .thumb { width: 100%; height: auto; max-height: 200px; object-fit: cover; border-radius: 8px; background: #000; }
        .btn { text-decoration: none; display: block; margin: 10px 0; padding: 12px; border-radius: 5px; font-size: 14px; color: white; border: none; cursor: pointer; width: 100%; text-align:center; font-weight: bold; }
        .btn-watch { background: #0078d7; }
        .btn-del { background: #28a745; }
        input { width: 90%; padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        #p-wrap { display: none; margin-top: 10px; background:white; padding:10px; border-radius:10px; }
        #p-bg { background: #eee; border-radius: 10px; height: 15px; width: 100%; overflow: hidden; }
        #p-fill { background: #28a745; height: 100%; width: 0%; transition: 0.2s; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">JioTube Pro - Atif Khan</h3>
    
    <div style="background:white; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border: 2px solid #0078d7;">
        <b>🚀 Uploader (6MB Chill)</b><br><br>
        <input type="file" id="fileInput"><br>
        <input type="text" id="nameInput" placeholder="Video ka naam..."><br>
        <button onclick="startUpload()" class="btn btn-watch">UPLOAD NOW</button>
        
        <div id="p-wrap">
            <div id="p-bg"><div id="p-fill"></div></div>
            <div id="status" style="font-size:12px; margin-top:5px; color:#0078d7;">Tayyari...</div>
        </div>
    </div>

    <form action="/" method="get" style="text-align:center; margin-bottom:15px;">
        <input type="text" name="q" placeholder="Video khojein..." style="width:60%;">
        <button type="submit" style="padding:10px; background:#333; color:white; border:none; border-radius:5px;">Search</button>
    </form>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/300x150?text=Processing...';">
            <h4 style="margin: 10px 0;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Watch / Download</a>
            <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
        </div>
        {% endfor %}
    </div>

    {% if next_cursor %}
    <div style="text-align:center; padding:20px;">
        <a href="/?next_cursor={{ next_cursor }}{% if query %}&q={{ query }}{% endif %}" style="background:#333; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">Next Page >></a>
    </div>
    {% endif %}

    <script>
    async function startUpload() {
        const file = document.getElementById('fileInput').files[0];
        if(!file) return alert("Pehle file select karo!");

        // Atif Bhai, ye line naam se saari galti saaf kar degi
        let rawName = document.getElementById('nameInput').value.trim();
        let safeName = rawName.replace(/[^a-zA-Z0-9]/g, '_'); 
        
        document.getElementById('p-wrap').style.display = 'block';
        const status = document.getElementById('status');
        const fill = document.getElementById('p-fill');

        const cloudName = "dawterffe";
        const unsignedPreset = "ml_default";
        const url = `https://api.cloudinary.com/v1_1/${cloudName}/video/upload`;

        const chunkSize = 6 * 1024 * 1024; // 6MB CHILL
        const totalChunks = Math.ceil(file.size / chunkSize);
        const uniqueId = "atif_" + Date.now();

        for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(file.size, start + chunkSize);
            const chunk = file.slice(start, end);
            const formData = new FormData();
            formData.append("file", chunk);
            formData.append("upload_preset", unsignedPreset);
            // Agar naam diya hai toh hi bhejenge, warna Cloudinary khud naam rakh lega
            if(safeName) formData.append("public_id", safeName);

            status.innerText = `Tukda ${i+1}/${totalChunks} ja raha hai...`;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Unique-Upload-Id': uniqueId,
                        'Content-Range': `bytes ${start}-${end - 1}/${file.size}`
                    }
                });
                if (!response.ok) {
                    const errorJson = await response.json();
                    throw new Error(errorJson.error.message);
                }
                const percent = Math.round((end / file.size) * 100);
                fill.style.width = percent + "%";
                status.innerText = "Upload: " + percent + "%";
            } catch (err) {
                alert("Cloudinary Error: " + err.message);
                return;
            }
        }
        status.innerText = "Mubarak! Refresh ho raha hai...";
        setTimeout(() => location.reload(), 1500);
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
        res = cloudinary.api.resources(resource_type="video", type="upload", prefix=search_query if search_query else None, max_results=10, next_cursor=cursor)
        videos, nxt = res.get('resources', []), res.get('next_cursor')
    except: videos, nxt = [], None
    return render_template_string(HTML_TEMPLATE, videos=videos, next_cursor=nxt, query=search_query)

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:50px;"><h3>Mita dein: {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass" required><br><br><button type="submit">DELETE</button></form></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        import cloudinary.uploader
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
