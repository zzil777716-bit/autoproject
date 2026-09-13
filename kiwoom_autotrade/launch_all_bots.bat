@echo off
title Antigravity Multi-Bot Control Center
cd /d "D:\ANTIGRAVITY(자동매매)\kiwoom_autotrade"
"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe" "D:\ANTIGRAVITY(자동매매)\kiwoom_autotrade\multibot_launcher.py"
if errorlevel 1 pause
