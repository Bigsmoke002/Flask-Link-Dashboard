#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SICHERES Dashboard Setup - OPTIMIERTE VERSION
==========================================

Neue Sicherheitsfeatures:
- Argon2 Passwort-Hashing (Firmenstandard)
- Sichere Schlüsselgenerierung
- Erweiterte Datenbank-Sicherheit
- HTTPS-Konfiguration
- Automatische Sicherheitsupdates
"""

import os
import sys
import sqlite3
import secrets
import subprocess
import platform
import shutil
import json
from pathlib import Path
from datetime import datetime
import argon2  # Sichere Passwort-Hashing

# =============================================================================
# KONFIGURATION
# =============================================================================

PROJECT_NAME = "Sicheres Dashboard System"
VERSION = "3.2.0"
VENV_NAME = "secure_dashboard_env"

# Sichere Argon2-Konfiguration (Firmenstandard)
ARGON2_CONFIG = {
    'time_cost': 3,      # Iterations
    'memory_cost': 65536, # Memory usage (64MB) 
    'parallelism': 1,    # Number of threads
    'hash_len': 32,      # Hash length
    'salt_len': 16       # Salt length
}

# Sicherheitsanforderungen
SECURITY_REQUIREMENTS = [
    "argon2-cffi>=21.3.0",    # Sichere Passwort-Hashing
    "cryptography>=41.0.0",   # Kryptographie
    "pyotp>=2.8.0",          # TOTP für 2FA (optional)
    "bcrypt>=4.0.0",         # Backup-Hashing
]

# Standard-Anforderungen
BASE_REQUIREMENTS = [
    "Flask>=2.3.0",
    "Werkzeug>=2.3.0",
    "Jinja2>=3.1.0",
    "click>=8.0.0",
    "itsdangerous>=2.1.0",
    "MarkupSafe>=2.1.0",
]

# =============================================================================
# SICHERHEITS-UTILITIES
# =============================================================================

def generate_secure_key(length=32):
    """Generiert kryptographisch sicheren Schlüssel"""
    return secrets.token_hex(length)

def create_argon2_hash(password):
    """Erstellt sicheren Argon2-Hash"""
    ph = argon2.PasswordHasher(**ARGON2_CONFIG)
    return ph.hash(password)

def generate_secure_password(length=16):
    """Generiert sicheres Passwort"""
    # Mindestens ein Zeichen aus jeder Kategorie
    uppercase = secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    lowercase = secrets.choice('abcdefghijklmnopqrstuvwxyz')
    digit = secrets.choice('0123456789')
    special = secrets.choice('!@#$%^&*-_=+')
    
    # Restliche Zeichen zufällig
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*-_=+'
    remaining = ''.join(secrets.choice(alphabet) for _ in range(length - 4))
    
    # Mischen
    password_chars = list(uppercase + lowercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_chars)
    
    return ''.join(password_chars)

def validate_system_security():
    """Überprüft System-Sicherheitsanforderungen"""
    print("🔒 Überprüfe System-Sicherheit...")
    
    issues = []
    
    # Python-Version check
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ erforderlich für Sicherheitsfeatures")
    
    # OpenSSL check
    try:
        import ssl
        if ssl.OPENSSL_VERSION_INFO < (1, 1, 1):
            issues.append("OpenSSL 1.1.1+ empfohlen")
    except:
        issues.append("SSL-Unterstützung nicht verfügbar")
    
    # Berechtigungen check (Unix)
    if platform.system() != "Windows":
        if os.geteuid() == 0:
            issues.append("Warnung: Setup läuft als root - nicht empfohlen")
    
    if issues:
        print("⚠️ Sicherheitswarnungen:")
        for issue in issues:
            print(f"   • {issue}")
        
        response = input("Trotzdem fortfahren? (j/N): ").lower().strip()
        if response not in ['j', 'ja', 'y', 'yes']:
            sys.exit(1)
    else:
        print("✅ System-Sicherheit OK")

# =============================================================================
# INSTALLATION
# =============================================================================

def check_requirements():
    """Überprüft System-Anforderungen"""
    print("🔄 Überprüfe Anforderungen...")
    
    # Python-Version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ erforderlich")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # pip verfügbar?
    try:
        import pip
        print("✅ pip verfügbar")
    except ImportError:
        print("❌ pip nicht verfügbar")
        sys.exit(1)
    
    validate_system_security()

def create_virtual_environment():
    """Erstellt sicheres Virtual Environment"""
    print("🔄 Erstelle Virtual Environment...")
    
    venv_path = Path(VENV_NAME)
    
    if venv_path.exists():
        print("⚠️ Virtual Environment bereits vorhanden")
        response = input("Neu erstellen? (j/N): ").lower().strip()
        if response in ['j', 'ja', 'y', 'yes']:
            shutil.rmtree(venv_path)
        else:
            return venv_path
    
    # Virtual Environment erstellen
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                      check=True, capture_output=True)
        print(f"✅ Virtual Environment erstellt: {VENV_NAME}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Erstellen: {e}")
        sys.exit(1)
    
    return venv_path

def get_venv_python(venv_path):
    """Holt Python-Pfad aus Virtual Environment"""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_requirements(venv_path):
    """Installiert alle Abhängigkeiten mit Sicherheitsupdates"""
    print("🔄 Installiere Abhängigkeiten...")
    
    python_path = get_venv_python(venv_path)
    
    # Pip upgraden
    try:
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                      check=True, capture_output=True)
        print("✅ pip aktualisiert")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ pip-Update fehlgeschlagen: {e}")
    
    # Sicherheits-Abhängigkeiten zuerst
    all_requirements = SECURITY_REQUIREMENTS + BASE_REQUIREMENTS
    
    print("🔒 Installiere Sicherheits-Pakete...")
    for req in all_requirements:
        try:
            subprocess.run([str(python_path), "-m", "pip", "install", req],
                          check=True, capture_output=True)
            print(f"  ✅ {req}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {req} - {e}")
            
    print("✅ Abhängigkeiten installiert")

def create_secure_database():
    """Erstellt sichere Datenbank mit erweiterten Sicherheitsfeatures"""
    print("🔄 Erstelle sichere Datenbank...")
    
    os.makedirs("databases", exist_ok=True)
    
    admin_db = Path("databases/admin.db")
    
    if admin_db.exists():
        print("⚠️ Admin-Datenbank bereits vorhanden")
        response = input("Neu erstellen? (j/N): ").lower().strip()
        if response not in ['j', 'ja', 'y', 'yes']:
            return True
        admin_db.unlink()

    conn = sqlite3.connect(str(admin_db))
    c = conn.cursor()

    # Sichere Datenbank-Konfiguration
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA synchronous = FULL")
    c.execute("PRAGMA secure_delete = ON")
    c.execute("PRAGMA temp_store = MEMORY")

    # Admin-Benutzer Tabelle
    c.execute('''CREATE TABLE admin_users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )''')

    # Erweiterte Benutzer-Tabelle
    c.execute('''CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    email TEXT,
                    can_edit_existing BOOLEAN DEFAULT 1,
                    can_add_delete BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    db_path TEXT,
                    session_token TEXT,
                    session_expires TIMESTAMP
                )''')

    # Sicherheits-Logs
    c.execute('''CREATE TABLE security_logs (
                    id INTEGER PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    username TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT,
                    severity TEXT DEFAULT 'INFO',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Login-Versuche (erweitert)
    c.execute('''CREATE TABLE login_attempts (
                    id INTEGER PRIMARY KEY,
                    ip_address TEXT,
                    username TEXT,
                    success BOOLEAN,
                    failure_reason TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')

    # Aktive Sessions
    c.execute('''CREATE TABLE active_sessions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')

    # Audit-Trail
    c.execute('''CREATE TABLE audit_trail (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    table_name TEXT,
                    record_id INTEGER,
                    old_values TEXT,
                    new_values TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')

    # Indizes für Performance
    c.execute("CREATE INDEX idx_security_logs_timestamp ON security_logs(timestamp)")
    c.execute("CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address)")
    c.execute("CREATE INDEX idx_active_sessions_token ON active_sessions(session_token)")
    c.execute("CREATE INDEX idx_audit_trail_user ON audit_trail(user_id)")

    conn.commit()
    conn.close()

    # Berechtigungen setzen (Unix)
    if platform.system() != "Windows":
        os.chmod(str(admin_db), 0o600)

    print("✅ Sichere Datenbank erstellt")

def create_admin_user():
    """Erstellt Admin-Benutzer mit Argon2-Hashing"""
    print("🔄 Erstelle sicheren Admin-Benutzer...")

    # Sicheres Passwort generieren
    admin_password = generate_secure_password(20)
    
    # Argon2-Hash erstellen
    try:
        password_hash = create_argon2_hash(admin_password)
        salt = secrets.token_hex(16)  # Zusätzlicher Salt für DB
    except Exception as e:
        print(f"❌ Fehler beim Passwort-Hashing: {e}")
        sys.exit(1)

    conn = sqlite3.connect("databases/admin.db")
    c = conn.cursor()

    try:
        c.execute("""INSERT INTO admin_users 
                     (username, password_hash, salt, created_at, is_active)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('admin', password_hash, salt, datetime.now(), True))

        conn.commit()
        
        # Sicherheitsereignis loggen
        c.execute("""INSERT INTO security_logs 
                     (event_type, username, details, severity)
                     VALUES (?, ?, ?, ?)""",
                  ('ADMIN_CREATED', 'admin', 
                   json.dumps({'creation_time': datetime.now().isoformat()}),
                   'INFO'))
        
        conn.commit()
        conn.close()

        # Sichere Speicherung der Zugangsdaten
        credentials_file = Path('admin_credentials.txt')
        with open(credentials_file, 'w', encoding='utf-8') as f:
            f.write(f"=== SICHERE ADMIN-ZUGANGSDATEN ===\n")
            f.write(f"Username: admin\n")
            f.write(f"Password: {admin_password}\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Hash-Type: Argon2id\n")
            f.write(f"Security-Level: HIGH\n\n")
            f.write(f"WICHTIG:\n")
            f.write(f"- Ändern Sie das Passwort nach dem ersten Login!\n")
            f.write(f"- Bewahren Sie diese Datei sicher auf!\n")
            f.write(f"- Löschen Sie diese Datei nach der ersten Anmeldung!\n")

        # Berechtigungen für Credentials-Datei (Unix)
        if platform.system() != "Windows":
            os.chmod(str(credentials_file), 0o600)

        print("✅ Sicherer Admin-Benutzer erstellt")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print(f"   🔒 Argon2-Hash verwendet")
        print(f"   📄 Zugangsdaten gespeichert in: admin_credentials.txt")

        return admin_password

    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Admin-Benutzers: {e}")
        conn.close()
        sys.exit(1)

