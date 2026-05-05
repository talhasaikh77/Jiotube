import os, time, cloudinary, cloudinary.uploader, cloudinary.api
from flask import Flask, request, redirect, render_template_string, session, send_file
from pytubefix import YouTube
import threading

app = Flask(__name__)
app.secret_key = "jiotube_v103_full_fix"

# --- CONFIG ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
SECURE_PASS = "809047"

STYLE = """<style>
    :root { --jio: #0072ef; --yt: #ff0000; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 30px; }
    .header { background: var(--jio); padding:15px; text-align:center; color:#fff; font-weight:bold; position:sticky; top:0; z-index:1000; font-size:18px; }
    .card { background: #fff; margin:12px; border-radius:12px; overflow:hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 1px solid #eee; }
    .up-panel { padding:15px; background:#fff; border-bottom: 2px solid var(--jio); }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:inline-block; cursor:pointer; }
    .btn-jio { background: var(--jio); } .btn-yt { background: var(--yt); }
    .btn-green { background: #28a745; } .btn-orange { background: #f39c12; }
    input { width:100%; padding:12px; margin:8px 0; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; font-size:14px; }
    .thumb-container { width:100%; height:190px; background:#000; position:relative; }
    .thumb-img { width:100%; height:100%; object-fit:cover; }
    .vid-info { padding:12px; }
    .action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
</style>"""

# --- CLOUD UPLOAD ENGINE ---
def background_upload(url, custom_name):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        cloudinary.uploader.upload(stream.url, 
            resource_type="video",
            public_id=custom_name,
            eager=[{"width": 480, "height": 320, "crop": "pad", "video_codec": "h264"}],
            eager_async=True
        )
    except Exception as e: print(f"Error: {e}")

# --- MAIN HOME ---
@app.route("/")
def index():
    q = request.args.get("q")
    curs = request.args.get("next")
    
    # 1. Header & Upload Panel
    html = f"{STYLE}<div class='header'>JIOTUBE MASTER CLOUD</div>"
    html += f'''<div class="up-panel">
        <form action="/process_upload" method="POST">
            <input name="url" placeholder="YouTube or Video Link" required>
            <input name="name" placeholder="Give Video Name" required>
            <button class="btn btn-jio" style="width:100%; font-size:14px;">START CLOUD UPLOAD</button>
        </form>
    </div>'''

    # 2. Search Bar
    html += f'''<div style="padding:0 12px;"><form action="/" method="GET">
        <input name="q" placeholder="Search videos..." value="{q if q else ''}">
        <button class="btn btn-yt" style="width:100%;">FIND</button>
    </form></div>'''

    # 3. Fetch & List Videos
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=20, next_cursor=curs)
        vids = res.get("resources", [])
        next_c = res.get("next_cursor")
        
        if q: vids = [v for v in vids if q.lower() in v['public_id'].lower()]

        for v in vids:
            p_id = v['public_id']
            # Thumbnail generation logic from Cloudinary
            thumb_url = v['secure_url'].rsplit('.', 1)[0] + ".jpg"
            
            html += f'''<div class="card">
                <div class="thumb-container">
                    <img src="{thumb_url}" class="thumb-img">
                    <div style="position:absolute; bottom:5px; right:5px; background:rgba(0,0,0,0.7); color:#fff; padding:2px 5px; font-size:10px; border-radius:4px;">MP4</div>
                </div>
                <div class="vid-info">
                    <b style="display:block; margin-bottom:10px; color:#333;">{p_id}</b>
                    <a href="{v['secure_url']}" class="btn btn-jio" style="width:100%; margin-bottom:8px;">WATCH NOW</a>
                    <div class="action-grid">
                        <a href="{v['secure_url']}" download class="btn btn-green">DOWNLOAD</a>
                        <a href="/rename_page?old={p_id}" class="btn btn-orange">RENAME</a>
                    </div>
                    <a href="/delete_page?p={p_id}" class="btn" style="background:red; width:100%; margin-top:8px;">DELETE VIDEO</a>
                </div>
            </div>'''
    except: html += "<div class='card' style='padding:20px; text-align:center;'>No videos found. Check Cloudinary.</div>"

    if next_c: html += f'<div style="padding:10px;"><a href="/?next={next_c}" class="btn btn-jio" style="width:100%;">LOAD MORE</a></div>'
    return html

# --- ACTION ROUTES ---
@app.route("/process_upload", methods=["POST"])
def process_upload():
    thread = threading.Thread(target=background_upload, args=(request.form.get("url"), request.form.get("name")))
    thread.start()
    return f"{STYLE}<div class='card' style='padding:20px; text-align:center;'><h3>Upload Started!</h3><p>Video background mein save ho rahi hai. Site band kar dein.</p><a href='/' class='btn btn-jio'>WAPAS JAYEIN</a></div>"

@app.route("/rename_page")
def rename_page():
    return f'''{STYLE}<div class="card" style="padding:20px;"><h3>Rename: {request.args.get("old")}</h3>
        <form action="/confirm_rename">
            <input type="hidden" name="old" value="{request.args.get("old")}">
            <input name="new" placeholder="Enter New Name" required>
            <input name="pass" type="password" placeholder="Pass: 809047" required>
            <button class="btn btn-orange" style="width:100%;">RENAME NOW</button>
        </form></div>'''

@app.route("/confirm_rename")
def confirm_rename():
    if request.args.get("pass") == SECURE_PASS:
        cloudinary.uploader.rename(request.args.get("old"), request.args.get("new"), resource_type="video")
        return redirect("/")
    return "Wrong Password!"

@app.route("/delete_page")
def delete_page():
    return f'''{STYLE}<div class="card" style="padding:20px;"><h3>Delete Video?</h3>
        <p>{request.args.get("p")}</p>
        <form action="/confirm_delete">
            <input type="hidden" name="p" value="{request.args.get("p")}">
            <input name="pass" type="password" placeholder="Pass: 809047" required>
            <button class="btn" style="background:red; width:100%;">DELETE FOREVER</button>
        </form></div>'''

@app.route("/confirm_delete")
def confirm_delete():
    if request.args.get("pass") == SECURE_PASS:
        cloudinary.uploader.destroy(request.args.get("p"), resource_type="video")
        return redirect("/")
    return "Wrong Password!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
