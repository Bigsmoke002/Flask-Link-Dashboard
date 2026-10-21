#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INSTALLATION SCRIPT FÜR USER-MANAGEMENT-SYSTEM
==============================================

Einfaches Setup-Script das die notwendigen Dateien erstellt und 
das User-Management-System vorbereitet.
"""

import os
import sys
import shutil
from datetime import datetime

PROJECT_NAME = "Enhanced User Management Dashboard"
VERSION = "2.0.0"

def print_banner():
    """Zeigt Installation-Banner"""
    print("=" * 80)
    print(f"🚀 {PROJECT_NAME} v{VERSION}")
    print("=" * 80)
    print("📋 INSTALLATION VON:")
    print("   ✅ Erweiterte User-Verwaltung")
    print("   ✅ Gruppen-Management") 
    print("   ✅ Berechtigungen-System")
    print("   ✅ Ordner/Link-Zuweisung")
    print("   ✅ Security-Middleware")
    print("   ✅ Audit-Logging")
    print("=" * 80)
    print()

def create_directory_structure():
    """Erstellt die notwendige Verzeichnisstruktur"""
    print("📁 Erstelle Verzeichnisstruktur...")
    
    directories = [
        'databases',
        'templates/admin',
        'templates/user', 
        'static/css',
        'static/js',
        'logs',
        'uploads',
        'exports'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"   ✅ {directory}/")
        except Exception as e:
            print(f"   ❌ Fehler bei {directory}: {e}")
    
    return True

def backup_existing_files():
    """Erstellt Backup der existierenden Dateien"""
    print("💾 Erstelle Backup der existierenden Dateien...")
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    files_to_backup = ['app.py', 'config.py', 'requirements.txt']
    backup_created = False
    
    for file in files_to_backup:
        if os.path.exists(file):
            if not backup_created:
                os.makedirs(backup_dir, exist_ok=True)
                backup_created = True
            shutil.copy2(file, backup_dir)
            print(f"   ✅ {file} gesichert")
    
    if os.path.exists('databases'):
        if not backup_created:
            os.makedirs(backup_dir, exist_ok=True)
            backup_created = True
        shutil.copytree('databases', os.path.join(backup_dir, 'databases'), dirs_exist_ok=True)
        print(f"   ✅ Datenbanken gesichert")
    
    if backup_created:
        print(f"   ✅ Backup erstellt: {backup_dir}")
        return backup_dir
    else:
        print("   ℹ️  Keine existierenden Dateien zum Sichern gefunden")
        return None

def create_requirements_txt():
    """Erstellt/aktualisiert requirements.txt"""
    print("📦 Erstelle requirements.txt...")
    
    requirements = [
        'Flask>=2.0.0',
        'argon2-cffi>=21.0.0',
        'python-dateutil>=2.8.0'
    ]
    
    try:
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
        print("   ✅ requirements.txt erstellt")
        return True
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen der requirements.txt: {e}")
        return False

def create_error_template():
    """Erstellt ein einfaches Error-Template"""
    print("📄 Erstelle Error-Template...")
    
    error_template = '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fehler {{ error_code }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }
        .error-container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
        }
        h1 { color: #e74c3c; }
        .back-btn {
            background: #3498db;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Fehler {{ error_code or 500 }}</h1>
        <h2>{{ error_title or 'Ein Fehler ist aufgetreten' }}</h2>
        <p>{{ error_message or message or 'Unbekannter Fehler' }}</p>
        <a href="/" class="back-btn">Zurück zur Startseite</a>
    </div>
</body>
</html>'''
    
    try:
        os.makedirs('templates', exist_ok=True)
        with open('templates/error.html', 'w', encoding='utf-8') as f:
            f.write(error_template)
        print("   ✅ templates/error.html erstellt")
        return True
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen des Error-Templates: {e}")
        return False

def create_login_templates():
    """Erstellt einfache Login-Templates"""
    print("📄 Erstelle Login-Templates...")
    
    # User Login Template
    user_login = '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 50px 0;
            min-height: 100vh;
        }
        .login-container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-width: 400px;
            margin: 0 auto;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { opacity: 0.9; }
        .admin-link {
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .admin-link a {
            color: #667eea;
            text-decoration: none;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .flash-message {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .flash-message.error {
            background-color: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        .flash-message.success {
            background-color: #efe;
            color: #363;
            border: 1px solid #cfc;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 User Login</h1>
        
        {% if get_flashed_messages() %}
            <div class="flash-messages">
                {% for category, message in get_flashed_messages(with_categories=true) %}
                    <div class="flash-message {{ category }}">{{ message }}</div>
                {% endfor %}
            </div>
        {% endif %}
        
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            
            <div class="form-group">
                <label for="username">Benutzername:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Passwort:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">Anmelden</button>
        </form>
        
        <div class="admin-link">
            <a href="/admin/login">👑 Admin-Bereich</a>
        </div>
    </div>
</body>
</html>'''
    
    # Admin Login Template
    admin_login = '''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #c94b4b 0%, #4b134f 100%);
            margin: 0;
            padding: 50px 0;
            min-height: 100vh;
        }
        .login-container {
            background: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 400px;
            margin: 0 auto;
            border-top: 5px solid #c94b4b;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .admin-badge {
            background: linear-gradient(135deg, #c94b4b, #4b134f);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 20px;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #c94b4b;
        }
        button {
            width: 100%;
            background: linear-gradient(135deg, #c94b4b, #4b134f);
            color: white;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover { opacity: 0.9; }
        .user-link {
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .user-link a {
            color: #c94b4b;
            text-decoration: none;
        }
        .flash-messages {
            margin-bottom: 20px;
        }
        .flash-message {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .flash-message.error {
            background-color: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
        .flash-message.success {
            background-color: #efe;
            color: #363;
            border: 1px solid #cfc;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div style="text-align: center;">
            <span class="admin-badge">🛡️ ADMIN</span>
        </div>
        <h1>Admin Login</h1>
        
        {% if get_flashed_messages() %}
            <div class="flash-messages">
                {% for category, message in get_flashed_messages(with_categories=true) %}
                    <div class="flash-message {{ category }}">{{ message }}</div>
                {% endfor %}
            </div>
        {% endif %}
        
        <form method="POST">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            
            <div class="form-group">
                <label for="username">Admin-Benutzername:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Admin-Passwort:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit">🔓 Admin-Anmeldung</button>
        </form>
        
        <div class="user-link">
            <a href="/login">👤 Normaler Login</a>
        </div>
    </div>
</body>
</html>'''
    
    try:
        # User Login Template
        os.makedirs('templates/user', exist_ok=True)
        with open('templates/user/login.html', 'w', encoding='utf-8') as f:
            f.write(user_login)
        print("   ✅ templates/user/login.html erstellt")
        
        # Admin Login Template
        os.makedirs('templates/admin', exist_ok=True)
        with open('templates/admin/login.html', 'w', encoding='utf-8') as f:
            f.write(admin_login)
        print("   ✅ templates/admin/login.html erstellt")
        
        return True
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen der Login-Templates: {e}")
        return False

def create_installation_guide():
    """Erstellt Installations-Anleitung"""
    print("📖 Erstelle Installations-Anleitung...")
    
    guide = '''# 🚀 User-Management Installation Guide

## Quick Start

1. **Datenbank initialisieren:**
   ```bash
   python database_updates.py
   ```

2. **App.py ersetzen:**
   - Lade die neue app.py aus dem Artifact `complete_app_py`
   - Ersetze deine bestehende app.py damit

3. **Server starten:**
   ```bash
   python app.py
   ```

4. **Admin-Dashboard öffnen:**
   - URL: http://localhost:5000/admin/login
   - Credentials: siehe admin_credentials.txt

## Was ist installiert?

✅ **User-Management:**
- User erstellen/bearbeiten/löschen
- Passwörter zurücksetzen
- Berechtigungen vergeben

✅ **Gruppen-System:**
- Gruppen erstellen und verwalten
- User zu Gruppen zuweisen
- Ordner/Links auf Gruppen-Ebene

✅ **Sicherheit:**
- Argon2-Passwort-Verschlüsselung
- Rate-Limiting
- CSRF-Schutz
- Audit-Logging

✅ **API-Endpoints:**
- `/api/admin/users` - User-Management
- `/api/admin/groups` - Gruppen-Management
- `/api/user/permissions` - Berechtigungen

## Nächste Schritte

1. Logge dich als Admin ein
2. Erstelle deine ersten User
3. Erstelle Gruppen und weise User zu
4. Konfiguriere Berechtigungen

## Support

- Logs: `logs/dashboard.log`
- Backup: `backup_*/`
- Credentials: `admin_credentials.txt`

Viel Erfolg! 🎉
'''
    
    try:
        with open('INSTALLATION_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(guide)
        print("   ✅ INSTALLATION_GUIDE.md erstellt")
        return True
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen der Anleitung: {e}")
        return False

def print_next_steps():
    """Zeigt nächste Schritte"""
    print("\n" + "=" * 80)
    print("🎉 INSTALLATION VORBEREITET!")
    print("=" * 80)
    print()
    print("📋 NÄCHSTE SCHRITTE:")
    print("   1. python database_updates.py")
    print("   2. Ersetze app.py mit der neuen Version (siehe Artifact)")
    print("   3. python app.py")
    print("   4. Öffne http://localhost:5000/admin/login")
    print()
    print("📁 ERSTELLTE DATEIEN:")
    print("   ✅ Verzeichnisstruktur (databases/, templates/, logs/)")
    print("   ✅ requirements.txt")
    print("   ✅ Login-Templates (user + admin)")
    print("   ✅ Error-Template")
    print("   ✅ INSTALLATION_GUIDE.md")
    print()
    print("🔧 NOCH BENÖTIGT:")
    print("   - database_updates.py ausführen")
    print("   - Neue app.py einsetzen (aus Artifact)")
    print()
    print("=" * 80)

def main():
    """Hauptfunktion"""
    try:
        print_banner()
        
        # 1. Backup erstellen
        backup_dir = backup_existing_files()
        
        # 2. Verzeichnisse erstellen
        create_directory_structure()
        
        # 3. Requirements erstellen
        create_requirements_txt()
        
        # 4. Templates erstellen
        create_error_template()
        create_login_templates()
        
        # 5. Anleitung erstellen
        create_installation_guide()
        
        # 6. Nächste Schritte zeigen
        print_next_steps()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        return 1

if __name__ == "__main__":
    exit(main())