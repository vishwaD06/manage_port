@echo off
title Smart Food Waste Reduction and Donation System
cd /d "%~dp0"

echo ======================================================================
echo   Smart Food Waste Reduction and Donation Management System
echo ======================================================================
echo.

echo [1/2] Checking MariaDB Database Server...
tasklist /fi "imagename eq mariadbd.exe" 2>nul | findstr /i "mariadbd.exe" >nul
if errorlevel 1 (
    echo [INFO] Starting MariaDB server in the background...
    start "MariaDB Server" /min "C:\Users\prath\AppData\Local\Programs\MariaDB\mariadb-11.4.13-winx64\bin\mariadbd.exe" --defaults-file="C:\Users\prath\AppData\Local\Programs\MariaDB\mariadb-11.4.13-winx64\data\my.ini" --console
    timeout /t 3 /nobreak >nul
) else (
    echo [OK] MariaDB server is active on port 3306.
)

echo [2/2] Launching Flask Web Server...
echo.
echo ======================================================================
echo   Web Application URL: http://127.0.0.1:5000
echo ======================================================================
echo.
python app.py
pause
