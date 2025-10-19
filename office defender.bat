@echo off
echo Полное удаление WPS Office...
echo.

taskkill /f /im wps.exe >nul 2>&1
taskkill /f /im et.exe >nul 2>&1  
taskkill /f /im wpp.exe >nul 2>&1
taskkill /f /im ksolaunch.exe >nul 2>&1
timeout /t 3 /nobreak >nul
rd /s /q "C:\Program Files\Kingsoft" >nul 2>&1
rd /s /q "C:\Program Files (x86)\Kingsoft" >nul 2>&1
rd /s /q "%LOCALAPPDATA%\Kingsoft" >nul 2>&1
rd /s /q "%APPDATA%\Kingsoft" >nul 2>&1
reg delete "HKLM\SOFTWARE\Kingsoft" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\WOW6432Node\Kingsoft" /f >nul 2>&1
reg delete "HKCU\Software\Kingsoft" /f >nul 2>&1
echo WPS Office полностью удален!
pause