#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DATABASE UPDATES FOR USER MANAGEMENT SYSTEM
==========================================

Führt alle notwendigen Datenbank-Updates für das User-Management durch:
- Erstellt/erweitert Admin-Datenbank
- Aktualisiert User-Datenbank-Schema
- Fügt Demo-Daten hinzu
- Erstellt Indizes für Performance
"""

import sqlite3
import os
import secrets
import argon2
from datetime import datetime

# Konfiguration
DATABASE_DIR = 'databases'
ADMIN_DB = os.path.join(DATABASE_DIR, 'admin.db')

# Argon2 Password Hasher
ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16
)

def print_status(message):
    """Druckt Status-Nachricht"""
    print(f"✅ {message}")

def print_error(message):
    """Druckt Fehler-Nachricht"""
    print(f"❌ {message}")

def print_warning(message):
    """Druckt Warnung"""
    print(f"⚠️  {message}")

def ensure_database_dir():
    """Stellt sicher, dass das Database-Verzeichnis existiert"""
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
        print_status(f"Database-Verzeichnis '{DATABASE_DIR}' erstellt")

def update_admin_database():
    """Aktualisiert/erstellt die Admin-Datenbank mit allen Tabellen"""
    print("🔄 Aktualisiere Admin-Datenbank...")
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Users-Tabelle mit erweiterten Feldern
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            can_edit_links BOOLEAN DEFAULT 1,
            can_delete_links BOOLEAN DEFAULT 0,
            can_add_links BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )''')
        print_status("Users-Tabelle erstellt/aktualisiert")
        
        # Groups-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        print_status("Groups-Tabelle erstellt")
        
        # Group-Members-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(group_id, user_id)
        )''')
        print_status("Group-Members-Tabelle erstellt")
        
        # Group-Tabs-Tabelle für Ordner
        c.execute('''CREATE TABLE IF NOT EXISTS group_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '📂',
            color TEXT DEFAULT '#10b981',
            position INTEGER DEFAULT 0,
            is_folder BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
        )''')
        print_status("Group-Tabs-Tabelle erstellt")
        
        # Group-Folder-Links-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS group_folder_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            folder_tab_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            icon TEXT DEFAULT '🔗',
            color TEXT DEFAULT '#10b981',
            position INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
            FOREIGN KEY (folder_tab_id) REFERENCES group_tabs (id) ON DELETE CASCADE
        )''')
        print_status("Group-Folder-Links-Tabelle erstellt")
        
        # User-Permissions-Tabelle für erweiterte Berechtigungen
        c.execute('''CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            permission_name TEXT NOT NULL,
            permission_value BOOLEAN DEFAULT 0,
            granted_by INTEGER,
            granted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES users (id),
            UNIQUE(user_id, permission_name)
        )''')
        print_status("User-Permissions-Tabelle erstellt")
        
        # Security-Log-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        print_status("Security-Log-Tabelle erstellt")
        
        # System-Settings-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'string',
            description TEXT,
            updated_by INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )''')
        print_status("System-Settings-Tabelle erstellt")
        
        # Indizes für bessere Performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_group_members_user_id ON group_members(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_security_log_timestamp ON security_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_security_log_event_type ON security_log(event_type)"
        ]
        
        for index in indexes:
            c.execute(index)
        
        print_status("Performance-Indizes erstellt")
        
        # Standard-Einstellungen hinzufügen
        default_settings = [
            ('default_can_edit_links', '1', 'boolean', 'Standard-Berechtigung: Links bearbeiten'),
            ('default_can_delete_links', '0', 'boolean', 'Standard-Berechtigung: Links löschen'),
            ('default_can_add_links', '1', 'boolean', 'Standard-Berechtigung: Links hinzufügen'),
            ('max_login_attempts', '5', 'integer', 'Maximale Login-Versuche'),
            ('session_timeout', '3600', 'integer', 'Session-Timeout in Sekunden'),
            ('enable_user_registration', '0', 'boolean', 'User-Registrierung aktiviert')
        ]
        
        for setting_key, setting_value, setting_type, description in default_settings:
            c.execute("""INSERT OR IGNORE INTO system_settings 
                         (setting_key, setting_value, setting_type, description)
                         VALUES (?, ?, ?, ?)""",
                      (setting_key, setting_value, setting_type, description))
        
        print_status("Standard-Einstellungen hinzugefügt")
        
        conn.commit()
        print_status("Admin-Datenbank erfolgreich aktualisiert")
        
    except Exception as e:
        conn.rollback()
        print_error(f"Fehler beim Aktualisieren der Admin-Datenbank: {e}")
        raise
    finally:
        conn.close()

def create_admin_user():
    """Erstellt einen Standard-Admin-User falls nicht vorhanden"""
    print("👤 Prüfe Admin-User...")
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Prüfe ob bereits ein Admin existiert
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = c.fetchone()[0]
        
        if admin_count == 0:
            # Standard-Admin erstellen
            admin_password = secrets.token_urlsafe(12)
            admin_hash = ph.hash(admin_password)
            
            c.execute("""INSERT INTO users (username, email, password_hash, is_admin, is_active, created_at)
                         VALUES (?, ?, ?, 1, 1, ?)""",
                      ('admin', 'admin@localhost', admin_hash, datetime.now()))
            
            conn.commit()
            
            # Admin-Credentials speichern
            with open('admin_credentials.txt', 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("ADMIN-ZUGANGSDATEN\n")
                f.write("=" * 50 + "\n")
                f.write(f"URL: http://localhost:5000/admin/login\n")
                f.write(f"Username: admin\n")
                f.write(f"Passwort: {admin_password}\n")
                f.write(f"Erstellt: {datetime.now()}\n")
                f.write("\n")
                f.write("WICHTIG:\n")
                f.write("- Diese Datei nach dem ersten Login löschen!\n")
                f.write("- Passwort sofort im Admin-Dashboard ändern!\n")
                f.write("- Nie in Git/Repository committen!\n")
                f.write("=" * 50 + "\n")
            
            print_status(f"Standard-Admin erstellt: admin / {admin_password}")
            print_warning("Zugangsdaten in admin_credentials.txt gespeichert")
            print_warning("WICHTIG: Passwort nach erstem Login ändern!")
            
        else:
            print_status(f"{admin_count} Admin-User bereits vorhanden")
        
    except Exception as e:
        conn.rollback()
        print_error(f"Fehler beim Erstellen des Admin-Users: {e}")
        raise
    finally:
        conn.close()

def create_demo_groups():
    """Erstellt Demo-Gruppen mit Ordnern"""
    print("📁 Erstelle Demo-Gruppen...")
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Demo-Gruppen
        demo_groups = [
            ('Entwickler', 'Entwickler-Team mit Zugriff auf Entwicklungsressourcen'),
            ('Marketing', 'Marketing-Team mit Zugriff auf Marketing-Tools'),
            ('Support', 'Support-Team mit Zugriff auf Kunden-Tools'),
            ('Management', 'Management mit erweiterten Berechtigungen')
        ]
        
        group_ids = {}
        for group_name, description in demo_groups:
            # Prüfe ob Gruppe bereits existiert
            c.execute("SELECT id FROM groups WHERE name = ?", (group_name,))
            existing = c.fetchone()
            
            if not existing:
                c.execute("""INSERT INTO groups (name, description, created_at)
                             VALUES (?, ?, ?)""",
                          (group_name, description, datetime.now()))
                group_id = c.lastrowid
                print_status(f"Demo-Gruppe '{group_name}' erstellt")
            else:
                group_id = existing[0]
                print_status(f"Demo-Gruppe '{group_name}' bereits vorhanden")
            
            group_ids[group_name] = group_id
        
        # Demo-Ordner für Entwickler-Gruppe
        if 'Entwickler' in group_ids:
            dev_folders = [
                ('GitHub', '🐙', '#f1502f'),
                ('Dokumentation', '📚', '#10b981'),
                ('Tools', '🔧', '#3b82f6'),
                ('APIs', '🔌', '#8b5cf6')
            ]
            
            for i, (folder_name, icon, color) in enumerate(dev_folders):
                c.execute("""INSERT OR IGNORE INTO group_tabs 
                             (group_id, name, icon, color, position)
                             VALUES (?, ?, ?, ?, ?)""",
                          (group_ids['Entwickler'], folder_name, icon, color, i))
        
        # Demo-Ordner für Marketing-Gruppe
        if 'Marketing' in group_ids:
            marketing_folders = [
                ('Social Media', '📱', '#e11d48'),
                ('Analytics', '📊', '#8b5cf6'),
                ('Content', '✍️', '#f59e0b'),
                ('Design', '🎨', '#06b6d4')
            ]
            
            for i, (folder_name, icon, color) in enumerate(marketing_folders):
                c.execute("""INSERT OR IGNORE INTO group_tabs 
                             (group_id, name, icon, color, position)
                             VALUES (?, ?, ?, ?, ?)""",
                          (group_ids['Marketing'], folder_name, icon, color, i))
        
        conn.commit()
        print_status("Demo-Gruppen und Ordner erstellt")
        
    except Exception as e:
        conn.rollback()
        print_error(f"Fehler beim Erstellen der Demo-Gruppen: {e}")
        raise
    finally:
        conn.close()

def create_demo_user():
    """Erstellt einen Demo-User"""
    print("👤 Erstelle Demo-User...")
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Prüfe ob Demo-User bereits existiert
        c.execute("SELECT id FROM users WHERE username = 'demo'")
        if c.fetchone():
            print_status("Demo-User bereits vorhanden")
            return
        
        # Demo-User erstellen
        demo_password = "Demo123!"
        demo_hash = ph.hash(demo_password)
        
        c.execute("""INSERT INTO users 
                     (username, email, password_hash, is_admin, is_active, 
                      can_edit_links, can_delete_links, can_add_links, created_at)
                     VALUES (?, ?, ?, 0, 1, 1, 0, 1, ?)""",
                  ('demo', 'demo@localhost', demo_hash, datetime.now()))
        
        demo_user_id = c.lastrowid
        
        # Demo-User zur Entwickler-Gruppe hinzufügen
        c.execute("SELECT id FROM groups WHERE name = 'Entwickler'")
        dev_group = c.fetchone()
        if dev_group:
            c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
                     (dev_group[0], demo_user_id))
        
        conn.commit()
        
        print_status(f"Demo-User erstellt: demo / {demo_password}")
        
        # Demo-Credentials zu admin_credentials.txt hinzufügen
        with open('admin_credentials.txt', 'a', encoding='utf-8') as f:
            f.write("\n")
            f.write("DEMO-USER:\n")
            f.write(f"Username: demo\n")
            f.write(f"Passwort: {demo_password}\n")
            f.write(f"URL: http://localhost:5000/login\n")
        
    except Exception as e:
        conn.rollback()
        print_error(f"Fehler beim Erstellen des Demo-Users: {e}")
        raise
    finally:
        conn.close()

def verify_installation():
    """Überprüft die Installation"""
    print("🔍 Überprüfe Installation...")
    
    try:
        conn = sqlite3.connect(ADMIN_DB)
        c = conn.cursor()
        
        # Prüfe wichtige Tabellen
        tables_to_check = [
            'users', 'groups', 'group_members', 'group_tabs', 
            'group_folder_links', 'security_log', 'system_settings'
        ]
        
        for table in tables_to_check:
            c.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            if c.fetchone()[0] == 1:
                print_status(f"Tabelle '{table}' vorhanden")
            else:
                print_error(f"Tabelle '{table}' fehlt!")
        
        # Prüfe Admin-User
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = c.fetchone()[0]
        print_status(f"{admin_count} Admin-User vorhanden")
        
        # Prüfe normale User
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
        user_count = c.fetchone()[0]
        print_status(f"{user_count} normale User vorhanden")
        
        # Prüfe Gruppen
        c.execute("SELECT COUNT(*) FROM groups")
        group_count = c.fetchone()[0]
        print_status(f"{group_count} Gruppen vorhanden")
        
        conn.close()
        
        return True
        
    except Exception as e:
        print_error(f"Fehler bei der Installations-Überprüfung: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("=" * 70)
    print("🚀 DATENBANK-UPDATES FÜR USER-MANAGEMENT-SYSTEM")
    print("=" * 70)
    print()
    
    try:
        # 1. Database-Verzeichnis sicherstellen
        ensure_database_dir()
        
        # 2. Admin-Datenbank aktualisieren
        update_admin_database()
        
        # 3. Admin-User erstellen
        create_admin_user()
        
        # 4. Demo-Gruppen erstellen
        create_demo_groups()
        
        # 5. Demo-User erstellen
        create_demo_user()
        
        # 6. Installation überprüfen
        if verify_installation():
            print("\n" + "=" * 70)
            print("🎉 DATENBANK-UPDATES ERFOLGREICH ABGESCHLOSSEN!")
            print("=" * 70)
            print()
            print("📋 NÄCHSTE SCHRITTE:")
            print("   1. Ersetze deine app.py mit der neuen Version")
            print("   2. Starte den Server: python app.py")
            print("   3. Öffne Admin-Dashboard: http://localhost:5000/admin/login")
            print("   4. Logge dich mit den Credentials aus admin_credentials.txt ein")
            print()
            print("🔑 ZUGANGSDATEN:")
            print("   - Admin-Credentials: siehe admin_credentials.txt")
            print("   - Demo-User: demo / Demo123!")
            print()
            print("✨ VERFÜGBARE FEATURES:")
            print("   ✅ User-Management (Erstellen/Bearbeiten/Löschen)")
            print("   ✅ Passwort-Reset-Funktionalität")
            print("   ✅ Gruppen-Verwaltung mit Ordner-Zuweisung")
            print("   ✅ Granulare Berechtigungen")
            print("   ✅ Audit-Logging für alle Admin-Aktionen")
            print("   ✅ Security-Features (Rate-Limiting, CSRF)")
            print()
            
        else:
            print_error("Installation nicht vollständig - bitte Fehler beheben")
            return 1
        
    except Exception as e:
        print_error(f"Unerwarteter Fehler: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())