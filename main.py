import os
import fitz  # PyMuPDF (PDF to Image conversion ke liye)
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import Flask, request, redirect, render_template_string, Response

app = Flask(__name__)

# --- Cloudinary Configuration ---
# Aapke purane credentials ka istemal kiya gaya hai
cloudinary.config(
    cloud_name="dawterffe", 
    api_key="258318685843824", 
    api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", 
    secure=True
)
ADMIN_PASSWORD = "809047"

# --- PDF TO JPG FAST CONVERSION LOGIC ---
def process_pdf_fast(file, pdf_name):
    pdf_path = f"temp_{pdf_name}.pdf"
    file.save(pdf_path)
    doc = fitz.open(pdf_path)
    
    for i in range(len(doc)):
        page = doc.load_page(i)
        # Matrix(2, 2) speed aur quality ka behtareen balance hai
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_path = f"{pdf_name}_p{i+1}.jpg"
        pix.save(img_path)
        
        # Cloudinary par upload (Folder: pdf_data)
        cloudinary.uploader.upload(
            img_path, 
            public_id=f"pdf_data/{pdf_name}/p{i+1}",
            tags=[pdf_name, "pdf_page"]
        )
        os.remove(img_path)
        
    doc.close()
    os.remove(pdf_path)

# --- HOME PAGE (JioTube Videos with Thumbnails & Search) ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    next_c = request.args.get('next')
    
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        all_v = res.get('resources', [])
        videos = [v for v in all_v if q in v.get('public_id', '').lower()]
        new_c = res.get('next_cursor')
    except:
        videos = []; new_c = None

    v_cards = ""
    for v in videos:
        # Video se thumbnail (JPG) link banana
        thumb = v['secure_url'].rsplit('.', 1)[0] + '.jpg'
        v_cards += f'''
        <div style="background:#fff;margin-bottom:20px;border-radius:12px;overflow:hidden;box-shadow:0 4px 8px rgba(0,0,0,0.1);border:1px solid #eee;">
            <img src="{thumb}" style="width:100%; height:auto; display:block; background:#f0f0f0;">
            <div style="padding:12px;">
                <b style="font-size:15px;color:#333;display:block;margin-bottom:10px;">{v['public_id']}</b>
                <div style="display:flex;gap:5px;">
                    <a href="{v['secure_url']}" style="flex:2;background:#0078d7;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-weight:bold;">PLAY</a>
                    <a href="/modify?task=rename&pid={v['public_id']}" style="flex:1;background:#ff9800;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;">NAME</a>
                    <a href="/modify?task=delete&pid={v['public_id']}" style="flex:1;background:#f44336;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;">DEL</a>
                </div>
            </div>
        </div>
        '''

    next_btn = f'<a href="/?next={new_c}&q={q}" style="display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;border-radius:10px;margin:10px;font-weight:bold;">LOAD MORE VIDEOS ↓</a>' if new_c else ""

    return f'''
    <body style="background:#f4f7f6;font-family:sans-serif;margin:0;padding-bottom:60px;">
        <div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #0078d7;position:sticky;top:0;z-index:1000;">
            <h2 style="margin:0;color:#0078d7;font-size:22px;">JioTube Pro</h2>
            <div style="margin-top:12px;display:flex;gap:8px;">
                <a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:10px;text-decoration:none;border-radius:6px;font-size:13px;font-weight:bold;">+ UPLOAD</a>
                <a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:6px;font-size:13px;font-weight:bold;">PDF VIEWER</a>
            </div>
            <form action="/" method="GET" style="margin-top:12px;display:flex;gap:5px;">
                <input type="text" name="q" placeholder="Search videos..." style="flex:1;padding:10px;border:1px solid #ddd;border-radius:6px;" value="{q}">
                <button style="background:#0078d7;color:#fff;border:none;padding:10px 18px;border-radius:6px;font-weight:bold;">OK</button>
            </form>
        </div>
        <div style="padding:12px;">{v_cards} {next_btn}</div>
    </body>
    '''

