# app/builder.py
import os
import shutil
import subprocess
import uuid
import zipfile
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Config
WORK_ROOT = Path("uploads")
WORK_ROOT.mkdir(parents=True, exist_ok=True)
DOCKER_TIMEOUT = 60  # seconds for docker run (container lifetime)
LOCAL_TIMEOUT = 20   # seconds for direct run (small code)

def _safe_mkdir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def generate_meta(name: str, targets: list, options: dict) -> dict:
    now = datetime.utcnow().isoformat() + "Z"
    meta = {
        "tool": "QuestionAutoBuilder",
        "version": "v1-proto",
        "created_at": now,
        "session_name": name,
        "targets": targets,
        "options": options
    }
    return meta

def run_subproc(cmd, cwd: Path, timeout=LOCAL_TIMEOUT):
    proc = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return proc.returncode, proc.stdout.decode(errors="replace"), proc.stderr.decode(errors="replace")

# ----------------------------
# Build strategies
# ----------------------------

def build_in_docker_linux(src_path: Path, out_dir: Path, std="c11", opt="O2", output_name="sample_main"):
    """
    Build inside a lightweight gcc Docker image (official) to isolate the process.
    Produces a linux ELF binary.
    """
    _safe_mkdir(out_dir)
    # Use official gcc image (may be large). We mount the session directory and run gcc inside.
    container_src = "/work/main.c"
    container_out = "/work/" + output_name
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{src_path.parent.resolve()}:/work:rw",
        "gcc:12", # use gcc:12 image (may be adjusted)
        "bash", "-lc",
        f"gcc -std={std} -{opt} {container_src} -o {container_out} -Wall -Wextra"
    ]
    try:
        rc, out, err = _run_cmd_capture(cmd, cwd=out_dir)
    except Exception as e:
        return {"success": False, "stderr": str(e), "stdout": "", "returncode": -99}

    exe_path = out_dir / output_name
    success = exe_path.exists()
    return {"success": success, "stdout": out, "stderr": err, "returncode": rc, "exe_path": str(exe_path) if success else None, "cmd": " ".join(cmd)}

def build_windows_cross_mingw(src_path: Path, out_dir: Path, std="c11", opt="O2", output_name="sample_main_win.exe"):
    """
    Use an ubuntu docker image to install mingw-w64 and cross-compile a Windows exe.
    This installs mingw on the fly — slow but works as prototype.
    """
    _safe_mkdir(out_dir)
    container_src = "/work/main.c"
    container_out = "/work/" + output_name
    # The command installs mingw-w64 then compiles. Note: slow on first run.
    script = (
        "apt-get update -qq && apt-get install -y -qq mingw-w64 && "
        f"x86_64-w64-mingw32-gcc -std={std} -{opt} {container_src} -o {container_out} -Wall -Wextra"
    )
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{src_path.parent.resolve()}:/work:rw",
        "ubuntu:22.04",
        "bash", "-lc",
        script
    ]
    try:
        rc, out, err = _run_cmd_capture(cmd, cwd=out_dir, timeout=1800)
    except Exception as e:
        return {"success": False, "stderr": str(e), "stdout": "", "returncode": -99}
    exe_path = out_dir / output_name
    success = exe_path.exists()
    return {"success": success, "stdout": out, "stderr": err, "returncode": rc, "exe_path": str(exe_path) if success else None, "cmd": " ".join(cmd)}

def build_local_clang(src_path: Path, out_dir: Path, std="c11", opt="O2", output_name="sample_main_macos"):
    """
    Local clang build (for macOS runner). This will be used by GitHub Actions macos job.
    """
    _safe_mkdir(out_dir)
    cmd = ["clang", f"-std={std}", f"-{opt}", str(src_path), "-o", str(out_dir / output_name), "-Wall", "-Wextra"]
    try:
        rc, out, err = _run_cmd_capture(cmd, cwd=out_dir)
    except Exception as e:
        return {"success": False, "stderr": str(e), "stdout": "", "returncode": -99}
    exe_path = out_dir / output_name
    success = exe_path.exists()
    return {"success": success, "stdout": out, "stderr": err, "returncode": rc, "exe_path": str(exe_path) if success else None, "cmd": " ".join(cmd)}

