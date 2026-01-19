# tool/autobuildtool.py
import sys
import subprocess
from pathlib import Path
import shutil
import os

def resource_path(relpath: str) -> Path:
    """
    Return a Path to resource that works both when executed normally and when bundled by PyInstaller.
    If PyInstaller bundles, resources are unpacked to _MEIPASS.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        base = Path(sys._MEIPASS)
        return base / relpath
    else:
        # normal execution (repo layout)
        return Path(__file__).resolve().parent.parent / relpath

def find_zig_exe() -> Path:
    # 1) If environment variable AUTOBUILD_ZIG set, prefer that
    env = os.environ.get("AUTOBUILD_ZIG")
    if env:
        p = Path(env)
        if p.exists():
            return p

    # 2) bundled or repo zig/zig.exe
    zig_rel = resource_path("zig/zig.exe")
    if zig_rel.exists():
        return zig_rel

    # 3) fallback: look on PATH for zig
    p = shutil.which("zig")
    if p:
        return Path(p)

    return None

def build_with_zig(zig_path: Path, src: Path, out_name: str, std="c11", opt="O2"):
    cmd = [
        str(zig_path),
        "cc",
        str(src),
        f"-{opt}",
        f"-std={std}",
        "-target", "x86_64-windows-gnu",
        "-o",
        out_name
    ]
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode

def main():
    print("=== AutoBuildTool for Windows ===")
    if len(sys.argv) < 2:
        print("使い方: autobuildtool.exe path\\to\\main.c")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print("エラー: 指定されたソースが見つかりません:", src)
        sys.exit(2)

    out_name = input("出力exe名 [a.exe]: ").strip() or "a.exe"
    if not out_name.lower().endswith(".exe"):
        out_name += ".exe"

    zig_path = find_zig_exe()
    if not zig_path:
        print("エラー: Zig が見つかりません。環境変数 AUTOBUILD_ZIG でパスを指定するか、zig/zig.exe を同梱してください。")
        sys.exit(3)

    print("使用する zig:", zig_path)
    print("ビルド中...（少し時間がかかる場合があります）")
    rc = build_with_zig(zig_path, src, out_name, std="c11", opt="O2")
    if rc != 0:
        print("ビルド失敗 (exit code {})".format(rc))
        sys.exit(rc)
    print("=== 完了 ===")
    print("生成されたファイル:", out_name)

if __name__ == "__main__":
    main()