@echo off
echo Building AutoBuildTool.exe

pyinstaller ^
  --onefile ^
  --name autobuildtool ^
  autobuildtool.py

echo Done
pause