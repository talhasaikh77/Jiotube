import os
from flask import Flask, request, render_template_string
import cloudinary
import cloudinary.api

app = Flask(__name__)

# Cloudinary Config (Aapki Details)
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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/axios/1.6.2/axios.min.js"></script>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 10px; }
        .card { background: white; margin: 15px auto; padding: 15px; border-radius: 10px; width: 92%; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .thumb { width: 100%; height: auto; max-height: 200px; object-fit: cover; border-radius: 8px; }
        .btn { text-decoration: none; display: block; margin: 10px 0; padding: 12px; border-radius: 5px; font-size: 14px; color: white; border: none; cursor: pointer; width: 100%; text-align:center; font-weight: bold; }
        .btn-watch { background: #0078d7; }
        .btn-del { background: #28a745; }
        input { width: 90%; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 5px; }
        #progress-wrapper { display: none; margin-top: 10px; }
        #progress-bar-bg { background: #eee; border-radius: 10px; height: 20px; width: 100%; overflow: hidden; }
        #progress-bar-fill { background: #0078d7; height: 100%; width: 0%; transition: 0.2s; }
        #status { font-size: 15px; font-weight: bold; margin-top: 5px; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">JioTube Pro - Atif Khan</h3>
    
    <div style="background:white; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border: 2px solid #0078d7;">
        <b>🚀 Heavy Video Uploader (Unsigned)</b><br><br>
        <input type="file" id="fileInput"><br>
        <input type="text" id="nameInput" placeholder="Video ka naam..."><br>
        <button onclick="startUpload()" class="btn btn-watch">UPLOAD NOW</button>
        
        <div id="progress-wrapper">
            <div id="progress-bar-bg"><div id="progress-bar-fill"></div></div>
            <div id="status">Starting...</div>
        </div>
    </div>

    <form action="/" method="get" style="text-align:center; margin-bottom:20px;">
        <input type="text" name="q" placeholder="Video khojein..." style="width:70%;">
        <button type="submit" style="padding:10px; background:#333; color:white; border:none; border-radius:5px;">Search</button>
    </form>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.replace('.mp4', '.jpg').replace('.mkv', '.jpg') }}" class="thumb">
            <h4 style="margin: 10px 0;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Watch / Download</a>
            <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete Video</a>
        </div>
        {% endfor %}
    </div>

    {% if next_cursor %}
    <div align="center">
        <a href="/?next_cursor={{ next_cursor }}{% if query %}&q={{ query }}{% endif %}" style="background:#333; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Next Page >></a>
    </div>
    {% endif %}

    <script>
    async function startUpload() {
        const file = document.getElementById('fileInput').files[0];
        const name = document.getElementById('nameInput').value;
        if(!file) return alert("File chunein!");

        document.getElementById('progress-wrapper').style.display = 'block';
        const status = document.getElementById('status');
        const fill = document.getElementById('progress-bar-fill');

        const cloudName = "dawterffe";
        const unsignedPreset = "ml_default";

        // Direct Upload to Cloudinary (Render bypass)
        const url = `https://api.cloudinary.com/v1_1/${cloudName}/video/upload`;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("upload_preset", unsignedPreset);
        if(name) formData.append("public_id", name);

        try {
            const res = await axios.post(url, formData, {
                onUploadProgress: (p) => {
                    const percent = Math.round((p.loaded * 100) / p.total);
                    fill.style.width = percent + "%";
                    status.innerText = "Uploading: " + percent + "%";
                }
            });
            status.innerText = "Mubarak ho! Upload Success.";
            setTimeout(() => location.reload(), 2000);
        } catch (err) {
            console.error(err);
            alert("Upload Fail! Check if ml_default is set to Unsigned in Cloudinary.");
        }
    }
    </script>
</body>
</html>
"""

# Search aur Delete routes waise hi rahenge
@app.route('/')
def index():
    search_query = request.args.get('q')
    cursor = request.args.get('next_cursor')
    try:
        if search_query:
            res = cloudinary.api.resources(resource_type="video", type="upload", prefix=search_query, max_results=10, next_cursor=cursor)
        else:
            res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=cursor)
        videos, nxt = res.get('resources', []), res.get('next_cursor')
    except: videos, nxt = [], None
    return render_template_string(HTML_TEMPLATE, videos=videos, next_cursor=nxt, query=search_query)

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:50px;"><h3>Delete: {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass: 809047" required><br><br><button type="submit">DELETE</button></form></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        import cloudinary.uploader
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong Password!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
