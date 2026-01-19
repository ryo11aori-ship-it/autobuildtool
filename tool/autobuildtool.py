import sys
import subprocess
from pathlib import Path

def main():
    print("=== AutoBuildTool for Windows ===")

    if len(sys.argv) < 2:
        print("使い方:")
        print("  autobuildtool.exe main.c")
        return

    src = Path(sys.argv[1])
    if not src.exists():
        print("エラー: main.c が見つかりません")
        return

    out_name = input("出力exe名 [a.exe]: ").strip()
    if not out_name:
        out_name = "a.exe"
    if not out_name.lower().endswith(".exe"):
        out_name += ".exe"

    zig = Path("zig/zig.exe")
    if not zig.exists():
        print("エラー: zig/zig.exe が見つかりません")
        return

    print("ビルド中...")

    cmd = [
        str(zig),
        "cc",
        str(src),
        "-O2",
        "-std=c11",
        "-target",
        "x86_64-windows-gnu",
        "-o",
        out_name
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ビルド失敗")
        return

    print("=== 完了 ===")
    print("生成されたファイル:", out_name)

if __name__ == "__main__":
    main()