@echo off
title Antigravity Multi-Bot Control Center
cd /d "C:\Antigravity\kiwoom_autotrade"
"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe" "C:\Antigravity\kiwoom_autotrade\multibot_launcher.py"
if errorlevel 1 pause
