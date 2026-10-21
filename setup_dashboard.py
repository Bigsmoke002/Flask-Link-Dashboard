#!/usr/bin/env python3
"""
Dashboard Setup Script
======================

Automatische Installation und Einrichtung des Modern Dashboard Systems.
Dieses Script führt eine komplette Neuinstallation durch.

Usage:
    python setup_dashboard.py [--dev] [--port PORT] [--no-virtual-env]

Options:
    --dev              Entwicklungsmodus aktivieren
    --port PORT        Spezifischen Port verwenden (Standard: 5000)
    --no-virtual-env   Kein Virtual Environment erstellen
    --force            Existierende Installation überschreiben

Features:
- Automatische Abhängigkeitsprüfung
- Virtual Environment Setup
- Datenbank-Initialisierung
- Admin-Benutzer Erstellung
- Konfigurationsdateien
- Erste Einrichtung
"""

import os
import sys
import subprocess
import argparse
import platform
import json
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime

# Konfiguration
REQUIRED_PYTHON = (3, 8)
PROJECT_NAME = "Modern Dashboard System"
VERSION = "2.0.0"
VENV_NAME = "dashboard_env"

def check_python_version():
    """Überprüft die Python-Version"""
    current = sys.version_info[:2]
    if current < REQUIRED_PYTHON:
        print(f"❌ Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ erforderlich!")
        print(f"   Aktuelle Version: {current[0]}.{current[1]}")
        print(f"   Bitte aktualisieren Sie Python: https://python.org/downloads/")
        return False

    print(f"✅ Python {current[0]}.{current[1]} - Kompatibel")
    return True

