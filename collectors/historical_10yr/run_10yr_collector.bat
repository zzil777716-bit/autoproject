@echo off
chcp 65001 > nul
echo [Antigravity 10-Year Stock Collector Starting...]
"C:\Users\HONG\AppData\Local\Programs\Python\Python310-32\python.exe" "C:\Antigravity\collectors\historical_10yr\collect_10yr_stocks.py"
echo [Collector Finished]
