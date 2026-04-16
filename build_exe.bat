@echo off
echo ========================================================
echo ASR Floating App - Build Script (Windows)
echo ========================================================

echo.
echo [1/3] Checking dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to install dependencies. Please check your Python environment.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist\ASR_Floating_App" rmdir /s /q "dist\ASR_Floating_App"

echo.
echo [3/3] Building Executable (Directory)...
REM 打包为包含 _internal 文件夹的目录结构
pyinstaller --clean --noconfirm --windowed --name "ASR_Floating_App" "app/main.py"

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo Build Successful!
    echo You can find your executable at: dist\ASR_Floating_App\ASR_Floating_App.exe
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Build Failed! Please check the error messages above.
    echo ========================================================
)

pause
