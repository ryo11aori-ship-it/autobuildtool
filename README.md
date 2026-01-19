Question-based Auto Build — Pro (prototype)
==========================================

What:
- Upload a single `main.c`, choose build targets (linux/windows/macos), pick C standard & optimization.
- The service builds binaries for requested OSes, packs logs + README + binaries into a zip, and returns it.

Security:
- Building arbitrary C is dangerous. Use Docker or CI runners for isolation.
- This prototype uses Docker for local Linux/Windows cross compile. macOS builds should use CI macOS runners.

Quickstart (local):
1. Install Docker (recommended).
2. python -m pip install flask
3. python app/server.py
4. Open http://localhost:8080 and upload main.c.

GitHub Actions:
- Example workflow at .github/workflows/build-matrix.yml builds sample/main.c into linux/windows/macos artifacts.

Notes:
- Windows exe is produced via mingw cross-compiler on ubuntu (via apt-get).
- macOS binary must be built on macOS runner.