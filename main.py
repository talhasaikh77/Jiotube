import os
from flask import Flask, request, render_template_string
import cloudinary
import cloudinary.api
import cloudinary.uploader
import requests

app = Flask(__name__)

# Cloudinary Config
cloudinary.config(
  cloud_name = "dawterffe",
  api_key = "258318685843824",
  api_secret = "NxTNXBeLmupMQ0S1FOPU9t6bcjo",
  secure = True
)

ADMIN_PASSWORD = "809047"

# --- HTML TEMPLATE ---
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
        .btn-ai { background: #8e44ad; padding: 12px 20px; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; }
        input { width: 100%; padding: 12px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        #p-wrap { display: none; margin-top: 10px; background:white; padding:10px; border-radius:10px; }
        #p-bg { background: #eee; border-radius: 10px; height: 15px; width: 100%; overflow: hidden; }
        #p-fill { background: #28a745; height: 100%; width: 0%; transition: 0.2s; }
    </style>
</head>
<body>
    <h3 align="center" style="color:#0078d7;">JioTube Pro - Atif Khan</h3>
    
    <div style="background:white; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border: 2px solid #0078d7;">
        <b>🚀 Uploader (6MB Chill)</b><br><br>
        <input type="file" id="fileInput">
        <input type="text" id="nameInput" placeholder="Video ka naam...">
        <button onclick="startUpload()" class="btn btn-watch">UPLOAD NOW</button>
        <div id="p-wrap">
            <div id="p-bg"><div id="p-fill"></div></div>
            <div id="status" style="font-size:12px; margin-top:5px; color:#0078d7;">Connecting...</div>
        </div>
    </div>

    <form action="/" method="get" style="text-align:center; margin-bottom:15px;">
        <input type="text" name="q" placeholder="Video khojein..." style="width:65%; padding:10px; border-radius:5px; border:1px solid #ccc;">
        <button type="submit" style="padding:10px; background:#333; color:white; border:none; border-radius:5px;">Search</button>
    </form>

    <div align="center">
        {% for v in videos %}
        <div class="card">
            <img src="{{ v.secure_url.rsplit('.', 1)[0] + '.jpg' }}" class="thumb" onerror="this.src='https://via.placeholder.com/300x150?text=Video';">
            <h4 style="margin: 10px 0;">{{ v.public_id }}</h4>
            <a href="{{ v.secure_url }}" class="btn btn-watch">Watch / Download</a>
            <a href="/delete-page?pid={{ v.public_id }}" class="btn btn-del">Delete</a>
        </div>
        {% endfor %}
    </div>

    <div style="text-align:center; padding:20px;">
        {% if next_cursor %}
        <a href="/?next_cursor={{ next_cursor }}{% if query %}&q={{ query }}{% endif %}" style="background:#333; color:white; padding:12px 20px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block; margin-right:5px;">Next Page >></a>
        {% endif %}
        
        <a href="/ai-chat" class="btn-ai">Ask AI 🤖</a>
    </div>

    <script>
    async function startUpload() {
        const file = document.getElementById('fileInput').files[0];
        if(!file) return alert("File chuno!");
        let safeName = document.getElementById('nameInput').value.trim().replace(/[^a-zA-Z0-9]/g, '_');
        document.getElementById('p-wrap').style.display = 'block';
        const status = document.getElementById('status');
        const fill = document.getElementById('p-fill');
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
            status.innerText = `Part ${i+1}/${totalChunks}...`;
            const res = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 'X-Unique-Upload-Id': uniqueId, 'Content-Range': `bytes ${start}-${end-1}/${file.size}` }
            });
            if(!res.ok) return alert("Fail!");
            fill.style.width = Math.round((end/file.size)*100) + "%";
        }
        location.reload();
    }
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def index():
    q = request.args.get('q')
    cursor = request.args.get('next_cursor')
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", prefix=q if q else None, max_results=10, next_cursor=cursor)
        videos, nxt = res.get('resources', []), res.get('next_cursor')
    except: videos, nxt = [], None
    return render_template_string(HTML_TEMPLATE, videos=videos, next_cursor=nxt, query=q)

@app.route('/ai-chat')
def ai_chat_page():
    return '''
    <body style="font-family:sans-serif; padding:20px; background:#f4f4f4; text-align:center;">
        <h3>Jio AI Assistant</h3>
        <form action="/ai-ask" method="POST" onsubmit="document.getElementById('ld').innerText='Soch raha hoon...';">
            <input type="text" name="question" placeholder="Apna sawal likhein..." required style="width:90%; padding:15px; border-radius:10px; border:1px solid #ccc;"><br><br>
            <button type="submit" style="width:90%; background:#8e44ad; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold;">ENTER DABAYEIN</button>
        </form>
        <p id="ld" style="color:#8e44ad; font-weight:bold;"></p>
        <br><a href="/" style="text-decoration:none; color:#333;">Back to Home</a>
    </body>
    '''

@app.route('/ai-ask', methods=['POST'])
def ai_ask():
    user_q = request.form.get('question')
    # AI Logic (Hum yahan ek free AI API use kar rahe hain jo sirf text jawaab degi)
    try:
        response = requests.get(f"https://api.popcat.xyz/chatbot?msg={user_q}&owner=Atif&botname=JioTubeAI")
        answer = response.json().get('response', 'Maaf kijiyega, main samajh nahi paya.')
    except:
        answer = "Internet connection check karein!"
    
    return f'''
    <body style="font-family:sans-serif; padding:20px; background:white;">
        <h4 style="color:#8e44ad;">Sawal: {user_q}</h4>
        <hr>
        <p style="font-size:18px; line-height:1.6;"><b>Jawab:</b> {answer}</p>
        <hr>
        <a href="/ai-chat" style="display:block; text-align:center; background:#0078d7; color:white; padding:15px; text-decoration:none; border-radius:10px;">Ek aur Sawal</a>
        <br>
        <a href="/" style="display:block; text-align:center; color:#333; text-decoration:none;">Home par jayein</a>
    </body>
    '''

@app.route('/delete-page')
def delete_page():
    pid = request.args.get('pid')
    return render_template_string('<body style="text-align:center;padding:50px;"><h3>Delete?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass" required><br><br><button type="submit" class="btn btn-del">DELETE</button></form></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong Password!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
