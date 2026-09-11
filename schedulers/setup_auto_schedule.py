"""
========================================================================================
⚙️ [SETUP: WINDOWS TASK SCHEDULER REGISTRATION - NXT & SOR COMPLIANT]
Registers a Windows Scheduled Task to pop up the PyQt5 Trading Dashboard every weekday at 07:50 AM
(10 minutes before Nextrade NXT Pre-Market 08:00 AM opening).
========================================================================================
"""

import os
import sys
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable
BASE_DIR = r"C:\Antigravity"
DASHBOARD_SCRIPT = os.path.join(BASE_DIR, "dashboard_app.py")
BAT_PATH = r"C:\Users\HONG\Desktop\Antigravity_Dashboard.bat"
TASK_NAME = "Antigravity_Morning_Trading_Trigger"

def register_task(time_str: str = "07:50"):
    """NXT 프리마켓(08:00) 대비 07:50 AM 윈도우 스케줄러 등록"""
    # 윈도우 배치 또는 파이썬 대시보드 직접 실행 등록
    target_cmd = f'"{PYTHON_EXE}" "{DASHBOARD_SCRIPT}"'
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", target_cmd,
        "/sc", "weekly",
        "/d", "MON,TUE,WED,THU,FRI",
        "/st", time_str,
        "/f"
    ]
    print(f">> [TaskScheduler] 윈도우 작업 스케줄러 등록 중: 매주 월~금 {time_str} (NXT 프리마켓 08:00 대비)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f">> [OK] ✅ 윈도우 작업 스케줄러 등록 완료: '{TASK_NAME}'")
        print(f"       매 영업일(월~금) 오전 {time_str}에 Antigravity PyQt5 지휘통제소가 자동으로 화면 전면에 팝업됩니다.")
    else:
        print(f">> [INFO] schtasks 실행 결과: {res.stdout or res.stderr}")

def unregister_task():
    cmd = ["schtasks", "/delete", "/tn", TASK_NAME, "/f"]
    subprocess.run(cmd, capture_output=True)
    print(f">> [OK] 윈도우 작업 스케줄러 등록 해제 완료: '{TASK_NAME}'")

if __name__ == "__main__":
    if "--remove" in sys.argv:
        unregister_task()
    else:
        register_task("07:50")
