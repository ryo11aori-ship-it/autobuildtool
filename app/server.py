# app/server.py
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from pathlib import Path
from builder import run_build_session, WORK_ROOT
from utils import safe_rm_tree
import os

app = Flask(__name__)
app.secret_key = "replace-this-in-prod"

UPLOAD_DIR = WORK_ROOT

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if 'source' not in request.files:
        flash("No file part")
        return redirect(url_for('index'))
    file = request.files['source']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for('index'))

    # Create session
    session_id = str(uuid.uuid4())[:12]
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    src_path = session_dir / "main.c"
    file.save(str(src_path))

    # Options
    std = request.form.get("std", "c11")
    opt = request.form.get("opt", "O2")
    use_docker = bool(request.form.get("use_docker", "on"))
    # Targets
    targets = []
    if request.form.get("target_linux"): targets.append("linux")
    if request.form.get("target_windows"): targets.append("windows")
    if request.form.get("target_macos"): targets.append("macos")
    if not targets:
        targets = ["linux"]  # default

    options = {"std": std, "opt": opt, "use_docker": use_docker}

    # Run build (synchronous; produces zip)
    res = run_build_session(session_id, src_path, targets, options)

    # Prepare download URLs
    session_public = session_id
    zipname = Path(res["zip"]).name
    readme = Path(res["readme"]).name

    return render_template("index.html",
                           built=True,
                           session=session_public,
                           zip_url=f"/download/{session_public}/{zipname}",
                           readme_url=f"/download/{session_public}/{readme}",
                           build_results=res["build_results"],
                           meta=res["meta"])

@app.route("/download/<session_id>/<filename>")
def download(session_id, filename):
    safe_dir = UPLOAD_DIR / session_id
    if not safe_dir.exists():
        return "Not found", 404
    return send_from_directory(directory=str(safe_dir), filename=filename, as_attachment=True)

@app.route("/cleanup/<session_id>", methods=["POST"])
def cleanup(session_id):
    sd = UPLOAD_DIR / session_id
    safe_rm_tree(sd)
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)