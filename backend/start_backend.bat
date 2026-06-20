@echo off
setlocal
chcp 65001 >nul
title QuickSpeak Backend v1.0.2
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python。请先安装 Python 3.10 或 3.11 x64，并勾选 Add Python to PATH。
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] 正在创建独立 Python 环境...
    python -m venv .venv
    if errorlevel 1 goto :failed
)

set "PYTHON=.venv\Scripts\python.exe"
if not exist ".venv\.quickspeak_deps_1.0.2" (
    echo [2/3] 正在安装后端依赖，首次运行需要一些时间...
    "%PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :failed
    "%PYTHON%" -m pip install -r requirements-backend.txt
    if errorlevel 1 goto :failed
    type nul > ".venv\.quickspeak_deps_1.0.2"
)

echo [3/3] 正在检查模型...
"%PYTHON%" download_model.py
if errorlevel 1 goto :failed

echo 正在启动 QuickSpeak 后端：http://localhost:8000
"%PYTHON%" main.py
if errorlevel 1 goto :failed
exit /b 0

:failed
echo.
echo [错误] QuickSpeak 后端安装或启动失败，请检查上方提示。
pause
exit /b 1