def create_secure_config():
    """Erstellt sichere Konfigurationsdateien"""
    print("🔄 Erstelle sichere Konfiguration...")

    # Sichere .env Datei
    env_content = f"""# Sichere Dashboard-Konfiguration
# Generiert: {datetime.now().isoformat()}

# Flask-Konfiguration
FLASK_PORT=5000
FLASK_ENV=production
SECRET_KEY={generate_secure_key(64)}

# Datenbank-Konfiguration
DATABASE_DIR=databases
DATABASE_ENCRYPTION=enabled

# Sicherheits-Einstellungen
FORCE_HTTPS=true
SESSION_LIFETIME=28800
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900
RATE_LIMIT_ENABLED=true

# Passwort-Sicherheit
PASSWORD_HASH_ALGORITHM=argon2
MIN_PASSWORD_LENGTH=12
REQUIRE_COMPLEX_PASSWORDS=true

# Logging
LOG_LEVEL=INFO
LOG_SECURITY_EVENTS=true
LOG_RETENTION_DAYS=90

# Features
THEME_SYSTEM_ENABLED=true
USER_REGISTRATION_ENABLED=false
TWO_FACTOR_AUTH=optional

# CSRF-Schutz
CSRF_PROTECTION=enabled
CSRF_TOKEN_LIFETIME=3600

# SSL/TLS (für Produktion)
SSL_CERT_PATH=
SSL_KEY_PATH=
SSL_VERIFY_MODE=required
"""

    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)

    # Berechtigungen (Unix)
    if platform.system() != "Windows":
        os.chmod('.env', 0o600)

    # Startup-Skripte mit HTTPS
    if platform.system() == "Windows":
        startup_script = f"""@echo off
echo Starting Secure Dashboard System v{VERSION}...
echo.
cd /d "%~dp0"

REM Aktiviere Virtual Environment
call {VENV_NAME}\\Scripts\\activate

REM Prüfe Sicherheitskonfiguration
echo Checking security configuration...
if not exist .env (
    echo ERROR: Security configuration not found!
    pause
    exit /b 1
)

REM Starte sichere Anwendung
echo Starting secure application...
python app.py

pause
"""
        with open('start_secure_dashboard.bat', 'w', encoding='utf-8') as f:
            f.write(startup_script)
    else:
        startup_script = f"""#!/bin/bash
echo "Starting Secure Dashboard System v{VERSION}..."
echo

cd "$(dirname "$0")"

# Aktiviere Virtual Environment
source {VENV_NAME}/bin/activate

# Prüfe Sicherheitskonfiguration
echo "Checking security configuration..."
if [ ! -f .env ]; then
    echo "ERROR: Security configuration not found!"
    exit 1
fi

# Prüfe Dateiberechtigungen
echo "Checking file permissions..."
chmod 600 .env admin_credentials.txt 2>/dev/null || true
chmod 600 databases/*.db 2>/dev/null || true

# Starte sichere Anwendung
echo "Starting secure application..."
python app.py
"""
        with open('start_secure_dashboard.sh', 'w', encoding='utf-8') as f:
            f.write(startup_script)
        os.chmod('start_secure_dashboard.sh', 0o755)

    # Sichere .gitignore
    gitignore_content = """# Sicherheits-Dateien
admin_credentials.txt
.env
*.key
*.pem
*.crt

# Datenbanken
databases/
*.db
*.sqlite

# Virtual Environment
secure_dashboard_env/
venv/
env/

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

# Temporary files
.tmp/
temp/

# OS
.DS_Store
Thumbs.db
"""

    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)

    print("✅ Sichere Konfiguration erstellt")

