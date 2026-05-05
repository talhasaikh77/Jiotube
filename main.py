import os, time, cloudinary, cloudinary.uploader, cloudinary.api
from flask import Flask, request, redirect, render_template_string, session, send_file
from pytubefix import YouTube
import threading

app = Flask(__name__)
app.secret_key = "jiotube_v102_background_master"

# --- MASTER CONFIG ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
SECURE_PASS = "809047"

STYLE = """<style>
    :root { --jio: #0072ef; --yt: #ff0000; }
    body { margin:0; font-family: sans-serif; background: #f0f2f5; padding-bottom: 20px; }
    .header { background: var(--jio); padding:15px; text-align:center; color:#fff; font-weight:bold; position:sticky; top:0; z-index:1000; }
    .card { background: #fff; margin:12px; border-radius:10px; overflow:hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border: 1px solid #ddd; padding:10px; }
    .btn { padding:10px; border-radius:6px; text-decoration:none; color:#fff; font-size:12px; text-align:center; font-weight:bold; border:none; display:block; cursor:pointer; }
    .btn-jio { background: var(--jio); } .btn-yt { background: var(--yt); }
    input { width:100%; padding:12px; margin:5px 0; border:1px solid #ccc; border-radius:6px; box-sizing:border-box; }
    .thumb { width:100%; height:150px; object-fit:cover; background:#000; }
</style>"""

# --- BACKGROUND UPLOAD LOGIC ---
def background_upload(url, custom_name):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        # Upload to Cloudinary with Jio Bharat Transformations
        cloudinary.uploader.upload(stream.url, 
            resource_type="video",
            public_id=custom_name,
            folder="JioTube_Videos",
            eager=[
                {"width": 320, "height": 240, "crop": "pad", "video_codec": "h264", "bit_rate": "300k"},
                {"format": "mp4", "transformation": "sp_450p"} 
            ],
            eager_async=True
        )
    except Exception as e:
        print(f"Background Error: {e}")

# --- HOME PAGE UI ---
@app.route("/")
def index():
    q = request.args.get("q")
    curs = request.args.get("next")
    
    # 1. Upload Panel (At the top)
    up_panel = f'''<div class="card">
        <h3 style="margin-top:0; color:var(--jio);">Upload to Cloud</h3>
        <form action="/process_upload" method="POST">
            <input name="url" placeholder="Paste Video/YT Link" required>
            <input name="name" placeholder="Save As (Video Name)" required>
            <button class="btn btn-jio" style="width:100%;">START CLOUD UPLOAD</button>
        </form>
    </div>'''

    # 2. Search Engine
    search_bar = f'''<div class="card">
        <form action="/" method="GET">
            <input name="q" placeholder="Search uploaded videos..." value="{q if q else ''}">
            <button class="btn btn-yt" style="width:100%;">FIND VIDEO</button>
        </form>
    </div>'''

    # 3. Video List (Card View)
    try:
        search_params = {"resource_type": "video", "type": "upload", "prefix": "JioTube_Videos/", "max_results": 10, "next_cursor": curs}
        res = cloudinary.api.resources(**search_params)
        vids = res.get("resources", [])
        next_c = res.get("next_cursor")
        
        # Filtering if search query exists
        if q:
            vids = [v for v in vids if q.lower() in v['public_id'].lower()]

        v_html = ""
        for v in vids:
            clean_name = v['public_id'].replace("JioTube_Videos/", "")
            v_html += f'''<div class="card" style="padding:0; margin-bottom:15px;">
                <img src="{v['secure_url'].rsplit('.', 1)[0]}.jpg" class="thumb">
                <div style="padding:10px;">
                    <b style="font-size:14px;">{clean_name}</b>
                    <div style="display:flex; gap:5px; margin-top:10px;">
                        <a href="{v['secure_url']}" class="btn btn-jio" style="flex:1;">WATCH</a>
                        <a href="{v['secure_url']}" download class="btn" style="background:#28a745; flex:1;">DOWNLOAD</a>
                        <a href="/delete?p={v['public_id']}" class="btn" style="background:red; width:40px;">DEL</a>
                    </div>
                </div>
            </div>'''
    except:
        v_html = "<p style='text-align:center;'>No videos found or Error.</p>"
        next_c = None

    n_btn = f'<div style="padding:10px;"><a href="/?next={next_c}" class="btn btn-jio">LOAD MORE</a></div>' if next_c else ""

    return f"{STYLE}<div class='header'>JIOTUBE CLOUD</div>{up_panel}{search_bar}{v_html}{n_btn}"

# --- ROUTES ---
@app.route("/process_upload", methods=["POST"])
def process_upload():
    url = request.form.get("url")
    name = request.form.get("name")
    # Threading use kar rahe hain taaki site band karne par bhi upload chalta rahe
    thread = threading.Thread(target=background_upload, args=(url, name))
    thread.start()
    return f"{STYLE}<div class='card'><h3>Upload Started!</h3><p>Aap site band kar sakte hain. Video background mein Cloudinary par save ho rahi hai.</p><a href='/' class='btn btn-jio'>Back to Home</a></div>"

@app.route("/delete")
def delete():
    p = request.args.get("p")
    # Security check to prevent accidental delete
    return f'''{STYLE}<div class="card"><h3>Delete {p}?</h3>
        <form action="/confirm_delete">
            <input type="hidden" name="p" value="{p}">
            <input name="pass" type="password" placeholder="Enter 809047 to Delete" required>
            <button class="btn" style="background:red; width:100%;">CONFIRM DELETE</button>
        </form></div>'''

@app.route("/confirm_delete")
def confirm_delete():
    p, pw = request.args.get("p"), request.args.get("pass")
    if pw == SECURE_PASS:
        cloudinary.uploader.destroy(p, resource_type="video")
        return redirect("/")
    return "Wrong Password"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
