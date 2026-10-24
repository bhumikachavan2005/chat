@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
title Vinu x Bhuu Private Archive - One-Click Installer
color 0B

echo ==============================================================================
echo        VINU x BHUU - PRIVATE WHATSAPP ARCHIVE ONE-CLICK INSTALLER
echo ==============================================================================
echo.

set "PY_CMD="

:: 1. Check standard python in PATH
python --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :found_python
)

:: 2. Check py launcher
py -3 --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    goto :found_python
)
py --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

:: 3. Check AppData local python installs
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :found_python
    )
)

:: 4. Check Program Files
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :found_python
    )
)

:: 5. Check Program Files (x86)
for /d %%D in ("%ProgramFiles(x86)%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :found_python
    )
)

:: 6. Check C:\Python3*
for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :found_python
    )
)

:: 7. Check WindowsApps Microsoft Store Python
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set "PY_CMD="%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe""
    goto :found_python
)

color 0C
echo ==============================================================================
echo  [ERROR] Python is not installed or not found on this computer!
echo ==============================================================================
echo.
echo Please download and install Python 3.10+ from: https://www.python.org/downloads/
echo (IMPORTANT: Make sure to check the box "Add Python to PATH" during install)
echo.
pause
exit /b 1

:found_python
echo [*] Python detected on this system:
%PY_CMD% --version
echo.

echo [*] Installing required packages (FastAPI, Uvicorn, Argon2, Cryptography)...
%PY_CMD% -m pip install fastapi uvicorn argon2-cffi cryptography python-multipart

if %errorlevel% neq 0 (
    echo [*] Retrying installation in user mode...
    %PY_CMD% -m pip install --user fastapi uvicorn argon2-cffi cryptography python-multipart
)

echo.
echo [*] Initializing database and verifying setup...
%PY_CMD% -c "import sys, os; sys.path.insert(0, os.getcwd()); from backend.database import init_db; init_db(); print('[+] Database verified successfully.')"

color 0A
echo.
echo ==============================================================================
echo     [SUCCESS] Everything is installed and ready to go!
echo ==============================================================================
echo.
echo You can now launch your private archive anytime by double-clicking:
echo   --^> start.bat
echo.
echo ==============================================================================
echo.
set /p START_NOW="Would you like to start the archive now? (Y/N, default=Y): "
if /i "%START_NOW%"=="" set START_NOW=Y
if /i "%START_NOW%"=="Y" (
    echo Starting archive...
    %PY_CMD% start_archive.py
)
