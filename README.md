# autobuildtool
# Question-based Auto Build (Prototype)

## What
Upload a `main.c`, answer a few simple options (compiler, C standard, optimization), and the server will attempt to compile and provide the binary and log.

## Quickstart (local)
1. Install Python 3.8+
2. Install dependencies:
   pip install flask
3. Run:
   python app/server.py
4. Open http://localhost:8080

**Security note**: DO NOT run this server on a public network without sandboxing untrusted code. Build operations execute arbitrary C code. Use Docker for safety.

## GitHub Actions
A sample workflow is included at `.github/workflows/build-sample.yml` to show how to run a build on push in CI and upload artifacts.
