# app/server.py
import os
import uuid
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from pathlib import Path
from builder import build_c

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "replace-this-with-a-random-secret-in-prod"

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

    # Save source under a uuid folder
    session_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    src_path = session_dir / "main.c"
    file.save(str(src_path))

    # Read options from form
    compiler = request.form.get("compiler", "gcc")
    std = request.form.get("std", "c11")
    opt = request.form.get("opt", "O2")
    static = bool(request.form.get("static"))
    output_name = request.form.get("output_name", "main")

    # Basic checks
    if output_name.strip() == "":
        output_name = "main"

    # Build
    build_res = build_c(str(src_path), str(session_dir), compiler=compiler, std=std, opt=opt, static=static, output_name=output_name)

    # Save build result to file for display
    log_path = session_dir / "build_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Command:\n")
        f.write(build_res.get("cmd", "") + "\n\n")
        f.write("--- STDOUT ---\n")
        f.write(build_res.get("stdout", "") + "\n")
        f.write("\n--- STDERR ---\n")
        f.write(build_res.get("stderr", "") + "\n")
        f.write(f"\nReturn code: {build_res.get('returncode')}\n")

    # Prepare response page
    success = build_res.get("success", False)
    exe_rel = None
    if success and build_res.get("exe_path"):
        exe_rel = f"/download/{session_id}/{output_name}"
    return render_template("index.html",
                           session_id=session_id,
                           success=success,
                           exe_rel=exe_rel,
                           log_path=f"/download/{session_id}/build_log.txt",
                           build_res=build_res)

@app.route("/download/<session_id>/<filename>")
def download(session_id, filename):
    safe_dir = UPLOAD_DIR / session_id
    if not safe_dir.exists():
        return "Not found", 404
    return send_from_directory(directory=str(safe_dir), filename=filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