def check_pip():
    """Überprüft ob pip verfügbar ist"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                      check=True, capture_output=True)
        print("✅ pip verfügbar")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip nicht verfügbar!")
        print("   Bitte installieren Sie pip: https://pip.pypa.io/en/stable/installation/")
        return False

def check_git():
    """Überprüft ob git verfügbar ist (optional)"""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        print("✅ git verfügbar")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ git nicht verfügbar (optional)")
        return False

def create_virtual_environment(venv_path):
    """Erstellt Virtual Environment"""
    if venv_path.exists():
        print(f"⚠️ Virtual Environment bereits vorhanden: {venv_path}")
        response = input("Überschreiben? (j/N): ").lower().strip()
        if response not in ['j', 'ja', 'y', 'yes']:
            return True

        # Altes venv entfernen
        import shutil
        shutil.rmtree(venv_path)
        print("🗑️ Altes Virtual Environment entfernt")

    print(f"🔄 Erstelle Virtual Environment: {venv_path}")

    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)],
                      check=True)
        print("✅ Virtual Environment erstellt")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Erstellen des Virtual Environment: {e}")
        return False

def get_venv_python(venv_path):
    """Gibt den Python-Pfad im Virtual Environment zurück"""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def get_venv_pip(venv_path):
    """Gibt den pip-Pfad im Virtual Environment zurück"""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def install_dependencies(venv_path, dev_mode=False):
    """Installiert Python-Abhängigkeiten"""
    pip_path = get_venv_pip(venv_path)

    print("🔄 Installiere Abhängigkeiten...")

    # Basis-Abhängigkeiten
    dependencies = [
        "Flask==3.0.0",
        "Werkzeug==3.0.1",
        "Jinja2==3.1.2",
        "click==8.1.7",
        "itsdangerous==2.1.2",
        "MarkupSafe==2.1.3",
        "blinker==1.7.0"
    ]

    # Entwicklungs-Abhängigkeiten
    if dev_mode:
        dependencies.extend([
            "pytest>=7.0.0",
            "pytest-flask>=1.2.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "flask-testing>=0.8.1"
        ])

    for dep in dependencies:
        try:
            print(f"  📦 Installiere {dep.split('==')[0]}...")
            subprocess.run([str(pip_path), "install", dep],
                          check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Fehler bei Installation von {dep}: {e}")
            return False

    print("✅ Alle Abhängigkeiten installiert")
    return True

def create_requirements_file(dev_mode=False):
    """Erstellt requirements.txt"""
    requirements = [
        "Flask==3.0.0",
        "Werkzeug==3.0.1",
        "Jinja2==3.1.2",
        "click==8.1.7",
        "itsdangerous==2.1.2",
        "MarkupSafe==2.1.3",
        "blinker==1.7.0"
    ]

    with open("requirements.txt", "w") as f:
        for req in requirements:
            f.write(f"{req}\n")

    print("✅ requirements.txt erstellt")

    if dev_mode:
        dev_requirements = [
            "pytest>=7.0.0",
            "pytest-flask>=1.2.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "flask-testing>=0.8.1"
        ]

        with open("requirements-dev.txt", "w") as f:
            for req in dev_requirements:
                f.write(f"{req}\n")

        print("✅ requirements-dev.txt erstellt")

def create_directory_structure():
    """Erstellt die Verzeichnisstruktur"""
    directories = [
        "databases",
        "static",
        "static/css",
        "static/js",
        "static/images",
        "templates",
        "logs",
        "backups"
    ]

    print("🔄 Erstelle Verzeichnisstruktur...")

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  📁 {directory}")

    print("✅ Verzeichnisstruktur erstellt")

def initialize_database():
    """Initialisiert die Datenbanken"""
    print("🔄 Initialisiere Datenbanken...")

    # Admin-Datenbank
    admin_db = Path("databases/admin.db")

    if admin_db.exists():
        print("⚠️ Admin-Datenbank bereits vorhanden")
        response = input("Neu erstellen? (j/N): ").lower().strip()
        if response not in ['j', 'ja', 'y', 'yes']:
            return True
        admin_db.unlink()

    conn = sqlite3.connect(str(admin_db))
    c = conn.cursor()

    # Admin-Tabelle
    c.execute('''CREATE TABLE admin_users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Benutzer-Tabelle
    c.execute('''CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    can_edit_existing BOOLEAN DEFAULT 1,
                    can_add_delete BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    db_path TEXT
                )''')

    # Login-Versuche
    c.execute('''CREATE TABLE login_attempts (
                    id INTEGER PRIMARY KEY,
                    ip_address TEXT,
                    username TEXT,
                    success BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    conn.commit()
    conn.close()

    print("✅ Datenbank-Schema erstellt")

def create_admin_user():
    """Erstellt den Admin-Benutzer"""
    print("🔄 Erstelle Admin-Benutzer...")

    admin_password = secrets.token_urlsafe(16)

    # Importiere Werkzeug für korrektes Passwort-Hashing
    try:
        # Versuche Werkzeug aus dem Virtual Environment zu importieren
        venv_path = Path(VENV_NAME)
        if venv_path.exists():
            venv_python = get_venv_python(venv_path)
            
            # Führe Python-Code im Virtual Environment aus, um den Hash zu erstellen
            hash_script = f"""
import sys
sys.path.insert(0, '.')
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash('{admin_password}')
print(password_hash)
"""
            
            result = subprocess.run([str(venv_python), "-c", hash_script], 
                                   capture_output=True, text=True, check=True)
            password_hash = result.stdout.strip()
            
        else:
            # Fallback: Versuche lokales Werkzeug
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(admin_password)
            
    except (ImportError, subprocess.CalledProcessError):
        print("⚠️ Werkzeug nicht verfügbar - erstelle temporären Hash")
        print("   Dieser wird beim ersten App-Start automatisch konvertiert")
        password_hash = f"TEMP_HASH_{admin_password}"

    conn = sqlite3.connect("databases/admin.db")
    c = conn.cursor()

    c.execute("INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
             ('admin', password_hash))

    conn.commit()
    conn.close()

    # Admin-Zugangsdaten speichern
    with open('admin_credentials.txt', 'w') as f:
        f.write(f"Admin Username: admin\n")
        f.write(f"Admin Password: {admin_password}\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\nIMPORTANT: Change this password after first login!\n")

    print("✅ Admin-Benutzer erstellt")
    print(f"   Username: admin")
    print(f"   Password: {admin_password}")
    print(f"   (Gespeichert in: admin_credentials.txt)")

    return admin_password

def create_config_files(port=5000, dev_mode=False):
    """Erstellt Konfigurationsdateien"""
    print("🔄 Erstelle Konfigurationsdateien...")

    # .env Datei
    env_content = f"""# Dashboard Configuration
