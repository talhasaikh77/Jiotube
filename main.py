import os
import fitz
import cloudinary
import cloudinary.uploader
import cloudinary.api
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
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_path = f"p{i+1}_{pdf_name}.jpg"
            pix.save(img_path)
            cloudinary.uploader.upload(img_path, public_id=f"p{i+1}", folder=f"pdf_data/{pdf_name}", tags=[pdf_name, "pdf_page"], resource_type="image")
            if os.path.exists(img_path): os.remove(img_path)
        doc.close()
        os.remove(pdf_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    next_c = request.args.get("next")
    try:
        res = cloudinary.api.resources(resource_type="video", type="upload", max_results=10, next_cursor=next_c)
        videos = [v for v in res.get("resources", []) if q in v.get("public_id", "").lower()]
        new_c = res.get("next_cursor")
    except: videos = []; new_c = None
    v_cards = ""
    for v in videos:
        thumb = v["secure_url"].rsplit(".", 1)[0] + ".jpg"
        v_cards += f" <div style=\"background:#fff;margin-bottom:20px;border-radius:12px;overflow:hidden;box-shadow:0 4px 8px rgba(0,0,0,0.1);\"><img src=\"{thumb}\" style=\"width:100%;\"><div style=\"padding:12px;\"><b>{v[\"public_id\"]}</b><div style=\"display:flex;gap:5px;margin-top:10px;\"><a href=\"{v[\"secure_url\"]}\" style=\"flex:2;background:#0078d7;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;\">PLAY</a><a href=\"/modify?task=rename&pid={v[\"public_id\"]}\" style=\"flex:1;background:orange;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;\">NAME</a><a href=\"/modify?task=delete&pid={v[\"public_id\"]}\" style=\"flex:1;background:red;color:#fff;text-align:center;padding:12px;text-decoration:none;border-radius:8px;font-size:11px;\">DEL</a></div></div></div>"
    next_btn = f"<a href=\"/?next={new_c}&q={q}\" style=\"display:block;background:#333;color:#fff;text-align:center;padding:15px;text-decoration:none;border-radius:10px;\">LOAD MORE ↓</a>" if new_c else ""
    return f"<body style=\"background:#f4f7f6;font-family:sans-serif;margin:0;\"><div style=\"background:#fff;padding:15px;text-align:center;border-bottom:3px solid #0078d7;position:sticky;top:0;z-index:1000;\"><h2>JioTube Pro</h2><div style=\"display:flex;gap:8px;\"><a href=\"/admin_upload\" style=\"flex:1;background:#28a745;color:#fff;padding:10px;text-decoration:none;border-radius:6px;\">+ UPLOAD</a><a href=\"/pdf_home\" style=\"flex:1;background:#e74c3c;color:#fff;padding:10px;text-decoration:none;border-radius:6px;\">PDF VIEWER</a></div><form action=\"/\" method=\"GET\" style=\"margin-top:12px;display:flex;gap:5px;\"><input type=\"text\" name=\"q\" placeholder=\"Search...\" style=\"flex:1;padding:10px;\" value=\"{q}\"><button style=\"background:#0078d7;color:#fff;border:none;padding:10px;\">OK</button></form></div><div style=\"padding:12px;\">{v_cards} {next_btn}</div></body>"

@app.route("/pdf_home")
def pdf_home():
    try: folders = cloudinary.api.subfolders("pdf_data")["folders"]
    except: folders = []
    f_list = "".join([f"<div style=\"background:#fff;margin-bottom:12px;padding:15px;border-radius:10px;display:flex;justify-content:space-between;border-left:6px solid #e74c3c;\"><a href=\"/view_pdf?name={f[\"name\"]}\" style=\"text-decoration:none;color:#333;font-weight:bold;\">{f[\"name\"].upper()}</a><a href=\"/pdf_delete?name={f[\"name\"]}\" style=\"color:red;text-decoration:none;font-size:12px;\">DEL</a></div>" for f in folders])
    return f"<body style=\"background:#f9f9f9;font-family:sans-serif;padding:20px;\"><h2 style=\"text-align:center;color:#e74c3c;\">PDF Archive</h2><a href=\"/upload_pdf_page\" style=\"display:block;background:#000;color:#fff;padding:18px;text-align:center;text-decoration:none;border-radius:12px;\">+ NEW PDF</a><br>{f_list}<br><center><a href=\"/\">← Home</a></center></body>"

@app.route("/upload_pdf_page")
def upload_pdf_page():
    return """<body style="text-align:center;padding:25px;font-family:sans-serif;background:#f0f4f5;"><div style="background:#fff;padding:25px;border-radius:20px;max-width:400px;margin:auto;"><h3 style="color:#0078d7;">MediaFire Upload</h3><form id="uF"><input type="file" id="fI" name="file" accept=".pdf" style="margin-bottom:20px;"><br><input type="text" id="pN" name="pdf_name" placeholder="PDF Name" style="width:90%;padding:10px;margin-bottom:10px;"><input type="password" id="pw" name="pw" placeholder="Pass" style="width:90%;padding:10px;margin-bottom:20px;"><div id="pW" style="display:none;margin-bottom:20px;"><div style="width:100%;background:#eee;height:15px;border-radius:10px;overflow:hidden;"><div id="pB" style="width:0%;background:#0078d7;height:100%;"></div></div><p id="sT" style="font-size:12px;">0%</p></div><button type="button" onclick="upL()" id="uB" style="width:100%;padding:15px;background:#0078d7;color:#fff;border:none;border-radius:10px;">START UPLOAD</button></form></div><script>function upL(){var f=document.getElementById("fI").files[0],n=document.getElementById("pN").value,p=document.getElementById("pw").value;if(!f||!n||!p)return alert("Fill all!");var d=new FormData();d.append("file",f);d.append("pdf_name",n);d.append("pw",p);var x=new XMLHttpRequest();x.upload.addEventListener("progress",function(e){if(e.lengthComputable){var pc=Math.round((e.loaded/e.total)*100);document.getElementById("pW").style.display="block";document.getElementById("pB").style.width=pc+"%";document.getElementById("sT").innerText="Uploading: "+pc+"%";document.getElementById("uB").disabled=true;}});x.onreadystatechange=function(){if(x.readyState==4&&x.status==200){document.getElementById("sT").innerText="Converting... Wait!";setTimeout(function(){window.location.href="/pdf_home"},3000)}};x.open("POST","/do_pdf_upload",true);x.send(d);}</script></body>"""

@app.route("/do_pdf_upload", methods=["POST"])
def do_pdf_upload():
    if request.form.get("pw") == ADMIN_PASSWORD:
        f = request.files.get("file")
        n = request.form.get("pdf_name").replace(" ","_")
        if f: process_pdf_fast(f, n)
    return "OK"

@app.route("/view_pdf")
def view_pdf():
    name = request.args.get("name")
    c = request.args.get("next")
    res = cloudinary.api.resources_by_tag(name, max_results=10, next_cursor=c)
    pages = sorted(res["resources"], key=lambda x: x["public_id"])
    nc = res.get("next_cursor")
    h = "".join([f"<div style=\"margin-bottom:20px;background:#fff;\"><img src=\"{p[\"secure_url\"]}\" style=\"width:100%;\"><div style=\"padding:10px;text-align:center;background:#eee;\"><a href=\"{p[\"secure_url\"].replace(\"/upload/\",\"/upload/fl_attachment/\")}\" style=\"background:#28a745;color:#fff;padding:8px;text-decoration:none;border-radius:5px;\">DOWNLOAD HQ</a></div></div>" for p in pages])
    nb = f"<a href=\"/view_pdf?name={name}&next={nc}\" style=\"display:block;background:#e74c3c;color:#fff;padding:15px;text-align:center;text-decoration:none;border-radius:10px;\">NEXT 10 PAGES →</a>" if nc else ""
    return f"<body style=\"background:#111;margin:0;\"><div style=\"background:#fff;padding:10px;text-align:center;position:sticky;top:0;display:flex;justify-content:space-between;\"><a href=\"/pdf_home\">← BACK</a><b>{name.upper()}</b><span></span></div>{h}{nb}</body>"

@app.route("/admin_upload", methods=["GET","POST"])
def admin_upload():
    if request.method == "POST" and request.form.get("pw") == ADMIN_PASSWORD:
        return "<form action=\"/do_up\" method=\"POST\" enctype=\"multipart/form-data\"><input type=\"file\" name=\"file\"><input type=\"text\" name=\"vname\"><button>UP</button></form>"
    return "<form method=\"POST\"><input type=\"password\" name=\"pw\"><button>Login</button></form>"

@app.route("/do_up", methods=["POST"])
def do_up():
    f = request.files.get("file")
    v = request.form.get("vname", "video").replace(" ","_")
    if f: cloudinary.uploader.upload(f, resource_type="video", public_id=v)
    return redirect("/")

@app.route("/modify")
def modify():
    t = request.args.get("task"); p = request.args.get("pid")
    return render_template_string("<form action=\"/confirm\" method=\"POST\"><input type=\"hidden\" name=\"pid\" value=\"{{p}}\"><input type=\"hidden\" name=\"task\" value=\"{{t}}\">{% if t==\"rename\" %}<input type=\"text\" name=\"new\"><br>{% endif %}<input type=\"password\" name=\"pw\"><button>OK</button></form>", t=t, p=p)

@app.route("/confirm", methods=["POST"])
def confirm():
    if request.form.get("pw") == ADMIN_PASSWORD:
        t = request.form.get("task"); p = request.form.get("pid")
        if t == "rename": cloudinary.uploader.rename(p, request.form.get("new").replace(" ","_"), resource_type="video")
        elif t == "delete": cloudinary.uploader.destroy(p, resource_type="video")
    return redirect("/")

@app.route("/pdf_delete")
def pdf_delete():
    cloudinary.api.delete_resources_by_tag(request.args.get("name"))
    return redirect("/pdf_home")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
