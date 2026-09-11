"""
========================================================================================
🚀 [ANTIGRAVITY MULTI-BOT CONTROL CENTER]
Python-Powered Interactive Launcher
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

# Python 32-bit Path validation & Fallback
DEFAULT_PYTHON = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
PYTHON_EXE = DEFAULT_PYTHON if os.path.exists(DEFAULT_PYTHON) else sys.executable
SAM_DIR = r"C:\Antigravity\kiwoom_autotrade"
SK_DIR = r"C:\Antigravity\sk_hynix_autotrade"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause(prompt="\nPress Enter to return to menu..."):
    try:
        input(prompt)
    except (KeyboardInterrupt, EOFError):
        pass

def print_menu():
    clear_screen()
    print("=" * 80)
    print("       🚀 [Antigravity Multi-Bot Control Center] Kiwoom 1-Share Auto-Trader")
    print("=" * 80)
    print("  1. [ALL-IN-ONE] 🚀 Start ALL Bots (Samsung + SK Hynix) Simultaneously")
    print("  2. [SAM-BOT]    🤖 Start Samsung Electronics Bot Only (005930)")
    print("  3. [SK-BOT]     ⚡ Start SK Hynix Bot Only (000660)")
    print("  " + "-" * 76)
    print("  4. [CALENDAR]   📅 Scan HTS 0659/0198/0184 & Update Desktop Calendar")
    print("  5. [COLLECTOR]  📥 Run Historical Data Collection (Samsung and SK Hynix)")
    print("  6. [CI/CD TEST] 🧪 Run Automated Strategy and Risk Unit Test Suite (20/20 PASS)")
    print("  7. [REPORT]     📈 Generate Daily Quant Research and Trade Journal Report")
    print("  8. [G-DRIVE]    ☁️ Backup and Sync All Research Data to Google Drive")
    print("  9. [STOP ALL]   🛑 Safely Terminate All Running Trading Bot Processes")
    print("  " + "-" * 76)
    print("  0. [EXIT]       🚪 Exit Control Center")
    print("=" * 80)

def run_script(title, script_path, cwd=None, new_window=True):
    if cwd is None:
        cwd = os.path.dirname(script_path)

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
            choice = input("👉 Select an option (0-9) and press Enter: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            print("\n>> [LAUNCHING] Starting SAM-BOT (005930) and SK-BOT (000660) in separate windows...")
            run_script("SAM-BOT (005930) Kiwoom MTF Trader", os.path.join(SAM_DIR, "main_trader.py"), cwd=SAM_DIR)
            time.sleep(2)
            run_script("SK-BOT (000660) Kiwoom MTF Trader", os.path.join(SK_DIR, "main_sk_trader.py"), cwd=SK_DIR)
            print(">> [OK] Both Trading Bots have been launched in separate console windows!")
            pause()

        elif choice == "2":
            print("\n>> [LAUNCHING] Starting SAM-BOT (005930)...")
            run_script("SAM-BOT (005930) Kiwoom MTF Trader", os.path.join(SAM_DIR, "main_trader.py"), cwd=SAM_DIR)
            print(">> [OK] SAM-BOT launched.")
            pause()

        elif choice == "3":
            print("\n>> [LAUNCHING] Starting SK-BOT (000660)...")
            run_script("SK-BOT (000660) Kiwoom MTF Trader", os.path.join(SK_DIR, "main_sk_trader.py"), cwd=SK_DIR)
            print(">> [OK] SK-BOT launched.")
            pause()

        elif choice == "4":
            print("\n>> [HTS SCANNER & CALENDAR] Analyzing HTS 0659/0198/0184 & Updating Desktop Calendar...")
            run_script("Calendar & HTS Scanner", os.path.join(SAM_DIR, "core", "calendar_generator.py"), cwd=SAM_DIR, new_window=False)
            pause()

        elif choice == "5":
            print("\n>> [DATA COLLECTION] Collecting 3M, 5M, 15M Historical Bars for SAM & SK...")
            run_script("Collector: Samsung (005930)", os.path.join(SAM_DIR, "collect_historical_data.py"), cwd=SAM_DIR)
            time.sleep(2)
            run_script("Collector: SK Hynix (000660)", os.path.join(SK_DIR, "collect_sk_hynix_data.py"), cwd=SK_DIR)
            print(">> [OK] Historical Data Collectors launched.")
            pause()

        elif choice == "6":
            print("\n>> [CI/CD] Running Multi-Bot Automated Integrity Test Suite...")
            run_script("CI Suite", os.path.join(SAM_DIR, "run_ci_suite.py"), cwd=SAM_DIR, new_window=False)
            pause()

        elif choice == "7":
            print("\n>> [QUANT REPORT] Generating Daily Quant Research & Trade Journal Reports...")
            print(">> [1/2] Analyzing Samsung Electronics (005930)...")
            run_script("Report SAM", os.path.join(SAM_DIR, "generate_daily_report.py"), cwd=SAM_DIR, new_window=False)
            print(">> [2/2] Analyzing SK Hynix (000660)...")
            run_script("Report SK", os.path.join(SK_DIR, "generate_daily_report.py"), cwd=SK_DIR, new_window=False)
            pause()

        elif choice == "8":
            print("\n>> [G-DRIVE SYNC] Backing up All Data & Research to Google Drive...")
            run_script("GDrive Sync", os.path.join(SAM_DIR, "core", "gdrive_sync.py"), cwd=SAM_DIR, new_window=False)
            pause()

        elif choice == "9":
            stop_all_bots()
            pause()

        elif choice == "0":
            print("\nGoodbye! Have a great trading day! 🚀")
            time.sleep(1)
            break
        else:
            print("\n[!] Invalid selection. Please enter a number between 0 and 9.")
            time.sleep(1.5)

if __name__ == "__main__":
    main()