FLASK_PORT={port}
FLASK_ENV={'development' if dev_mode else 'production'}
DATABASE_DIR=databases
SECRET_KEY={secrets.token_hex(32)}

# Security Settings
RATE_LIMIT_ENABLED=true
SESSION_LIFETIME=3600
MAX_LOGIN_ATTEMPTS=5

# Features
THEME_SYSTEM_ENABLED=true
USER_REGISTRATION_ENABLED=false
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    # Startup Script
    if platform.system() == "Windows":
        startup_script = f"""@echo off
echo Starting Dashboard System...
cd /d "%~dp0"
call {VENV_NAME}\\Scripts\\activate
python app.py
pause
"""
        with open('start_dashboard.bat', 'w') as f:
            f.write(startup_script)
        print("  📄 start_dashboard.bat")
    else:
        startup_script = f"""#!/bin/bash
echo "Starting Dashboard System..."
cd "$(dirname "$0")"
source {VENV_NAME}/bin/activate
python app.py
"""
        with open('start_dashboard.sh', 'w') as f:
            f.write(startup_script)
        os.chmod('start_dashboard.sh', 0o755)
        print("  📄 start_dashboard.sh")

    # .gitignore
    gitignore_content = """# Virtual Environment
dashboard_env/
venv/
env/

# Databases
databases/
*.db
*.sqlite

# Credentials
admin_credentials.txt
.env

# Logs
logs/
*.log

# Backups
backups/
database_backups/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""

    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)

    print("✅ Konfigurationsdateien erstellt")

def create_example_user(venv_path):
    """Erstellt einen Beispiel-Benutzer"""
    print("🔄 Erstelle Beispiel-Benutzer...")

    demo_password = "demo123"

    # Erstelle korrekten Hash für Demo-User
    try:
        if venv_path and venv_path.exists():
            venv_python = get_venv_python(venv_path)
            
            hash_script = f"""
import sys
sys.path.insert(0, '.')
from werkzeug.security import generate_password_hash
password_hash = generate_password_hash('{demo_password}')
print(password_hash)
"""
            
            result = subprocess.run([str(venv_python), "-c", hash_script], 
                                   capture_output=True, text=True, check=True)
            demo_hash = result.stdout.strip()
            
        else:
            from werkzeug.security import generate_password_hash
            demo_hash = generate_password_hash(demo_password)
            
    except (ImportError, subprocess.CalledProcessError):
        print("⚠️ Werkzeug nicht verfügbar - erstelle temporären Hash für Demo-User")
        demo_hash = f"TEMP_HASH_{demo_password}"

    # Beispiel-Benutzerdatenbank
    user_db = Path("databases/user_demo.db")

    conn = sqlite3.connect(str(user_db))
    c = conn.cursor()

    # Reiter-Tabelle
    c.execute('''CREATE TABLE tabs (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT,
                    color TEXT DEFAULT '#5865f2',
                    icon TEXT DEFAULT '📁',
                    position INTEGER,
                    parent_id INTEGER,
                    is_folder BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Benutzereinstellungen
    c.execute('''CREATE TABLE user_settings (
                    id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'default',
                    sidebar_collapsed BOOLEAN DEFAULT 0,
                    sidebar_width INTEGER DEFAULT 280,
                    show_icons BOOLEAN DEFAULT 1,
                    auto_save BOOLEAN DEFAULT 1,
                    animations_enabled BOOLEAN DEFAULT 1,
                    compact_mode BOOLEAN DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Theme-Historie
    c.execute('''CREATE TABLE theme_history (
                    id INTEGER PRIMARY KEY,
                    theme TEXT NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Standard-Einstellungen
    c.execute("INSERT INTO user_settings (id) VALUES (1)")

    # Beispiel-Reiter
    example_tabs = [
        (1, "Dashboard", "", "#5865f2", "🏠", 1, None, True),
        (2, "Entwicklung", "", "#8b5cf6", "💻", 2, None, True),
        (3, "GitHub", "https://github.com", "#333333", "🐙", 1, 2, False),
        (4, "Stack Overflow", "https://stackoverflow.com", "#f48024", "📚", 2, 2, False),
        (5, "Google", "https://google.com", "#4285f4", "🔍", 3, None, False),
        (6, "YouTube", "https://youtube.com", "#ff0000", "📺", 4, None, False),
    ]

    c.executemany("""INSERT INTO tabs
                     (id, name, url, color, icon, position, parent_id, is_folder)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", example_tabs)

    conn.commit()
    conn.close()

    # Benutzer zur Admin-DB hinzufügen
    conn = sqlite3.connect("databases/admin.db")
    c = conn.cursor()

    c.execute("""INSERT INTO users
                 (username, password_hash, can_edit_existing, can_add_delete, db_path)
                 VALUES (?, ?, ?, ?, ?)""",
              ('demo', demo_hash, True, True, 'databases/user_demo.db'))

    conn.commit()
    conn.close()

    print("✅ Demo-Benutzer erstellt")
    print("   Username: demo")
    print("   Password: demo123")

