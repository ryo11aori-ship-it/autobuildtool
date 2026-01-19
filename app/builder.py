# app/builder.py
import subprocess
import os
import shutil
import uuid
from pathlib import Path

DEFAULT_TIMEOUT = 15  # seconds

def safe_mkdir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def build_c(source_path: str,
            out_dir: str,
            compiler: str = "gcc",
            std: str = "c11",
            opt: str = "O2",
            static: bool = False,
            output_name: str = "main",
            timeout: int = DEFAULT_TIMEOUT):
    """
    Build a C source file.
    source_path: path to main.c
    out_dir: directory to place outputs
    returns dict with keys: success(bool), returncode, stdout, stderr, exe_path (if success)
    """
    safe_mkdir(out_dir)
    workdir = Path(out_dir).resolve()
    src = Path(source_path).resolve()
    if not src.exists():
        return {"success": False, "returncode": -1, "stdout": "", "stderr": f"Source {src} not found", "exe_path": None}

    # Prepare output path
    exe_path = workdir / output_name
    cmd = [compiler, "-std=" + std, "-" + opt, str(src), "-o", str(exe_path)]

    if static:
        cmd.append("-static")

    # For debugging reproducibility, include -Wall -Wextra optionally
    cmd.extend(["-Wall", "-Wextra"])

    try:
        proc = subprocess.run(cmd, cwd=str(workdir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        stdout = proc.stdout.decode(errors="replace")
        stderr = proc.stderr.decode(errors="replace")
        success = (proc.returncode == 0)
        return {
            "success": success,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "exe_path": str(exe_path) if success else None,
            "cmd": " ".join(cmd)
        }
    except subprocess.TimeoutExpired as e:
        return {"success": False, "returncode": -2, "stdout": "", "stderr": f"Build timed out after {timeout}s", "exe_path": None}
    except Exception as e:
        return {"success": False, "returncode": -3, "stdout": "", "stderr": str(e), "exe_path": None}