# ----------------------------
# Helpers
# ----------------------------
def _run_cmd_capture(cmd, cwd: Path, timeout=LOCAL_TIMEOUT):
    """
    Run a shell command list and capture stdout/stderr (streamed as return).
    Use subprocess.run. Returns (returncode, stdout, stderr).
    """
    proc = subprocess.run(cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    out = proc.stdout.decode(errors="replace")
    err = proc.stderr.decode(errors="replace")
    return proc.returncode, out, err

def pack_artifacts(session_dir: Path, artifact_basename: str) -> Path:
    zip_path = session_dir / f"{artifact_basename}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in session_dir.iterdir():
            if p.name == zip_path.name:
                continue
            zf.write(p, arcname=p.name)
    return zip_path

def generate_readme(session_dir: Path, meta: dict, build_summaries: Dict[str, dict]) -> Path:
    readme = session_dir / "README_build.txt"
    with open(readme, "w", encoding="utf-8") as f:
        f.write("Question-based Auto Build — Build Summary\n")
        f.write("===============================\n\n")
        f.write(f"Session: {meta.get('session_name')}\n")
        f.write(f"Created: {meta.get('created_at')}\n\n")
        f.write("Options:\n")
        f.write(json.dumps(meta.get("options", {}), indent=2))
        f.write("\n\nTargets:\n")
        for t in meta.get("targets", []):
            f.write(f"- {t}\n")
        f.write("\n\nBuild details:\n")
        for t, s in build_summaries.items():
            f.write(f"--- {t} ---\n")
            f.write(f"Success: {s.get('success')}\n")
            f.write(f"Return code: {s.get('returncode')}\n")
            f.write("Command:\n")
            f.write(s.get("cmd", "") + "\n\n")
            f.write("STDOUT:\n")
            f.write(s.get("stdout", "") + "\n")
            f.write("STDERR:\n")
            f.write(s.get("stderr", "") + "\n\n")
    return readme

# ----------------------------
# High-level API
# ----------------------------
def run_build_session(session_id: str, src_file: Path, targets: list, options: dict) -> dict:
    """
    session_id: unique id
    src_file: path to main.c
    targets: list of "linux","windows","macos"
    options: dict {std, opt, docker(boolean default True)}
    """
    session_dir = WORK_ROOT / session_id
    _safe_mkdir(session_dir)
    # Ensure main.c is in session_dir (it should be)
    # Copy if necessary
    src_dest = session_dir / "main.c"
    if src_file.resolve() != src_dest.resolve():
        shutil.copy2(src_file, src_dest)

    build_results = {}
    for t in targets:
        if t == "linux":
            out_name = f"{session_id}_linux_x86_64"
            out_path = session_dir / out_name
            if options.get("use_docker", True):
                res = build_in_docker_linux(src_dest, session_dir, std=options.get("std","c11"), opt=options.get("opt","O2"), output_name=out_name)
            else:
                rc, out, err = _run_cmd_capture(["gcc", f"-std={options.get('std','c11')}", f"-{options.get('opt','O2')}", str(src_dest), "-o", str(out_path)])
                res = {"success": (rc==0), "returncode": rc, "stdout": out, "stderr": err, "exe_path": str(out_path) if rc==0 else None, "cmd": "gcc ..."}
            build_results["linux"] = res

        elif t == "windows":
            out_name = f"{session_id}_windows_x86_64.exe"
            if options.get("use_docker", True):
                res = build_windows_cross_mingw(src_dest, session_dir, std=options.get("std","c11"), opt=options.get("opt","O2"), output_name=out_name)
            else:
                # try local cross compilation
                rc, out, err = _run_cmd_capture(["x86_64-w64-mingw32-gcc", f"-std={options.get('std','c11')}", f"-{options.get('opt','O2')}", str(src_dest), "-o", str(session_dir / out_name)])
                res = {"success": (rc==0), "returncode": rc, "stdout": out, "stderr": err, "exe_path": str(session_dir / out_name) if rc==0 else None, "cmd": "x86_64-w64-mingw32-gcc ..."}
            build_results["windows"] = res

        elif t == "macos":
            out_name = f"{session_id}_macos_x86_64"
            # For macOS, prefer building on macOS runner (GitHub Actions). If running locally on mac, use clang.
            if os.uname().sysname == "Darwin" and not options.get("force_ci", False):
                res = build_local_clang(src_dest, session_dir, std=options.get("std","c11"), opt=options.get("opt","O2"), output_name=out_name)
            else:
                # Not on mac -> indicate request and advise CI
                res = {"success": False, "returncode": -1, "stdout": "", "stderr": "macOS binaries must be built on macOS (use CI macOS runner).", "exe_path": None, "cmd": ""}
            build_results["macos"] = res

        else:
            build_results[t] = {"success": False, "stderr": "Unknown target", "returncode": -2}

    # Generate README and pack
    meta = generate_meta(session_id, targets, options)
    readme_path = generate_readme(session_dir, meta, build_results)
    zip_path = pack_artifacts(session_dir, f"{session_id}_artifacts")

    return {
        "session_id": session_id,
        "meta": meta,
        "build_results": build_results,
        "readme": str(readme_path),
        "zip": str(zip_path)
    }