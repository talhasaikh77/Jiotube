import os
import fitz  # PyMuPDF
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import Flask, request, redirect, render_template_string, Response

app = Flask(__name__)

# --- Config ---
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

# --- FAST PDF CONVERTER ---
def process_pdf_fast(file, pdf_name):
    pdf_path = f"temp_{pdf_name}.pdf"
    file.save(pdf_path)
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_path = f"{pdf_name}_p{i+1}.jpg"
        pix.save(img_path)
        cloudinary.uploader.upload(img_path, 
                                 public_id=f"pdf_data/{pdf_name}/p{i+1}",
                                 tags=[pdf_name, "pdf_page"])
        os.remove(img_path)
    doc.close()
    os.remove(pdf_path)

# --- HOME PAGE (Thumbnails Back!) ---
@app.route('/')
def index():
    q = request.args.get('q', '').strip().lower()
    next_c = request.args.get('next')
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get('resources', []) if q in v.get('public_id', '').lower()]
        new_c = res.get('next_cursor')
    except: videos = []; new_c = None

    v_cards = ""
    for v in videos:
        # Thumbnail URL generate karna
        thumb = v['secure_url'].rsplit('.', 1)[0] + '.jpg'
        v_cards += f'''
        <div style="background:#fff;margin-bottom:20px;border-radius:10px;overflow:hidden;box-shadow:0 2px 5px #ccc;">
            <img src="{thumb}" style="width:100%; height:auto; display:block; background:#eee;">
            <div style="padding:12px;">
                <b style="font-size:15px;display:block;margin-bottom:10px;">{v['public_id']}</b>
                <div style="display:flex;gap:5px;">
                    <a href="{v['secure_url']}" style="flex:2;background:#0078d7;color:#fff;text-align:center;padding:10px;text-decoration:none;border-radius:5px;font-weight:bold;">PLAY</a>
                    <a href="/modify?task=rename&pid={v['public_id']}" style="flex:1;background:orange;color:#fff;text-align:center;padding:10px;text-decoration:none;border-radius:5px;font-size:11px;">NAME</a>
                    <a href="/modify?task=delete&pid={v['public_id']}" style="flex:1;background:red;color:#fff;text-align:center;padding:10px;text-decoration:none;border-radius:5px;font-size:11px;">DEL</a>
                </div>
            </div>
        </div>
        '''

    next_btn = f'<a href="/?next={new_c}&q={q}" style="display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;border-radius:10px;margin:10px;">NEXT VIDEOS →</a>' if new_c else ""

    return f'''
    <body style="background:#f4f4f4;font-family:sans-serif;margin:0;padding-bottom:50px;">
        <div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #0078d7;position:sticky;top:0;z-index:100;">
            <h2 style="margin:0;color:#0078d7;">JioTube Pro</h2>
            <div style="margin-top:10px;display:flex;gap:5px;">
                <a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:10px;text-decoration:none;border-radius:5px;font-size:12px;">+ VIDEO</a>
                <a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:5px;font-size:12px;">PDF VIEWER</a>
            </div>
            <form action="/" method="GET" style="margin-top:10px;display:flex;">
                <input type="text" name="q" placeholder="Search..." style="flex:1;padding:8px;border:1px solid #ddd;" value="{q}">
                <button style="background:#0078d7;color:#fff;border:none;padding:8px 15px;">OK</button>
            </form>
        </div>
        <div style="padding:10px;">{v_cards} {next_btn}</div>
    </body>
    '''

# --- PDF UPLOAD PAGE (With Loader) ---
@app.route('/upload_pdf_page')
def upload_pdf_page():
    return '''
    <body style="text-align:center;padding:30px;font-family:sans-serif;">
        <div id="loader" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,255,255,0.95);z-index:1000;">
            <div style="margin-top:50%;">
                <div style="width:50px;height:50px;border:5px solid #f3f3f3;border-top:5px solid #e74c3c;border-radius:50%;animation:spin 1s linear infinite;margin:auto;"></div>
                <h3 style="color:#e74c3c;margin-top:20px;">Processing PDF...</h3>
                <p>Converting to High Quality Images</p>
            </div>
        </div>
        <style>@keyframes spin {0%{transform:rotate(0deg);} 100%{transform:rotate(360deg);}}</style>
        <h3>Upload PDF</h3>
        <form action="/do_pdf_upload" method="POST" enctype="multipart/form-data" onsubmit="document.getElementById('loader').style.display='block';">
            <input type="file" name="file" accept=".pdf" required><br><br>
            <input type="text" name="pdf_name" placeholder="PDF Name" required style="width:80%;padding:10px;"><br><br>
            <input type="password" name="pw" placeholder="Admin Pass" required style="width:80%;padding:10px;"><br><br>
            <button style="width:90%;padding:15px;background:#e74c3c;color:#fff;border:none;border-radius:10px;font-weight:bold;">START CONVERSION</button>
        </form>
    </body>
    '''

