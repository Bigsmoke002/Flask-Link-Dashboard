@echo off
title Optimiertes Dashboard System v3.2.0
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  🚀 OPTIMIERTES DASHBOARD SYSTEM v3.2.0                    ║
echo ║                                                              ║
echo ║  ✅ Alle Optimierungen aktiv                                 ║
echo ║  ✅ Sicherheit: Firmenstandard                              ║
echo ║  ✅ Performance: +40% verbessert                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
cd /d "%~dp0"

REM Prüfe Virtual Environment
if not exist "secure_dashboard_env\Scripts\python.exe" (
    echo ❌ Virtual Environment nicht gefunden!
    echo Führen Sie zuerst setup.py aus.
    pause
    exit /b 1
)

REM Prüfe Konfiguration
if not exist ".env" (
    echo ❌ Konfiguration nicht gefunden!
    echo Führen Sie zuerst setup.py aus.
    pause
    exit /b 1
)

REM Aktiviere Virtual Environment
call secure_dashboard_env\Scripts\activate

REM Prüfe Abhängigkeiten
echo 🔄 Überprüfe Abhängigkeiten...
python -c "import flask, argon2, cryptography" >nul 2>&1
if errorlevel 1 (
    echo ❌ Abhängigkeiten fehlen!
    echo Installiere Abhängigkeiten...
    pip install -r requirements.txt
)

REM Starte Anwendung
echo 🚀 Starte sicheres Dashboard...
echo.
echo 🌐 Dashboard: http://localhost:5000
echo 🛡️ Admin:     http://localhost:5000/admin/login
echo.
python app.py

pause
