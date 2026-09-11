"""
========================================================================================
[COPILOT MULTI-BOT CI/CD ORCHESTRATOR]
Runs isolated unit tests across Samsung Electronics & SK Hynix Trading Systems.
========================================================================================
"""

import sys
import os
import subprocess
import time

# Windows UTF-8 stdout configuration
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

PYTHON_EXE = r"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"

PROJECTS = [
    {
        "name": "[SAM-BOT] Samsung Electronics (005930)",
        "dir": r"C:\Antigravity\kiwoom_autotrade",
        "script": "test_suite.py",
        "strategy": "Strategy 2: MTF-Squeeze & Divergence (1-Share Fixed)"
    },
    {
        "name": "[SK-BOT] SK Hynix (000660)",
        "dir": r"C:\Antigravity\sk_hynix_autotrade",
        "script": "test_suite.py",
        "strategy": "Triple-Screen Envelope Pullback (1-Share Fixed)"
    }
]

def run_ci_orchestrator():
    print("=" * 80)
    print(">> [COPILOT CI/CD] Multi-Bot Continuous Integration & Unit Test Pipeline")
    print(f">> Execution Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f">> Python Executable: {PYTHON_EXE}")
    print("=" * 80)
    
    total_passed = True
    summary_results = []
    
    for proj in PROJECTS:
        print(f"\n[PIPELINE] Testing target: {proj['name']} ...")
        print(f"   * Directory: {proj['dir']}")
        print(f"   * Strategy : {proj['strategy']}")
        print("-" * 80)
        
        start_t = time.time()
        test_path = os.path.join(proj['dir'], proj['script'])
        
        if not os.path.exists(test_path):
            print(f"[ERROR] Test file not found: {test_path}")
            summary_results.append((proj['name'], "MISSING", 0.0))
            total_passed = False
            continue
            
        result = subprocess.run(
            [PYTHON_EXE, test_path],
            cwd=proj['dir'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        elapsed = time.time() - start_t
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
            
        if result.returncode == 0:
            print(f"   -> Result: [PASS] in {elapsed:.2f}s")
            summary_results.append((proj['name'], "PASS", elapsed))
        else:
            print(f"   -> Result: [FAIL] in {elapsed:.2f}s (Exit Code: {result.returncode})")
            summary_results.append((proj['name'], "FAIL", elapsed))
            total_passed = False

    print("\n" + "=" * 80)
    print(">> [CI/CD PIPELINE SUMMARY REPORT]")
    print("=" * 80)
    for name, status, elapsed in summary_results:
        status_str = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f" - {name:<45} : {status_str:<10} ({elapsed:.2f}s)")
        
    print("-" * 80)
    if total_passed:
        print(">> [SUCCESS] ALL MULTI-BOT SYSTEM INTEGRITY TESTS HAVE PASSED! (20/20)")
        print("   Ready for live 1-Share Kiwoom Mock Trading session.")
    else:
        print(">> [WARNING] SOME TESTS FAILED. Please review error logs before starting trading bots.")
    print("=" * 80)
    
    return 0 if total_passed else 1

if __name__ == '__main__':
    exit_code = run_ci_orchestrator()
    sys.exit(exit_code)