def create_documentation():
    """Erstellt grundlegende Dokumentation"""
    print("🔄 Erstelle Dokumentation...")

    # Kurze README für den lokalen Ordner
    readme_content = f"""# {PROJECT_NAME} - Lokale Installation

## Schnellstart

1. **Dashboard starten:**
   ```bash
   # Windows
   start_dashboard.bat

   # Linux/Mac
   ./start_dashboard.sh
   ```

2. **Oder manuell:**
   ```bash
   source {VENV_NAME}/bin/activate  # Linux/Mac
   {VENV_NAME}\\Scripts\\activate   # Windows
   python app.py
   ```

3. **Zugriff:**
   - Dashboard: http://localhost:5000
   - Admin-Panel: http://localhost:5000/admin/login

## Zugangsdaten

- **Admin**: Siehe `admin_credentials.txt`
- **Demo-User**: demo / demo123

## Verzeichnisstruktur

```
dashboard-system/
├── app.py                  # Hauptanwendung
├── requirements.txt        # Python-Abhängigkeiten
├── admin_credentials.txt   # Admin-Zugangsdaten
├── .env                   # Konfiguration
├── {VENV_NAME}/           # Virtual Environment
├── databases/             # SQLite-Datenbanken
├── templates/             # HTML-Templates
├── static/               # CSS, JS, Bilder
└── logs/                 # Log-Dateien
```

## Konfiguration

Bearbeiten Sie `.env` für erweiterte Einstellungen.

## Support

Bei Problemen siehe die vollständige Dokumentation im Repository.
"""

    with open('README_LOCAL.md', 'w') as f:
        f.write(readme_content)

    print("✅ Lokale Dokumentation erstellt")

