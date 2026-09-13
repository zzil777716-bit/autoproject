# ==============================================================================
# [Copilot Multi-Bot Management Script for PowerShell]
# Provides CLI control & health check for Samsung & SK Hynix Trading Bots
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PythonExe = "C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe"
$SamDir = "D:\ANTIGRAVITY(자동매매)\kiwoom_autotrade"
$SkDir = "D:\ANTIGRAVITY(자동매매)\sk_hynix_autotrade"

function Show-Menu {
    Clear-Host
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host "       🚀 [Copilot Multi-Bot Control Center] PowerShell Edition" -ForegroundColor Yellow
    Write-Host "==============================================================================" -ForegroundColor Cyan
    Write-Host " 1. [START ALL]  🚀 Start Both Samsung & SK Hynix Bots (Separate Windows)" -ForegroundColor Green
    Write-Host " 2. [SAM-BOT]    🤖 Start Samsung Electronics (005930) Bot Only" -ForegroundColor White
    Write-Host " 3. [SK-BOT]     ⚡ Start SK Hynix (000660) Bot Only" -ForegroundColor White
    Write-Host " ------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host " 4. [COLLECTOR]  📥 Sync Historical Candles (SAM + SK)" -ForegroundColor Cyan
    Write-Host " 5. [CI/CD TEST] 🧪 Run Automated Multi-Bot Unit Test Suite" -ForegroundColor Magenta
    Write-Host " 6. [MONITOR]    📊 Check Bot Process Status & Health" -ForegroundColor Yellow
    Write-Host " 7. [STOP ALL]   🛑 Safely Stop All Trading Bots" -ForegroundColor Red
    Write-Host " ------------------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host " 0. [EXIT]       🚪 Exit" -ForegroundColor Gray
    Write-Host "==============================================================================" -ForegroundColor Cyan
}

function Start-AllBots {
    Write-Host "`n>> Starting SAM-BOT (005930) & SK-BOT (000660)..." -ForegroundColor Green
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d $SamDir && $PythonExe $SamDir\main_trader.py" -WindowStyle Normal
    Start-Sleep -Seconds 2
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d $SkDir && $PythonExe $SkDir\main_sk_trader.py" -WindowStyle Normal
    Write-Host ">> [OK] Both bots have been launched successfully!" -ForegroundColor Green
    Pause
}

function Run-CiTests {
    Write-Host "`n>> Executing CI/CD Unit Test Suite..." -ForegroundColor Magenta
    & $PythonExe "$SkDir\run_ci_suite.py"
    Pause
}

function Check-Status {
    Write-Host "`n>> Active Python Trading Processes:" -ForegroundColor Yellow
    Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, @{Name="Memory (MB)"; Expression={[math]::Round($_.WorkingSet64/1MB, 2)}}, StartTime | Format-Table -AutoSize
    Pause
}

function Stop-AllBots {
    Write-Host "`n>> Terminating all active Python Bot processes..." -ForegroundColor Red
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host ">> [OK] All Bot processes stopped." -ForegroundColor Green
    Pause
}

do {
    Show-Menu
    $choice = Read-Host "👉 Select an option (0-7)"
    switch ($choice) {
        "1" { Start-AllBots }
        "2" { Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d $SamDir && $PythonExe $SamDir\main_trader.py" }
        "3" { Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d $SkDir && $PythonExe $SkDir\main_sk_trader.py" }
        "4" { 
            Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d $SamDir && $PythonExe $SamDir\collect_historical_data.py"
            Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d $SkDir && $PythonExe $SkDir\collect_sk_hynix_data.py"
        }
        "5" { Run-CiTests }
        "6" { Check-Status }
        "7" { Stop-AllBots }
        "0" { Write-Host "Good bye! 🚀" -ForegroundColor Cyan; break }
        Default { Write-Host "Invalid option." -ForegroundColor Red; Start-Sleep -Seconds 1 }
    }
} while ($choice -ne "0")
