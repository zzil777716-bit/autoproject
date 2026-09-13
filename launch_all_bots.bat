@echo off
chcp 65001 > nul
title Antigravity Multi-Bot Control Center

set "PYTHON_EXE=C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

cd /d "D:\ANTIGRAVITY(자동매매)"
"%PYTHON_EXE%" "D:\ANTIGRAVITY(자동매매)\multibot_launcher.py"
pause
