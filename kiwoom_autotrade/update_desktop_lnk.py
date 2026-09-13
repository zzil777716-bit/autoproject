import os
import subprocess

desktop_dir = r"C:\Users\HONG\Desktop"
vbs_script = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{desktop_dir}\\키움_자동매매_통합런처.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\\Windows\\System32\\cmd.exe"
oLink.Arguments = "/c ""D:\\ANTIGRAVITY(자동매매)\\kiwoom_autotrade\\launch_all_bots.bat"""
oLink.WorkingDirectory = "D:\\ANTIGRAVITY(자동매매)\\kiwoom_autotrade"
oLink.Description = "키움증권 삼성전자 & SK하이닉스 1주 모의투자 통합 자동매매 런처"
oLink.IconLocation = "shell32.dll, 43"
oLink.Save
'''

vbs_path = r"D:\ANTIGRAVITY(자동매매)\kiwoom_autotrade\update_lnk_final.vbs"
with open(vbs_path, "w", encoding="cp949") as f:
    f.write(vbs_script)

subprocess.run(["cscript", "//nologo", vbs_path], check=True)
if os.path.exists(vbs_path):
    os.remove(vbs_path)

print("Desktop .lnk shortcut updated successfully!")
