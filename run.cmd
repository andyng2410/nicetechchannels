@echo off
setlocal

chcp 65001 >nul 2>nul
cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Chua co moi truong .venv. Hay chay .\install.cmd truoc.
    exit /b 1
)

set "PATH=%~dp0.venv\Scripts;%~dp0.tools\ffmpeg\bin;%PATH%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

"%~dp0.venv\Scripts\python.exe" "%~dp0web_server.py" %*
exit /b %ERRORLEVEL%
