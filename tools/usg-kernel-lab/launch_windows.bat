@echo off
setlocal
cd /d "%~dp0..\.."
py -c "import jsonschema" >nul 2>nul
if errorlevel 1 (
  echo Missing dependency: jsonschema
  echo Install it with: py -m pip install "jsonschema^>=4.18,^<5"
  pause
  exit /b 1
)
py tools\usg-kernel-lab\server.py
pause
