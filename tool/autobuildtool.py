# tool/autobuildtool.py
import sys
import subprocess
from pathlib import Path
import shutil
import os

# --- 安全なストリーム再設定（PyInstaller バンドル環境や Windows Runner 対策） ---
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# =====================
# Zig / C 関連（既存）
# =====================

def find_zig():
    """Zig 実行ファイルを探す（環境変数→ローカル zig/zig.exe→PATH）"""
    env = os.environ.get("AUTOBUILD_ZIG")
    if env:
        p = Path(env)
        if p.exists():
            return p

    local = Path("zig/zig.exe")
    if local.exists():
        return local

    local2 = Path("tool/zig/zig.exe")
    if local2.exists():
        return local2

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


# =====================
# Python / PyInstaller
# =====================

def find_pyinstaller():
    """pyinstaller を探す（PATH 優先）"""
    p = shutil.which("pyinstaller")
    if p:
        return Path(p)
    return None


def build_python(pyinstaller: Path, src: Path, out_name: str):
    """
    PyInstaller を使って main.py を exe 化する
    """
    cmd = [
        str(pyinstaller),
        "--onefile",
        "--clean",
        "--name",
        Path(out_name).stem,
        str(src)
    ]
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    return proc.returncode


# =====================
# メイン
# =====================

def main():
    print("AutoBuildTool (Windows) - start")

    cwd = Path.cwd()
    main_c = cwd / "main.c"
    main_py = cwd / "main.py"

    # --- 明示的に main.c が argv で指定された場合（従来互換） ---
    if len(sys.argv) >= 2:
        src = Path(sys.argv[1])
        if not src.exists():
            print("ERROR: source not found:", src)
            sys.exit(2)

        out_name = None
        if len(sys.argv) >= 3:
            out_name = sys.argv[2]
        else:
            try:
                out_name = input("Output exe name [a.exe]: ").strip()
            except Exception:
                out_name = ""

        if not out_name:
            out_name = "a.exe"
        if not out_name.lower().endswith(".exe"):
            out_name += ".exe"

        zig_path = find_zig()
        if not zig_path:
            print("ERROR: Zig not found.")
            sys.exit(3)

        print("Using zig:", zig_path)
        rc = build_with_zig(zig_path, src, out_name)
        sys.exit(rc)

    # --- 自動検出ルート ---
    has_c = main_c.exists()
    has_py = main_py.exists()

    if not has_c and not has_py:
        print("ERROR: main.c or main.py not found in current directory.")
        sys.exit(1)

    # --- 両方ある場合は選択 ---
    if has_c and has_py:
        print("Found both main.c and main.py.")
        print("Select build target:")
        print("1) C (Zig)")
        print("2) Python (PyInstaller)")
        try:
            choice = input("> ").strip()
        except Exception:
            choice = "1"
    elif has_c:
        choice = "1"
    else:
        choice = "2"

    # --- 出力名 ---
    try:
        out_name = input("Output exe name [a.exe]: ").strip()
    except Exception:
        out_name = ""
    if not out_name:
        out_name = "a.exe"
    if not out_name.lower().endswith(".exe"):
        out_name += ".exe"

    # --- C ルート ---
    if choice == "1":
        zig_path = find_zig()
        if not zig_path:
            print("ERROR: Zig not found.")
            sys.exit(3)

        print("Using zig:", zig_path)
        print(f"Building {main_c} -> {out_name} ...")
        rc = build_with_zig(zig_path, main_c, out_name)
        if rc != 0:
            print("Build failed.")
            sys.exit(rc)

    # --- Python ルート ---
    elif choice == "2":
        pyinstaller = find_pyinstaller()
        if not pyinstaller:
            print("ERROR: pyinstaller not found. Install with: pip install pyinstaller")
            sys.exit(4)

        print("Using pyinstaller:", pyinstaller)
        rc = build_python(pyinstaller, main_py, out_name)
        if rc != 0:
            print("Build failed.")
            sys.exit(rc)

    else:
        print("Invalid selection.")
        sys.exit(1)

    print("Build succeeded. Created:", out_name)
    sys.exit(0)


if __name__ == "__main__":
    main()