# --- PDF ARCHIVE PAGE ---
@app.route('/pdf_home')
def pdf_home():
    try:
        folders = cloudinary.api.subfolders("pdf_data")['folders']
    except:
        folders = []
    
    f_list = "".join([f'''
        <div style="background:#fff;margin-bottom:12px;padding:18px;border-radius:10px;box-shadow:0 2px 4px rgba(0,0,0,0.05);display:flex;justify-content:space-between;align-items:center;border-left:6px solid #e74c3c;">
            <a href="/view_pdf?name={f['name']}" style="text-decoration:none;color:#333;font-weight:bold;font-size:16px;">{f['name'].upper()}</a>
            <a href="/pdf_delete?name={f['name']}" onclick="return confirm('Delete this PDF?')" style="color:#f44336;text-decoration:none;font-size:13px;font-weight:bold;border:1px solid #f44336;padding:5px 10px;border-radius:5px;">DELETE</a>
        </div>
    ''' for f in folders])

    return f'''
    <body style="background:#f9f9f9;font-family:sans-serif;padding:20px;">
        <h2 style="text-align:center;color:#e74c3c;margin-bottom:25px;">PDF Archive</h2>
        <a href="/upload_pdf_page" style="display:block;background:#000;color:#fff;padding:18px;text-align:center;text-decoration:none;border-radius:12px;font-weight:bold;box-shadow:0 4px 6px rgba(0,0,0,0.2);">+ UPLOAD NEW PDF</a>
        <br><h4 style="color:#666;">SAVED DOCUMENTS:</h4>
        {f_list}
        <br><center><a href="/" style="color:#0078d7;text-decoration:none;font-weight:bold;">← Back to Home</a></center>
    </body>
    '''

# --- PDF UPLOAD WITH MEDIAFIRE PROGRESS BAR ---
@app.route('/upload_pdf_page')
def upload_pdf_page():
    return '''
    <body style="text-align:center;padding:25px;font-family:sans-serif;background:#f0f4f5;">
        <div style="background:#fff;padding:25px;border-radius:20px;box-shadow:0 10px 25px rgba(0,0,0,0.1);max-width:400px;margin:auto;margin-top:30px;">
            <h3 style="color:#0078d7;margin-bottom:25px;">Upload Document</h3>
            
            <form id="uploadForm">
                <input type="file" id="fileInput" name="file" accept=".pdf" style="margin-bottom:20px;width:100%;font-size:14px;"><br>
                <input type="text" id="pdfName" name="pdf_name" placeholder="Enter PDF Name" style="width:90%;padding:12px;margin-bottom:12px;border:1px solid #ccc;border-radius:8px;">
                <input type="password" id="adminPw" name="pw" placeholder="Admin Password" style="width:90%;padding:12px;margin-bottom:25px;border:1px solid #ccc;border-radius:8px;">
                
                <div id="progressWrapper" style="display:none; margin-bottom:25px; text-align:left;">
                    <div style="width:100%; background:#eee; border-radius:15px; height:18px; overflow:hidden; border:1px solid #ddd;">
                        <div id="progressBar" style="width:0%; background:linear-gradient(90deg, #0078d7, #00c6ff); height:100%; transition: width 0.4s;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:8px;">
                        <span id="statusText" style="font-size:12px; font-weight:bold; color:#0078d7;">Uploading: 0%</span>
                        <span id="speedText" style="font-size:11px; color:#999;">Stable Connection</span>
                    </div>
                </div>

                <button type="button" onclick="uploadFile()" id="upBtn" style="width:100%;padding:16px;background:#0078d7;color:#fff;border:none;border-radius:10px;font-weight:bold;font-size:16px;cursor:pointer;box-shadow:0 4px 10px rgba(0,120,215,0.3);">START UPLOAD</button>
            </form>
        </div>

        <script>
        function uploadFile() {
            var file = document.getElementById('fileInput').files[0];
            var name = document.getElementById('pdfName').value;
            var pw = document.getElementById('adminPw').value;
            
            if(!file || !name || !pw) { alert("Please fill all fields!"); return; }

            var formData = new FormData();
            formData.append("file", file);
            formData.append("pdf_name", name);
            formData.append("pw", pw);

            var xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener("progress", function(e) {
                if (e.lengthComputable) {
                    var percent = Math.round((e.loaded / e.total) * 100);
                    document.getElementById('progressWrapper').style.display = 'block';
                    document.getElementById('progressBar').style.width = percent + '%';
                    document.getElementById('statusText').innerText = "Uploading: " + percent + "%";
                    document.getElementById('upBtn').disabled = true;
                    document.getElementById('upBtn').innerText = "DO NOT CLOSE...";
                }
            });

            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    document.getElementById('statusText').innerText = "Converting to JPG... ⚡";
                    document.getElementById('progressBar').style.background = "#28a745";
                    setTimeout(function(){ window.location.href = "/pdf_home"; }, 3000);
                }
            };

            xhr.open("POST", "/do_pdf_upload", true);
            xhr.send(formData);
        }
        </script>
    </body>
    '''

@app.route('/do_pdf_upload', methods=['POST'])
def do_pdf_upload():
    if request.form.get('pw') == ADMIN_PASSWORD:
        file = request.files.get('file')
        p_name = request.form.get('pdf_name').replace(' ','_')
        if file:
            process_pdf_fast(file, p_name)
    return "OK"

