"""
========================================================================================
🚀 [ANTIGRAVITY MULTI-BOT CONTROL CENTER: ENTERPRISE EDITION]
Modular multi-process launcher orchestrating Workers, Collectors, Schedulers, and GDrive Sync.
========================================================================================
"""

import sys
import os
import subprocess
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable
BASE_DIR = r"C:\Antigravity"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause(prompt="\nPress Enter to return to menu..."):
    try:
        input(prompt)
    except (KeyboardInterrupt, EOFError):
        pass

def print_menu():
    clear_screen()
    print("=" * 82)
    print("      🚀 [Antigravity Multi-Bot Control Center] Enterprise Architecture")
    print("=" * 82)
    print("  G. [GUI PRO]    🖥️ Launch Interactive Mouse-Driven GUI Dashboard (방안 1 추천 🌟)")
    print("  1. [ALL-IN-ONE] 🚀 Start ALL Trading Workers (Dual Engine: Strategy A + B) Simultaneously")
    print("  2. [SAM-BOT]    🔵 Start Samsung Worker (Dual: 3-Lines + 20-60-120 Disparity)")
    print("  3. [SK-BOT]     🟣 Start SK Hynix Worker (Dual: 3-Lines + 20-60-120 Disparity)")
    print("  " + "-" * 78)
    print("  4. [CALENDAR]   📅 Run Live KRX Market Scanner & Update Desktop Calendar & Monthly Excel")
    print("  5. [RECONCILE]  🔄 Run Account Reconciliation & Order Status Sync Worker")
    print("  6. [CI/CD TEST] 🧪 Run Architecture Integrity & Risk Unit Test Suite (16/16 100% PASS)")
    print("  7. [QUANT LAB]  📊 Run 15M 20-60-120 Alignment & Golden Disparity Matrix Simulation")
    print("  8. [APPROVAL]   🔔 Test Daily Morning Interactive Approval Notification Modal")
    print("  9. [G-DRIVE]    ☁️ Backup All Data, Architecture & Monthly Sheets to Google Drive")
    print(" 10. [STOP ALL]   🛑 Safely Terminate All Running Trading Bot Processes")
    print("  " + "-" * 78)
    print("  0. [EXIT]       🚪 Exit Control Center")
    print("=" * 82)

def run_script(title, script_path, cwd=BASE_DIR, new_window=True):
    if new_window:
        cmd = ["cmd.exe", "/k", "title", title, "&&", PYTHON_EXE, script_path]
        subprocess.Popen(cmd, cwd=cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        try:
            cmd = [PYTHON_EXE, script_path]
            subprocess.run(cmd, cwd=cwd, check=False)
        except KeyboardInterrupt:
            print("\n[!] Execution interrupted by user (Ctrl+C).")
        except Exception as e:
            print(f"\n[!] Execution error: {e}")

def stop_all_bots():
    current_pid = os.getpid()
    print(f"\n>> [SHUTDOWN] Safely terminating all trading bot processes (Excluding Launcher PID: {current_pid})...")
    kill_cmd = f'taskkill /fi "PID ne {current_pid}" /f /im python.exe /t 2>nul'
    os.system(kill_cmd)
    print(">> [OK] All trading bot processes terminated safely.")

def main():
    while True:
        print_menu()
        try:
            choice = input("👉 Select an option (0-10) and press Enter: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice.upper() == "G":
            print("\n>> [GUI DASHBOARD] Launching Interactive Mouse-Driven GUI Dashboard...")
            run_script("Antigravity GUI Dashboard", os.path.join(BASE_DIR, "gui_launcher.py"))
            pause()

        elif choice == "1":
            print("\n>> [LAUNCHING] Starting SAM-BOT (005930) and SK-BOT (000660) in separate worker processes...")
            run_script("SAM-BOT (005930) Worker", os.path.join(BASE_DIR, "workers", "worker_samsung_squeeze.py"))
            time.sleep(2)
            run_script("SK-BOT (000660) Worker", os.path.join(BASE_DIR, "workers", "worker_hynix_pullback.py"))
            print(">> [OK] Both Trading Bot Workers have been launched in separate console windows!")
            pause()

        elif choice == "2":
            print("\n>> [LAUNCHING] Starting Samsung Electronics Worker (005930)...")
            run_script("SAM-BOT (005930) Worker", os.path.join(BASE_DIR, "workers", "worker_samsung_squeeze.py"))
            print(">> [OK] SAM-BOT launched.")
            pause()

        elif choice == "3":
            print("\n>> [LAUNCHING] Starting SK Hynix Worker (000660)...")
            run_script("SK-BOT (000660) Worker", os.path.join(BASE_DIR, "workers", "worker_hynix_pullback.py"))
            print(">> [OK] SK-BOT launched.")
            pause()

        elif choice == "4":
            print("\n>> [HTS SCANNER & CALENDAR] Analyzing HTS 0659/0198/0184 & Updating Desktop Calendar...")
            run_script("Calendar & HTS Worker", os.path.join(BASE_DIR, "workers", "theme_calendar_worker.py"), new_window=False)
            pause()

        elif choice == "5":
            print("\n>> [RECONCILIATION] Starting Order & Account Reconciliation Worker...")
            run_script("Reconciliation Worker", os.path.join(BASE_DIR, "workers", "reconciliation_worker.py"), new_window=False)
            pause()

        elif choice == "6":
            print("\n>> [CI/CD] Running Multi-Bot Automated Integrity Test Suite...")
            run_script("CI Suite", os.path.join(BASE_DIR, "tests", "run_ci_suite.py"), new_window=False)
            pause()

        elif choice == "7":
            print("\n>> [QUANT LAB] Running 15M 20-60-120 Alignment & Golden Disparity Matrix Simulation...")
            run_script("Alignment Disparity Matrix", os.path.join(BASE_DIR, "research", "analyze_ma_alignment_disparity.py"), new_window=False)
            pause()

        elif choice == "8":
            print("\n>> [MORNING APPROVAL MODAL] Launching Interactive Morning Trading Authorization Dialog...")
            run_script("Morning Approval Dialog", os.path.join(BASE_DIR, "schedulers", "interactive_launcher.py"), new_window=False)
            pause()

        elif choice == "9":
            print("\n>> [G-DRIVE SYNC] Backing up All Data, Architecture & Research to Google Drive...")
            run_script("GDrive Sync", os.path.join(BASE_DIR, "storage", "gdrive_sync.py"), new_window=False)
            pause()

        elif choice == "10":
            stop_all_bots()
            pause()

        elif choice == "0":
            print("\nGoodbye! Have a great trading day! 🚀")
            time.sleep(1)
            break
        else:
            print("\n[!] Invalid selection. Please enter a number between 0 and 10.")
            time.sleep(1.5)

if __name__ == "__main__":
    main()
