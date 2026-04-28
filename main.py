import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
import threading
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Cloudinary Config
cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

def process_pdf_in_background(pdf_path, pdf_name):
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Matrix 3.0 = Ultra High Definition (Best for Text)
            pix = page.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))
            # PNG use kar rahe hain taaki quality bilkul na gire
            img_path = f"p{i+1}_{pdf_name}.png"
            pix.save(img_path)
            
            # Direct Upload with Zero Compression
            cloudinary.uploader.upload(
                img_path, 
                public_id=f"p{i+1}", 
                folder=f"pdf_data/{pdf_name}", 
                resource_type="image",
                lossless=True
            )
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
        if os.path.exists(pdf_path): os.remove(pdf_path)
    except Exception as e:
        print(f"Error: {e}")

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=15, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_cards = "".join([f"""<div style="background:#fff;margin-bottom:20px;border-radius:12px;overflow:hidden;box-shadow:0 4px 8px rgba(0,0,0,0.1);"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;" loading="lazy"><div style="padding:12px;"><b>{v["public_id"]}</b><div style="display:flex;gap:5px;margin-top:10px;"><a href="{v["secure_url"]}" style="flex:2;background:#0078d7;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;">PLAY</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;">DEL</a></div></div></div>""" for v in videos])
    return f"""<body style="background:#f4f7f6;font-family:sans-serif;margin:0;"><div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #0078d7;position:sticky;top:0;z-index:1000;"><h2>JioTube Pro</h2><div style="display:flex;gap:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">+ VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">PDF VIEWER</a></div></div><div style="padding:12px;">{v_cards} {"<a href=\"/?next="+new_c+"&q="+q+"\" style=\"display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;border-radius:10px;\">LOAD MORE ↓</a>" if new_c else ""}</div></body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    filtered = [f for f in folders if q in f["name"].lower()]
    f_list = "".join([f"""<div style="background:#fff;margin-bottom:12px;padding:15px;border-radius:10px;border-left:6px solid #e74c3c;display:flex;justify-content:space-between;align-items:center;"><a href="/view_pdf?name={f["name"]}" style="text-decoration:none;color:#333;font-weight:bold;">{f["name"].upper()}</a><div style="display:flex;gap:5px;"><a href="/modify?task=rename&pid={f["name"]}&type=pdf" style="background:orange;color:#fff;padding:5px 10px;text-decoration:none;border-radius:5px;font-size:12px;">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="background:red;color:#fff;padding:5px 10px;text-decoration:none;border-radius:5px;font-size:12px;">DEL</a></div></div>""" for f in filtered])
    return f"""<body style="background:#f9f9f9;font-family:sans-serif;padding:0;"><div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #e74c3c;position:sticky;top:0;z-index:1000;"><h2>PDF Archive</h2><div style="display:flex;gap:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">BACK</a><a href="/upload_pdf_page" style="flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">+ NEW</a></div></div><div style="padding:15px;">{f_list}</div></body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); c = request.args.get("next")
    ts = int(time.time())
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        nc = res.get("next_cursor")
    except: pages = []; nc = None
    h = "".join([f"""<div style="margin-bottom:25px;background:#fff;text-align:center;"><img src="{p["secure_url"]}?v={ts}" style="width:100%;display:block;"><div style="padding:10px;background:#eee;"><a href="{p["secure_url"].replace("/upload/","/upload/fl_attachment/")}" style="color:#fff;text-decoration:none;font-size:12px;background:#28a745;padding:8px 20px;border-radius:5px;font-weight:bold;">DOWNLOAD PNG</a></div></div>""" for p in pages])
    return f"""<body style="background:#000;margin:0;"><div style="background:#fff;padding:10px;text-align:center;position:sticky;top:0;display:flex;justify-content:space-between;z-index:1000;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;font-weight:bold;">← BACK</a><b style="font-size:14px;">{name.upper()}</b><span></span></div>{h}{f"<a href=\"/view_pdf?name="+name+"&next="+nc+"\" style=\"display:block;background:#e74c3c;color:#fff;padding:20px;text-align:center;text-decoration:none;font-weight:bold;\">LOAD NEXT PAGES →</a>" if nc else ""}</body>"""

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("pdf_name").replace(" ","_")
        if f:
            pdf_path = f"temp_{int(time.time())}.pdf"
            f.save(pdf_path)
            threading.Thread(target=process_pdf_in_background, args=(pdf_path, n)).start()
            return "OK"
    return "Error"

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return """<body style="text-align:center;padding:25px;font-family:sans-serif;background:#f0f4f5;"><div style="background:#fff;padding:25px;border-radius:20px;max-width:400px;margin:auto;"><h3>Upload Ultra HD PDF</h3><p style="font-size:12px;color:#e74c3c;font-weight:bold;">Warning: High Matrix (3.0) will take more time to process.</p><form id="uF"><input type="file" id="fI" accept=".pdf" style="margin-bottom:20px;"><br><input type="text" id="pN" placeholder="PDF Name" style="width:90%;padding:10px;margin-bottom:10px;"><input type="password" id="pw" placeholder="Pass" style="width:90%;padding:10px;margin-bottom:20px;"><button type="button" onclick="upL()" id="uB" style="width:100%;padding:15px;background:#e74c3c;color:#fff;border:none;border-radius:10px;font-weight:bold;">START ULTRA HD UPLOAD</button></form></div><script>function upL(){var f=document.getElementById("fI").files[0],n=document.getElementById("pN").value,p=document.getElementById("pw").value;if(!f||!n||!p)return alert("Fill all!");var d=new FormData();d.append("file",f);d.append("pdf_name",n);d.append("pw",p);document.getElementById("uB").innerText="Uploading...";document.getElementById("uB").disabled=true;var x=new XMLHttpRequest();x.onreadystatechange=function(){if(x.readyState==4&&x.status==200){alert("Uploaded! Please wait 3-5 minutes for Ultra HD processing.");window.location.href="/pdf_home"}};x.open("POST","/do_pdf_upload",true);x.send(d);}</script></body>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