# --- PDF VIEWING (10 IMAGES PER PAGE + HQ DOWNLOAD) ---
@app.route('/view_pdf')
def view_pdf():
    name = request.args.get('name')
    cursor = request.args.get('next')
    
    res = cloudinary.api.resources_by_tag(name, max_results=10, next_cursor=cursor)
    pages = sorted(res['resources'], key=lambda x: x['public_id'])
    new_c = res.get('next_cursor')

    img_html = ""
    for i, p in enumerate(pages):
        # High Quality Download link
        download_url = p['secure_url'].replace("/upload/", "/upload/fl_attachment/")
        img_html += f'''
        <div style="background:#fff;margin-bottom:25px;border-bottom:6px solid #e74c3c;box-shadow:0 4px 10px rgba(0,0,0,0.3);">
            <img src="{p['secure_url']}" style="width:100%;display:block;min-height:200px;">
            <div style="padding:12px;display:flex;justify-content:space-between;align-items:center;background:#f8f9fa;border-top:1px solid #ddd;">
                <span style="font-weight:bold;color:#333;font-size:14px;">📄 PAGE {i+1}</span>
                <a href="{download_url}" style="background:#28a745;color:#fff;padding:10px 20px;text-decoration:none;border-radius:6px;font-size:12px;font-weight:bold;">DOWNLOAD HQ</a>
            </div>
        </div>
        '''
    
    next_btn = f'''
        <a href="/view_pdf?name={name}&next={new_c}" style="display:block;background:#e74c3c;color:#fff;padding:18px;text-align:center;text-decoration:none;font-weight:bold;margin:15px;border-radius:12px;box-shadow:0 4px 8px rgba(231,76,60,0.3);">
            LOAD NEXT 10 PAGES →
        </a>''' if new_c else ""

    return f'''
    <body style="background:#111;margin:0;font-family:sans-serif;padding-bottom:40px;">
        <div style="background:#fff;padding:12px;text-align:center;position:sticky;top:0;z-index:1000;display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #e74c3c;">
            <a href="/pdf_home" style="color:#e74c3c;text-decoration:none;font-weight:bold;padding:5px 10px;">← BACK</a>
            <b style="font-size:16px;">{name.upper()}</b>
            <span style="width:40px;"></span>
        </div>
        <div style="padding:5px;">
            {img_html}
            {next_btn}
        </div>
        <div style="text-align:center;padding:20px;">
            <a href="/pdf_home" style="color:#999;text-decoration:none;font-size:14px;">End of results. Back to Archive?</a>
        </div>
    </body>
    '''

# --- ADMIN VIDEO MANAGEMENT ---
@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return '''
        <div style="text-align:center;padding:50px;font-family:sans-serif;">
            <h2>Upload Video</h2>
            <form action="/do_up" method="POST" enctype="multipart/form-data">
                <input type="file" name="file" required><br><br>
                <input type="text" name="vname" placeholder="Video Title" style="padding:10px;width:80%;"><br><br>
                <button style="padding:15px 30px;background:#28a745;color:#fff;border:none;border-radius:8px;font-weight:bold;">UPLOAD TO CLOUD</button>
            </form>
        </div>'''
    return '''
    <div style="text-align:center;padding:50px;font-family:sans-serif;">
        <form method="POST">
            <input type="password" name="pw" placeholder="Admin Password" style="padding:12px;"><br><br>
            <button style="padding:10px 25px;">LOGIN</button>
        </form>
    </div>'''

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file')
    vname = request.form.get('vname', 'video').replace(' ','_')
    if file:
        cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    t = request.args.get('task')
    p = request.args.get('pid')
    return render_template_string('''
        <body style="text-align:center;padding:50px;font-family:sans-serif;">
            <h2 style="color:red;">{{t.upper()}}</h2>
            <p>Target: {{p}}</p>
            <form action="/confirm" method="POST">
                <input type="hidden" name="pid" value="{{p}}">
                <input type="hidden" name="task" value="{{t}}">
                {% if t=="rename" %}
                    <input type="text" name="new" placeholder="New Name" style="padding:10px;width:80%;"><br><br>
                {% endif %}
                <input type="password" name="pw" placeholder="Admin Password" style="padding:10px;width:80%;"><br><br>
                <button style="padding:15px 40px;background:#000;color:#fff;border:none;border-radius:10px;">CONFIRM</button>
            </form>
        </body>
    ''', t=t, p=p)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task')
        p = request.form.get('pid')
        if t == 'rename':
            cloudinary.uploader.rename(p, request.form.get('new').replace(' ','_'), resource_type="video")
        elif t == 'delete':
            cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

@app.route('/pdf_delete')
def pdf_delete():
    name = request.args.get('name')
    # Delete all images with this tag
    cloudinary.api.delete_resources_by_tag(name)
    return redirect('/pdf_home')

if __name__ == '__main__':
    # Render ke liye port binding
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
