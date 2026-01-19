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

def find_zig():
    """Zig 実行ファイルを探す（環境変数→ローカル zig/zig.exe→PATH）"""
    env = os.environ.get("AUTOBUILD_ZIG")
    if env:
        p = Path(env)
        if p.exists():
            return p

    # リポジトリ内に zig/zig.exe を置いている想定
    local = Path("zig/zig.exe")
    if local.exists():
        return local

    # あるいは tool/zig/zig.exe（過去の構成）
    local2 = Path("tool/zig/zig.exe")
    if local2.exists():
        return local2

    # PATH 上の zig
    p = shutil.which("zig")
    if p:
        return Path(p)

    return None

def build_with_zig(zig_path: Path, src: Path, out_name: str, std="c11", opt="O2"):
    """
    Zig を使ってクロスコンパイル（Windowsターゲット）する。
    戻り値は subprocess の returncode。
    """
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
    # 実行は標準の環境で行う（ログをそのまま流す）
    proc = subprocess.run(cmd)
    return proc.returncode

def main():
    # ASCII の短い起動メッセージ（初期エンコーディング問題回避）
    print("AutoBuildTool (Windows) - start")

    if len(sys.argv) < 2:
        print("Usage: autobuildtool.exe path\\to\\main.c [out.exe]")
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print("ERROR: source not found:", src)
        sys.exit(2)

    # 非対話的に argv[2] で出力名が渡される場合を優先
    out_name = None
    if len(sys.argv) >= 3:
        out_name = sys.argv[2]
    else:
        # パイプや対話から読み取る（例: echo name | exe source）
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
        print("ERROR: Zig not found. Provide zig/zig.exe in repo or set AUTOBUILD_ZIG env var, or ensure zig is on PATH.")
        sys.exit(3)

    print("Using zig:", zig_path)
    print(f"Building {src} -> {out_name} ...")
    rc = build_with_zig(zig_path, src, out_name, std="c11", opt="O2")
    if rc != 0:
        print("Build failed (exit code {})".format(rc))
        sys.exit(rc)

    print("Build succeeded. Created:", out_name)
    sys.exit(0)

if __name__ == "__main__":
    main()