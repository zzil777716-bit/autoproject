import os
import sys
import win32com.client

desktop = r"C:\Users\HONG\Desktop"
python_exe = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
shell = win32com.client.Dispatch("WScript.Shell")

# 1. Antigravity_Dashboard.bat
bat_dash_code = '@echo off\r\ncd /d C:\\Antigravity\r\n"C:\\Users\\HONG\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe" C:\\Antigravity\\gui_launcher.py\r\n'
bat_dash_path = os.path.join(desktop, "Antigravity_Dashboard.bat")
with open(bat_dash_path, "wb") as f:
    f.write(bat_dash_code.encode("ascii"))

# 2. Antigravity_Console.bat
bat_con_code = '@echo off\r\ncd /d C:\\Antigravity\r\n"C:\\Users\\HONG\\AppData\\Local\\Programs\\Python\\Python310-32\\python.exe" C:\\Antigravity\\multibot_launcher.py\r\npause\r\n'
bat_con_path = os.path.join(desktop, "Antigravity_Console.bat")
with open(bat_con_path, "wb") as f:
    f.write(bat_con_code.encode("ascii"))

# 3. Shortcut 1: Antigravity_Dashboard.lnk
lnk1 = os.path.join(desktop, "Antigravity_Dashboard.lnk")
s1 = shell.CreateShortCut(lnk1)
s1.TargetPath = python_exe
s1.Arguments = r"C:\Antigravity\gui_launcher.py"
s1.WorkingDirectory = r"C:\Antigravity"
s1.Description = "Antigravity Trading Dashboard"
s1.Save()

# 4. Shortcut 2: Antigravity_Console.lnk
lnk2 = os.path.join(desktop, "Antigravity_Console.lnk")
s2 = shell.CreateShortCut(lnk2)
s2.TargetPath = python_exe
s2.Arguments = r"C:\Antigravity\multibot_launcher.py"
s2.WorkingDirectory = r"C:\Antigravity"
s2.Description = "Antigravity Multi-Bot Launcher"
s2.Save()

print(">> [SUCCESS] Clean Desktop Launchers Created!")