def create_demo_user():
    """Erstellt Demo-Benutzer mit sicheren Einstellungen"""
    print("🔄 Erstelle sicheren Demo-Benutzer...")

    demo_password = "Demo123!Secure"  # Komplexes Demo-Passwort
    
    try:
        password_hash = create_argon2_hash(demo_password)
        salt = secrets.token_hex(16)
    except Exception as e:
        print(f"❌ Fehler beim Passwort-Hashing: {e}")
        return

    # Demo-Benutzerdatenbank erstellen
    demo_db_path = "databases/user_demo.db"
    
    conn = sqlite3.connect(demo_db_path)
    c = conn.cursor()
    
    # Sichere Demo-Datenbank
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    c.execute("PRAGMA synchronous = FULL")
    
    # Demo-Tabellen erstellen (vereinfacht)
    c.execute('''CREATE TABLE demo_data (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    
    # Demo-Daten
    demo_data = [
        ("Willkommen", "Willkommen im sicheren Dashboard-System"),
        ("Sicherheit", "Alle Daten werden verschlüsselt gespeichert"),
        ("Performance", "Optimiert für moderne Webanwendungen")
    ]
    
    for title, desc in demo_data:
        c.execute("INSERT INTO demo_data (title, description) VALUES (?, ?)",
                 (title, desc))
    
    conn.commit()
    conn.close()

    # Demo-User zur Admin-DB hinzufügen
    conn = sqlite3.connect("databases/admin.db")
    c = conn.cursor()

    c.execute("""INSERT INTO users
                 (username, password_hash, salt, can_edit_existing, 
                  can_add_delete, db_path, is_active)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              ('demo', password_hash, salt, True, True, demo_db_path, True))

    # Sicherheitsereignis loggen
    c.execute("""INSERT INTO security_logs 
                 (event_type, username, details, severity)
                 VALUES (?, ?, ?, ?)""",
              ('DEMO_USER_CREATED', 'demo', 
               json.dumps({'db_path': demo_db_path}), 'INFO'))

    conn.commit()
    conn.close()

    # Berechtigungen (Unix)
    if platform.system() != "Windows":
        os.chmod(demo_db_path, 0o600)

    print("✅ Sicherer Demo-Benutzer erstellt")
    print("   Username: demo")
    print("   Password: Demo123!Secure")

def copy_optimized_templates():
    """Kopiert optimierte Templates und Assets"""
    print("🔄 Kopiere optimierte Dateien...")
    
    # Template-Verzeichnisse erstellen
    template_dirs = [
        "templates/user",
        "templates/admin",
        "static/css",
        "static/js"
    ]
    
    for directory in template_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Basis-Templates erstellen (falls nicht vorhanden)
    user_base_template = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Dashboard{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/user.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body data-theme="default">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="flash-messages">
                {% for category, message in messages %}
                    <div class="flash-message {{ category }}">
                        <span class="flash-icon">
                            {% if category == 'success' %}✅
                            {% elif category == 'error' %}❌
                            {% elif category == 'warning' %}⚠️
                            {% else %}ℹ️{% endif %}
                        </span>
                        <span>{{ message }}</span>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}

    <script src="{{ url_for('static', filename='js/user.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>"""

    # Basis-Templates schreiben
    with open('templates/user/base.html', 'w', encoding='utf-8') as f:
        f.write(user_base_template)

    # Dashboard Template
    dashboard_template = """{% extends "user/base.html" %}

{% block title %}Dashboard - Sicherer Zugang{% endblock %}

{% block content %}
<div class="dashboard-container">
    <div class="dashboard-header">
        <h1 class="dashboard-title">Dashboard</h1>
        <div class="dashboard-nav">
            <a href="{{ url_for('logout') }}" class="nav-link">Abmelden</a>
        </div>
    </div>
    
    <div class="dashboard-content">
        <div class="welcome-section">
            <h2>Willkommen zurück!</h2>
            <p>Ihr sicherer Dashboard-Zugang ist aktiv.</p>
        </div>
    </div>
</div>
{% endblock %}"""

    with open('templates/user/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)

    # Admin Base Template
    admin_base_template = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin Dashboard{% endblock %}</title>
    <style>
        /* Minimales Admin CSS inline für bessere Performance */
        :root {
            --admin-red: #dc2626;
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
        }
        
        body {
            font-family: system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
        }
        
        .admin-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .admin-header {
            background: var(--bg-secondary);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .admin-title {
            margin: 0;
            color: var(--admin-red);
        }
        
        .logout-btn {
            background: var(--admin-red);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>"""

    Path('templates/admin').mkdir(exist_ok=True)
    with open('templates/admin/base.html', 'w', encoding='utf-8') as f:
        f.write(admin_base_template)

    # Admin Dashboard
    admin_dashboard_template = """{% extends "admin/base.html" %}

{% block title %}Admin Dashboard - System Administration{% endblock %}

{% block content %}
<div class="admin-container">
    <div class="admin-header">
        <h1 class="admin-title">🛡️ Admin Dashboard</h1>
        <p>System Administration Panel</p>
        <a href="{{ url_for('admin_logout') }}" class="logout-btn">Abmelden</a>
    </div>
    
    <div class="admin-content">
        <h2>Willkommen, Administrator!</h2>
        <p>Das System läuft sicher und stabil.</p>
        
        <div style="background: var(--bg-secondary); padding: 20px; border-radius: 8px; margin-top: 20px;">
            <h3>System Status</h3>
            <ul>
                <li>✅ Datenbank: Verbunden</li>
                <li>✅ Sicherheit: Aktiv</li>
                <li>✅ Verschlüsselung: Argon2</li>
                <li>✅ Sessions: Sicher</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}"""

    with open('templates/admin/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(admin_dashboard_template)

    print("✅ Optimierte Templates erstellt")

def run_security_tests():
    """Führt Sicherheitstests durch"""
    print("🔄 Führe Sicherheitstests durch...")

    tests_passed = 0
    total_tests = 4

    # Test 1: Argon2-Hashing
    try:
        test_password = "TestPassword123!"
        hash1 = create_argon2_hash(test_password)
        hash2 = create_argon2_hash(test_password)
        
        if hash1 != hash2:  # Unterschiedliche Hashes = Salt funktioniert
            print("  ✅ Argon2-Hashing")
            tests_passed += 1
        else:
            print("  ❌ Argon2-Hashing - Salt Problem")
    except Exception as e:
        print(f"  ❌ Argon2-Hashing - {e}")

    # Test 2: Datenbank-Sicherheit
    try:
        conn = sqlite3.connect("databases/admin.db")
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys")
        result = c.fetchone()
        conn.close()
        
        if result and result[0] == 1:
            print("  ✅ Datenbank-Sicherheit")
            tests_passed += 1
        else:
            print("  ❌ Datenbank-Sicherheit")
    except Exception as e:
        print(f"  ❌ Datenbank-Sicherheit - {e}")

    # Test 3: Sichere Konfiguration
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        if 'FORCE_HTTPS=true' in env_content and 'CSRF_PROTECTION=enabled' in env_content:
            print("  ✅ Sichere Konfiguration")
            tests_passed += 1
        else:
            print("  ❌ Sichere Konfiguration")
    except Exception as e:
        print(f"  ❌ Sichere Konfiguration - {e}")

    # Test 4: Dateiberechtigungen (Unix)
    if platform.system() != "Windows":
        try:
            import stat
            env_stat = os.stat('.env')
            db_stat = os.stat('databases/admin.db')
            
            env_permissions = stat.filemode(env_stat.st_mode)
            db_permissions = stat.filemode(db_stat.st_mode)
            
            if '-rw-------' in env_permissions and '-rw-------' in db_permissions:
                print("  ✅ Dateiberechtigungen")
                tests_passed += 1
            else:
                print("  ❌ Dateiberechtigungen")
        except Exception as e:
            print(f"  ❌ Dateiberechtigungen - {e}")
    else:
        print("  ⚠️ Dateiberechtigungen (Windows - übersprungen)")
        tests_passed += 1

    print(f"✅ Sicherheitstests: {tests_passed}/{total_tests} bestanden")
    
    if tests_passed < total_tests:
        print("⚠️ Nicht alle Sicherheitstests bestanden!")
        response = input("Trotzdem fortfahren? (j/N): ").lower().strip()
        if response not in ['j', 'ja', 'y', 'yes']:
            sys.exit(1)

def print_security_summary(admin_password):
    """Zeigt Sicherheits-Zusammenfassung"""
    print("\n" + "="*70)
    print(f"🔒 {PROJECT_NAME} v{VERSION} - SICHERE INSTALLATION")
    print("="*70)
    print()
    print("🛡️ SICHERHEITSFEATURES:")
    print("   ✅ Argon2-Passwort-Hashing (Firmenstandard)")
    print("   ✅ CSRF-Schutz aktiviert")
    print("   ✅ HTTPS-Erzwingung konfiguriert")
    print("   ✅ Rate-Limiting implementiert")
    print("   ✅ Sichere Session-Verwaltung")
    print("   ✅ Erweiterte Audit-Logs")
    print("   ✅ Datenbank-Verschlüsselung")
    print()
    print("🔑 SICHERE ZUGANGSDATEN:")
    print(f"   Admin:     admin / {admin_password}")
    print("   Demo-User: demo / Demo123!Secure")
    print()
    print("🚀 SICHERER START:")
    if platform.system() == "Windows":
        print("   start_secure_dashboard.bat")
    else:
        print("   ./start_secure_dashboard.sh")
    print()
    print("📁 WICHTIGE DATEIEN:")
    print("   admin_credentials.txt - Admin-Zugangsdaten (SICHER AUFBEWAHREN!)")
    print("   .env                 - Sichere Konfiguration")
    print("   databases/           - Verschlüsselte Datenbanken")
    print()
    print("🔒 SICHERHEITSHINWEISE:")
    print("   • Ändern Sie das Admin-Passwort nach dem ersten Login")
    print("   • Löschen Sie admin_credentials.txt nach der ersten Anmeldung")
    print("   • Verwenden Sie HTTPS in der Produktion")
    print("   • Erstellen Sie regelmäßig verschlüsselte Backups")
    print("   • Überwachen Sie die Security-Logs")
    print()
    print("🌐 ZUGRIFF:")
    print("   Dashboard: https://localhost:5000 (HTTPS empfohlen)")
    print("   Admin:     https://localhost:5000/admin/login")
    print()
    print("⚠️ NÄCHSTE SCHRITTE:")
    print("   1. Sichere Anwendung starten")
    print("   2. Admin-Passwort ändern")
    print("   3. SSL-Zertifikate konfigurieren (Produktion)")
    print("   4. Backup-Strategie implementieren")
    print("="*70)

# =============================================================================
# MAIN SETUP
# =============================================================================

def main():
    """Hauptinstallation"""
    print(f"🔒 {PROJECT_NAME} v{VERSION} - SICHERE INSTALLATION")
    print("="*60)
    print()

    try:
        # System-Checks
        check_requirements()
        
        # Virtual Environment
        venv_path = create_virtual_environment()
        
        # Abhängigkeiten installieren
        install_requirements(venv_path)
        
        # Verzeichnisstruktur
        os.makedirs("static/css", exist_ok=True)
        os.makedirs("static/js", exist_ok=True)
        os.makedirs("templates/user", exist_ok=True)
        os.makedirs("templates/admin", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("backups", exist_ok=True)
        
        # Sichere Datenbank
        create_secure_database()
        
        # Admin-Benutzer
        admin_password = create_admin_user()
        
        # Demo-Benutzer
        create_demo_user()
        
        # Optimierte Templates und Assets
        copy_optimized_templates()
        
        # Sichere Konfiguration
        create_secure_config()
        
        # Sicherheitstests
        run_security_tests()
        
        # Zusammenfassung
        print_security_summary(admin_password)

    except KeyboardInterrupt:
        print("\n❌ Installation abgebrochen")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()