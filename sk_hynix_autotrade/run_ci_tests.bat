@echo off
chcp 65001 > nul
title [CI/CD Automated Unit Tests] Kiwoom Multi-Bot Test Suite
cd /d "%~dp0"
echo ==============================================================================
echo  🚀 [COPILOT CI/CD] Starting Multi-Bot Automated Integrity Test Suite
echo ==============================================================================
echo.
"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe" run_ci_suite.py
echo.
pause
