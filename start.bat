@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
title Vinu x Bhuu Private Friendship Archive
color 0D

echo ==============================================================================
echo        VINU x BHUU - PRIVATE WHATSAPP FRIENDSHIP ARCHIVE
echo ==============================================================================
echo [*] Initializing Private Archive...
echo.

set "PY_CMD="

:: 1. Check standard python in PATH
python --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :run
)

:: 2. Check py launcher
py -3 --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py -3"
    goto :run
)
py --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :run
)

:: 3. Check AppData local python installs
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :run
    )
)

:: 4. Check Program Files
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :run
    )
)

:: 5. Check Program Files (x86)
for /d %%D in ("%ProgramFiles(x86)%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :run
    )
)

:: 6. Check C:\Python3*
for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY_CMD="%%D\python.exe""
        goto :run
    )
)

:: 7. Check WindowsApps Microsoft Store Python
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set "PY_CMD="%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe""
    goto :run
)

color 0C
echo ==============================================================================
echo  [ERROR] Python is not installed or not found on this computer!
echo ==============================================================================
echo.
echo Please install Python 3.10+ from: https://www.python.org/downloads/
echo (Make sure to check "Add Python to PATH" during installation)
echo.
pause
exit /b 1

:run
%PY_CMD% start_archive.py
