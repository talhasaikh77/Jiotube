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

# ... (Pura HTML Template wahi rahega jo pichli baar diya tha) ...

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
    return render_template_string('<body style="text-align:center;padding:50px;"><h3>Delete: {{pid}}?</h3><form action="/confirm-del" method="post"><input type="hidden" name="pid" value="{{pid}}"><input type="password" name="pw" placeholder="Pass" required><br><br><button type="submit">DELETE</button></form></body>', pid=pid)

@app.route('/confirm-del', methods=['POST'])
def confirm_del():
    if request.form.get('pw') == ADMIN_PASSWORD:
        import cloudinary.uploader
        cloudinary.uploader.destroy(request.form.get('pid'), resource_type="video")
        return "Deleted! <a href='/'>Back</a>"
    return "Wrong!"

# --- YEH RAHI PORT WALI SETTING ---
if __name__ == '__main__':
    # Render ke liye 'PORT' environment variable lena zaroori hai
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
