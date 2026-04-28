import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
import time
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

cloudinary.config(cloud_name="dawterffe", api_key="258318685843824", api_secret="NxTNXBeLmupMQ0S1FOPU9t6bcjo", secure=True)
ADMIN_PASSWORD = "809047"

def process_pdf_fast(file, pdf_name):
    try:
        pdf_path = f"temp_{pdf_name}.pdf"
        file.save(pdf_path)
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
            img_path = f"p{i+1}_{pdf_name}.jpg"
            pix.save(img_path)
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", tags=[pdf_name, "pdf_page"], resource_type="image")
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
        os.remove(pdf_path)
        return True
    except: return False

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=15, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_cards = "".join([f"""<div style="background:#fff;margin-bottom:20px;border-radius:12px;overflow:hidden;box-shadow:0 4px 8px rgba(0,0,0,0.1);"><img src="{v["secure_url"].rsplit(".", 1)[0]}.jpg" style="width:100%;"><div style="padding:12px;"><b>{v["public_id"]}</b><div style="display:flex;gap:5px;margin-top:10px;"><a href="{v["secure_url"]}" style="flex:2;background:#0078d7;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;">PLAY</a><a href="/modify?task=rename&pid={v["public_id"]}&type=video" style="flex:1;background:orange;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;">NAME</a><a href="/modify?task=delete&pid={v["public_id"]}&type=video" style="flex:1;background:red;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;">DEL</a></div></div></div>""" for v in videos])
    return f"""<body style="background:#f4f7f6;font-family:sans-serif;margin:0;"><div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #0078d7;position:sticky;top:0;z-index:1000;"><h2>JioTube Pro</h2><div style="display:flex;gap:8px;"><a href="/admin_upload" style="flex:1;background:#28a745;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">+ VIDEO</a><a href="/pdf_home" style="flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">PDF VIEWER</a></div><form action="/" method="GET" style="margin-top:10px;display:flex;gap:5px;"><input type="text" name="q" placeholder="Search..." style="flex:1;padding:8px;" value="{q}"><button style="padding:8px 15px;background:#0078d7;color:#fff;border:none;">OK</button></form></div><div style="padding:12px;">{v_cards} {"<a href=\"/?next="+new_c+"&q="+q+"\" style=\"display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;border-radius:10px;\">LOAD MORE ↓</a>" if new_c else ""}</div></body>"""

@app.route("/pdf_home")
def pdf_home():
    q = request.args.get("q", "").strip().lower()
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    filtered = [f for f in folders if q in f["name"].lower()]
    f_list = "".join([f"""<div style="background:#fff;margin-bottom:12px;padding:15px;border-radius:10px;border-left:6px solid #e74c3c;display:flex;justify-content:space-between;align-items:center;"><a href="/view_pdf?name={f["name"]}" style="text-decoration:none;color:#333;font-weight:bold;">{f["name"].upper()}</a><div style="display:flex;gap:5px;"><a href="/modify?task=rename&pid={f["name"]}&type=pdf" style="background:orange;color:#fff;padding:5px 10px;text-decoration:none;border-radius:5px;font-size:12px;">NAME</a><a href="/modify?task=delete&pid={f["name"]}&type=pdf" style="background:red;color:#fff;padding:5px 10px;text-decoration:none;border-radius:5px;font-size:12px;">DEL</a></div></div>""" for f in filtered])
    return f"""<body style="background:#f9f9f9;font-family:sans-serif;padding:0;"><div style="background:#fff;padding:15px;text-align:center;border-bottom:3px solid #e74c3c;position:sticky;top:0;z-index:1000;"><h2>PDF Archive</h2><div style="display:flex;gap:8px;"><a href="/" style="flex:1;background:#333;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">BACK</a><a href="/upload_pdf_page" style="flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:6px;">+ NEW</a></div><form action="/pdf_home" method="GET" style="margin-top:10px;display:flex;gap:5px;padding:0 10px;"><input type="text" name="q" placeholder="Search..." style="flex:1;padding:8px;" value="{q}"><button style="padding:8px 15px;background:#e74c3c;color:#fff;border:none;">OK</button></form></div><div style="padding:15px;">{f_list}</div></body>"""

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name"); c = request.args.get("next")
    try:
        res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{name}/", max_results=10, next_cursor=c)
        pages = sorted(res.get("resources", []), key=lambda x: x["public_id"])
        nc = res.get("next_cursor")
    except: pages = []; nc = None
    # Black screen fix: f_auto, q_auto aur version timestamp add kiya hai
    ts = int(time.time())
    h = ""
    for p in pages:
        opt_url = p["secure_url"].replace("/upload/", f"/upload/f_auto,q_auto/v{ts}/")
        h += f"""<div style="margin-bottom:15px;background:#000;text-align:center;"><img src="{opt_url}" style="width:100%;min-height:200px;display:block;"><div style="padding:10px;"><a href="{p["secure_url"].replace("/upload/","/upload/fl_attachment/")}" style="color:#fff;text-decoration:none;font-size:12px;background:#28a745;padding:5px 10px;border-radius:4px;">DOWNLOAD HQ</a></div></div>"""
    return f"""<body style="background:#111;margin:0;"><div style="background:#fff;padding:10px;text-align:center;position:sticky;top:0;display:flex;justify-content:space-between;z-index:1000;"><a href="/pdf_home" style="text-decoration:none;color:#e74c3c;">← BACK</a><b>{name.upper()}</b><span></span></div>{h}{f"<a href=\"/view_pdf?name="+name+"&next="+nc+"\" style=\"display:block;background:#e74c3c;color:#fff;padding:15px;text-align:center;text-decoration:none;\">NEXT 10 PAGES →</a>" if nc else ""}</body>"""

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid"); tp = request.args.get("type")
    return render_template_string("""<body style="text-align:center;padding:50px;font-family:sans-serif;"><h3>{{t.upper()}}</h3><form action="/confirm" method="POST"><input type="hidden" name="pid" value="{{p}}"><input type="hidden" name="task" value="{{t}}"><input type="hidden" name="type" value="{{tp}}">{% if t=="rename" %}<input type="text" name="new" placeholder="New Name" style="width:80%;padding:10px;"><br><br>{% endif %}<input type="password" name="pw" placeholder="Pass" style="width:80%;padding:10px;"><br><br><button style="padding:10px 40px;background:#333;color:#fff;">OK</button></form></body>""", t=t, p=p, tp=tp)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t = request.form.get("task"); p = request.form.get("pid"); tp = request.form.get("type")
        if tp == "video":
            if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
            elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
            return redirect("/")
        else:
            if t == "rename":
                new_n = request.form.get("new").replace(" ","_")
                res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{p}/")
                for r in res.get("resources", []):
                    old_id = r["public_id"]
                    new_id = old_id.replace(f"pdf_data/{p}/", f"pdf_data/{new_n}/")
                    cloudinary.uploader.rename(old_id, new_id)
            elif t == "delete":
                res = cloudinary.api.resources(type="upload", prefix=f"pdf_data/{p}/")
                ids = [r["public_id"] for r in res.get("resources", [])]
                if ids: cloudinary.api.delete_resources(ids)
            return redirect("/pdf_home")
    return "Wrong Password"