# --- Baki Routes (pdf_home, view_pdf, confirm, etc.) ---
@app.route('/pdf_home')
def pdf_home():
    try: folders = cloudinary.api.subfolders("pdf_data")['folders']
    except: folders = []
    f_list = "".join([f'<div style="background:#fff;margin-bottom:10px;padding:15px;border-radius:8px;box-shadow:0 1px 3px #ccc;display:flex;justify-content:space-between;"><a href="/view_pdf?name={f["name"]}" style="text-decoration:none;color:#333;font-weight:bold;">{f["name"]}</a><a href="/pdf_delete?name={f["name"]}" style="color:red;text-decoration:none;font-size:12px;">Delete</a></div>' for f in folders])
    return f'<body style="background:#f9f9f9;font-family:sans-serif;padding:15px;"><h2 style="text-align:center;color:#e74c3c;">PDF Archive</h2><a href="/upload_pdf_page" style="display:block;background:#000;color:#fff;padding:15px;text-align:center;text-decoration:none;border-radius:10px;font-weight:bold;">+ NEW PDF</a><br>{f_list}</body>'

@app.route('/view_pdf')
def view_pdf():
    name = request.args.get('name'); cursor = request.args.get('next')
    res = cloudinary.api.resources_by_tag(name, max_results=10, next_cursor=cursor)
    pages = sorted(res['resources'], key=lambda x: x['public_id'])
    new_c = res.get('next_cursor')
    img_html = "".join([f'<div style="margin-bottom:20px;background:#fff;border-bottom:4px solid #e74c3c;"><img src="{p["secure_url"]}" style="width:100%;"><div style="padding:10px;text-align:center;background:#eee;"><a href="{p["secure_url"].replace("/upload/","/upload/fl_attachment/")}" style="background:#28a745;color:#fff;padding:8px 20px;text-decoration:none;border-radius:5px;font-size:12px;font-weight:bold;">DOWNLOAD HQ</a></div></div>' for p in pages])
    next_btn = f'<a href="/view_pdf?name={name}&next={new_c}" style="display:block;background:#e74c3c;color:#fff;padding:15px;text-align:center;text-decoration:none;border-radius:10px;margin:10px;">NEXT 10 PAGES →</a>' if new_c else ""
    return f'<body style="background:#111;margin:0;font-family:sans-serif;"><div style="background:#fff;padding:10px;text-align:center;position:sticky;top:0;z-index:100;"><b>{name.upper()}</b> | <a href="/pdf_home" style="color:red;text-decoration:none;">EXIT</a></div>{img_html}{next_btn}</body>'

@app.route('/do_pdf_upload', methods=['POST'])
def do_pdf_upload():
    if request.form.get('pw') == ADMIN_PASSWORD:
        file = request.files.get('file'); p_name = request.form.get('pdf_name').replace(' ','_')
        if file: process_pdf_fast(file, p_name)
    return redirect('/pdf_home')

@app.route('/admin_upload', methods=['GET', 'POST'])
def admin_upload():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PASSWORD:
        return '<form action="/do_up" method="POST" enctype="multipart/form-data" style="padding:20px;"><input type="file" name="file"><br><br><input type="text" name="vname" placeholder="Video Name"><br><br><button>UPLOAD</button></form>'
    return '<form method="POST" style="padding:20px;"><input type="password" name="pw" placeholder="Pass"><br><br><button>Login</button></form>'

@app.route('/do_up', methods=['POST'])
def do_up():
    file = request.files.get('file'); vname = request.form.get('vname', 'video').replace(' ','_')
    if file: cloudinary.uploader.upload(file, resource_type="video", public_id=vname)
    return redirect('/')

@app.route('/modify')
def modify():
    t = request.args.get('task'); p = request.args.get('pid')
    return render_template_string('<form action="/confirm" method="POST" style="padding:40px;text-align:center;"><h3>{{t.upper()}}</h3><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name"><br><br>{% endif %}<input type="password" name="pw" placeholder="Admin Pass"><br><br><button>CONFIRM</button></form>', t=t, p=p)

@app.route('/confirm', methods=['POST'])
def confirm():
    if request.form.get('pw') == ADMIN_PASSWORD:
        t = request.form.get('task'); p = request.form.get('pid')
        if t == 'rename': cloudinary.uploader.rename(p, request.form.get('new').replace(' ','_'), resource_type="video")
        elif t == 'delete': cloudinary.uploader.destroy(p, resource_type="video")
    return redirect('/')

@app.route('/pdf_delete')
def pdf_delete():
    cloudinary.api.delete_resources_by_tag(request.args.get('name'))
    return redirect('/pdf_home')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
