import sys
import subprocess
from pathlib import Path
import shutil
import os

# ===== Windows exe での文字化け・UnicodeEncodeError 対策 =====
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def find_zig():
    # 環境変数優先
    env = os.environ.get("AUTOBUILD_ZIG")
    if env and Path(env).exists():
        return Path(env)

    # リポジトリ直下の zig フォルダ（任意）
    local = Path("zig/zig.exe")
    if local.exists():
        return local

    # PATH
    p = shutil.which("zig")
    if p:
        return Path(p)

    return None

def main():
    print("AutoBuildTool (Windows)")

    if len(sys.argv) < 2:
        print("Usage: autobuildtool.exe main.c [out.exe]")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print("ERROR: source not found:", src)
        sys.exit(2)

    # 出力名（パイプ or 引数）
    if len(sys.argv) >= 3:
        out = sys.argv[2]
    else:
        try:
            out = input("Output exe name: ").strip()
        except Exception:
            out = ""

    if not out:
        out = "a.exe"
    if not out.lower().endswith(".exe"):
        out += ".exe"

    zig = find_zig()
    if not zig:
        print("ERROR: zig not found")
        sys.exit(3)

    cmd = [
       