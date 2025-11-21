@echo off
echo Stopping Minecraft Status Monitor...
REM Try to kill by window title first (fastest)
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq Minecraft Monitor*" 2>nul

REM Fallback: Use PowerShell to find by command line (works even if wmic is missing)
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*minecraft_status_monitor.py*' } | ForEach-Object { Write-Host 'Killing process ' $_.ProcessId; Stop-Process -Id $_.ProcessId -Force }"

echo Done.
pause