@app.route("/admin_upload")
def admin_upload():
    return """<body style="text-align:center;padding:25px;font-family:sans-serif;background:#f0f4f5;"><div style="background:#fff;padding:25px;border-radius:20px;max-width:400px;margin:auto;"><h3>Upload Video</h3><form id="uF"><input type="file" id="fI" accept="video/*" style="margin-bottom:20px;"><br><input type="text" id="vN" placeholder="Video Name" style="width:90%;padding:10px;margin-bottom:10px;"><input type="password" id="pw" placeholder="Pass" style="width:90%;padding:10px;margin-bottom:20px;"><div id="pW" style="display:none;margin-bottom:20px;"><div style="width:100%;background:#eee;height:15px;border-radius:10px;overflow:hidden;"><div id="pB" style="width:0%;background:#28a745;height:100%;"></div></div><p id="sT" style="font-size:12px;">0%</p></div><button type="button" onclick="upL()" id="uB" style="width:100%;padding:15px;background:#28a745;color:#fff;border:none;border-radius:10px;">START UPLOAD</button></form></div><script>function upL(){var f=document.getElementById("fI").files[0],n=document.getElementById("vN").value,p=document.getElementById("pw").value;if(!f||!n||!p)return alert("Fill all!");var d=new FormData();d.append("file",f);d.append("vname",n);d.append("pw",p);var x=new XMLHttpRequest();x.upload.addEventListener("progress",function(e){if(e.lengthComputable){var pc=Math.round((e.loaded/e.total)*100);document.getElementById("pW").style.display="block";document.getElementById("pB").style.width=pc+"%";document.getElementById("sT").innerText="Uploading: "+pc+"%";document.getElementById("uB").disabled=true;}});x.onreadystatechange=function(){if(x.readyState==4&&x.status==200){window.location.href="/"}};x.open("POST","/do_up",true);x.send(d);}</script></body>"""

@app.route("/do_up", methods=["POST"])
def do_up():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); v = request.form.get("vname", "video").replace(" ","_")
        if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
    return "OK"

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return """<body style="text-align:center;padding:25px;font-family:sans-serif;background:#f0f4f5;"><div style="background:#fff;padding:25px;border-radius:20px;max-width:400px;margin:auto;"><h3>Upload PDF</h3><form id="uF"><input type="file" id="fI" accept=".pdf" style="margin-bottom:20px;"><br><input type="text" id="pN" placeholder="PDF Name" style="width:90%;padding:10px;margin-bottom:10px;"><input type="password" id="pw" placeholder="Pass" style="width:90%;padding:10px;margin-bottom:20px;"><div id="pW" style="display:none;margin-bottom:20px;"><div style="width:100%;background:#eee;height:15px;border-radius:10px;overflow:hidden;"><div id="pB" style="width:0%;background:#0078d7;height:100%;"></div></div><p id="sT" style="font-size:12px;">0%</p></div><button type="button" onclick="upL()" id="uB" style="width:100%;padding:15px;background:#0078d7;color:#fff;border:none;border-radius:10px;">START UPLOAD</button></form></div><script>function upL(){var f=document.getElementById("fI").files[0],n=document.getElementById("pN").value,p=document.getElementById("pw").value;if(!f||!n||!p)return alert("Fill all!");var d=new FormData();d.append("file",f);d.append("pdf_name",n);d.append("pw",p);var x=new XMLHttpRequest();x.upload.addEventListener("progress",function(e){if(e.lengthComputable){var pc=Math.round((e.loaded/e.total)*100);document.getElementById("pW").style.display="block";document.getElementById("pB").style.width=pc+"%";document.getElementById("sT").innerText="Uploading: "+pc+"%";document.getElementById("uB").disabled=true;}});x.onreadystatechange=function(){if(x.readyState==4&&x.status==200){document.getElementById("sT").innerText="Processing... Please wait!";setTimeout(function(){window.location.href="/pdf_home"},5000)}};x.open("POST","/do_pdf_upload",true);x.send(d);}</script></body>"""

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file"); n = request.form.get("pdf_name").replace(" ","_")
        if f: process_pdf_fast(f, n)
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
