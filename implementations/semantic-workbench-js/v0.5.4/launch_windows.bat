@echo off
setlocal
cd /d "%~dp0"

 echo.
 echo  USG Semantic Workbench v0.5.4
 echo  ---------------------------

where node >nul 2>nul
if %errorlevel%==0 (
    echo Starting full local bridge with Node.js...
    start "USG Semantic Workbench Server" cmd /k node server.js
    timeout /t 2 /nobreak >nul
    start "" http://127.0.0.1:8765
    echo.
    echo The full app is opening in your browser.
    echo Keep the server window open while using the app.
    goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
    echo Node.js was not found. Starting static Python mode.
    echo The rule interpreter will work; the Ollama bridge requires Node.js.
    start "USG Semantic Workbench Static Server" cmd /k py -3 -m http.server 8765 --bind 127.0.0.1
    timeout /t 2 /nobreak >nul
    start "" http://127.0.0.1:8765
    goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
    echo Node.js was not found. Starting static Python mode.
    echo The rule interpreter will work; the Ollama bridge requires Node.js.
    start "USG Semantic Workbench Static Server" cmd /k python -m http.server 8765 --bind 127.0.0.1
    timeout /t 2 /nobreak >nul
    start "" http://127.0.0.1:8765
    goto :end
)

echo No Node.js or Python server was found.
echo Opening the app directly. Offline pattern interpretation is still available.
start "" "%~dp0index.html"

echo.
echo To enable the optional local LLM adapter, install Node.js and run this launcher again.

:end
echo.
echo You can close this launcher. Keep the server window open until you finish testing.
pause