def run_tests(venv_path):
    """Führt grundlegende Tests durch"""
    print("🔄 Führe Basis-Tests durch...")

    # Test: Python import
    python_path = get_venv_python(venv_path)

    test_script = """
import sys
sys.path.insert(0, '.')

try:
    import sqlite3
    print("✅ SQLite verfügbar")
except ImportError:
    print("❌ SQLite nicht verfügbar")
    sys.exit(1)

try:
    # Test Datenbankverbindung
    conn = sqlite3.connect('databases/admin.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM admin_users")
    count = c.fetchone()[0]
    conn.close()
    print(f"✅ Admin-Datenbank: {count} Benutzer")
except Exception as e:
    print(f"❌ Datenbankfehler: {e}")
    sys.exit(1)

try:
    # Test Werkzeug import
    from werkzeug.security import generate_password_hash, check_password_hash
    test_hash = generate_password_hash("test")
    if check_password_hash(test_hash, "test"):
        print("✅ Werkzeug Passwort-Hashing funktioniert")
    else:
        print("❌ Werkzeug Passwort-Hashing fehlerhaft")
        sys.exit(1)
except ImportError:
    print("❌ Werkzeug nicht verfügbar")
    sys.exit(1)

print("✅ Alle Tests bestanden")
"""

    try:
        result = subprocess.run([str(python_path), "-c", test_script],
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests fehlgeschlagen: {e.stderr}")
        return False

def print_success_message(admin_password, port=5000):
    """Zeigt Erfolgsmeldung an"""
    print("\n" + "="*60)
    print(f"🎉 {PROJECT_NAME} erfolgreich installiert!")
    print("="*60)
    print()
    print("📋 WICHTIGE INFORMATIONEN:")
    print()
    print(f"🌐 Dashboard-URL: http://localhost:{port}")
    print(f"🛡️ Admin-Panel:   http://localhost:{port}/admin/login")
    print()
    print("👤 ZUGANGSDATEN:")
    print(f"   Admin:     admin / {admin_password}")
    print("   Demo-User: demo / demo123")
    print()
    print("🚀 DASHBOARD STARTEN:")

    if platform.system() == "Windows":
        print("   start_dashboard.bat")
    else:
        print("   ./start_dashboard.sh")

    print("   ODER: python app.py")
    print()
    print("📁 WICHTIGE DATEIEN:")
    print("   admin_credentials.txt - Admin-Passwort")
    print("   .env                 - Konfiguration")
    print("   README_LOCAL.md      - Lokale Dokumentation")
    print()
    print("⚠️ SICHERHEIT:")
    print("   - Ändern Sie das Admin-Passwort nach dem ersten Login")
    print("   - Bewahren Sie admin_credentials.txt sicher auf")
    print("   - Erstellen Sie regelmäßig Backups der databases/ Ordner")
    print()
    print("🎯 NÄCHSTE SCHRITTE:")
    print("   1. Dashboard starten")
    print("   2. Als Admin anmelden")
    print("   3. Neue Benutzer erstellen")
    print("   4. Dashboard personalisieren")
    print()
    print("="*60)

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description=f"Setup für {PROJECT_NAME}")
    parser.add_argument("--dev", action="store_true",
                       help="Entwicklungsmodus aktivieren")
    parser.add_argument("--port", type=int, default=5000,
                       help="Port für Dashboard (Standard: 5000)")
    parser.add_argument("--no-virtual-env", action="store_true",
                       help="Kein Virtual Environment erstellen")
    parser.add_argument("--force", action="store_true",
                       help="Existierende Installation überschreiben")

    args = parser.parse_args()

    print("="*60)
    print(f"    {PROJECT_NAME} Setup")
    print(f"    Version: {VERSION}")
    print("="*60)
    print()

    # Systemvoraussetzungen prüfen
    print("🔍 Prüfe Systemvoraussetzungen...")

    if not check_python_version():
        sys.exit(1)

    if not check_pip():
        sys.exit(1)

    check_git()  # Optional
    print()

    # Virtual Environment
    venv_path = Path(VENV_NAME)

    if not args.no_virtual_env:
        if not create_virtual_environment(venv_path):
            sys.exit(1)

        if not install_dependencies(venv_path, args.dev):
            sys.exit(1)
    else:
        print("⚠️ Überspringe Virtual Environment (--no-virtual-env)")
        venv_path = None

    print()

    # Projektstruktur
    create_requirements_file(args.dev)
    create_directory_structure()
    print()

    # Datenbank-Setup
    initialize_database()
    admin_password = create_admin_user()
    create_example_user(venv_path)
    print()

    # Konfiguration
    create_config_files(args.port, args.dev)
    create_documentation()
    print()

    # Tests
    if venv_path:
        if not run_tests(venv_path):
            print("⚠️ Einige Tests fehlgeschlagen, aber Installation kann fortgesetzt werden")

    # Erfolgsmeldung
    print_success_message(admin_password, args.port)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup abgebrochen durch Benutzer.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unerwarteter Fehler: {e}")
        print("Bitte wenden Sie sich an den Support.")
        sys.exit(1)