#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup Script für Dashboard System
Entfernt alle Beispieldaten und repariert User-Erstellung
"""

import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_database():
    """Erstellt Backup der Datenbanken vor Bereinigung"""
    backup_dir = Path(f"backup_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    
    print("🔄 Erstelle Backup der Datenbanken...")
    
    db_dir = Path("databases")
    if db_dir.exists():
        shutil.copytree(db_dir, backup_dir / "databases")
        print(f"✅ Backup erstellt: {backup_dir}")
        return backup_dir
    else:
        print("⚠️  Kein databases/ Verzeichnis gefunden")
        return None

def clean_example_data():
    """Entfernt alle Beispieldaten aus den Datenbanken"""
    print("🧹 Entferne Beispieldaten...")
    
    # Admin-Datenbank bereinigen
    admin_db = Path("databases/admin.db")
    if admin_db.exists():
        conn = sqlite3.connect(str(admin_db))
        c = conn.cursor()
        
        # Demo-User entfernen
        c.execute("DELETE FROM users WHERE username = 'demo'")
        print("   ✅ Demo-User entfernt")
        
        # Beispiel-Gruppen entfernen (falls vorhanden)
        c.execute("DELETE FROM groups WHERE name LIKE 'Demo%' OR name LIKE 'Beispiel%'")
        c.execute("DELETE FROM groups WHERE name LIKE 'Test%' OR name LIKE 'Sample%'")
        print("   ✅ Beispiel-Gruppen entfernt")
        
        # Beispiel-Links entfernen
        c.execute("DELETE FROM links WHERE name LIKE 'Demo%' OR name LIKE 'Beispiel%'")
        c.execute("DELETE FROM links WHERE name LIKE 'Test%' OR url LIKE '%example.com%'")
        print("   ✅ Beispiel-Links entfernt")
        
        # Security-Logs von Demo-User bereinigen
        c.execute("DELETE FROM security_logs WHERE username = 'demo'")
        print("   ✅ Demo-User Security-Logs entfernt")
        
        conn.commit()
        conn.close()
        print("✅ Admin-Datenbank bereinigt")
    
    # Demo-User Datenbank komplett entfernen
    demo_db = Path("databases/user_demo.db")
    if demo_db.exists():
        os.remove(demo_db)
        print("✅ Demo-User Datenbank entfernt")
    
    # Andere Beispiel-Datenbanken entfernen
    db_dir = Path("databases")
    if db_dir.exists():
        for db_file in db_dir.glob("*demo*.db"):
            os.remove(db_file)
            print(f"✅ {db_file.name} entfernt")
        
        for db_file in db_dir.glob("*test*.db"):
            os.remove(db_file)
            print(f"✅ {db_file.name} entfernt")

def fix_user_creation_schema():
    """Repariert Datenbankschema für User-Erstellung"""
    print("🔧 Repariere Datenbankschema...")
    
    admin_db = Path("databases/admin.db")
    if not admin_db.exists():
        print("❌ Admin-Datenbank nicht gefunden")
        return False
    
    conn = sqlite3.connect(str(admin_db))
    c = conn.cursor()
    
    try:
        # Prüfe und erstelle fehlende Spalten in users Tabelle
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        
        missing_columns = []
        required_columns = {
            'email': 'TEXT',
            'can_edit_links': 'BOOLEAN DEFAULT 1',
            'can_delete_links': 'BOOLEAN DEFAULT 0', 
            'can_add_links': 'BOOLEAN DEFAULT 1',
            'is_active': 'BOOLEAN DEFAULT 1',
            'is_admin': 'BOOLEAN DEFAULT 0',
            'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'last_login': 'TIMESTAMP',
            'login_attempts': 'INTEGER DEFAULT 0',
            'locked_until': 'TIMESTAMP',
            'salt': 'TEXT'
        }
        
        for column, definition in required_columns.items():
            if column not in columns:
                missing_columns.append((column, definition))
        
        # Fehlende Spalten hinzufügen
        for column, definition in missing_columns:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
                print(f"   ✅ Spalte '{column}' hinzugefügt")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    print(f"   ⚠️  Warnung bei Spalte '{column}': {e}")
        
        # Erstelle groups Tabelle falls nicht vorhanden
        c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Erstelle group_members Tabelle falls nicht vorhanden
        c.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                UNIQUE(user_id, group_id)
            )
        """)
        
        # Erstelle security_logs Tabelle falls nicht vorhanden
        c.execute("""
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                username TEXT,
                ip_address TEXT,
                details TEXT,
                success BOOLEAN DEFAULT 1
            )
        """)
        
        # Erstelle links Tabelle falls nicht vorhanden
        c.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                icon TEXT,
                group_id INTEGER,
                folder_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        conn.commit()
        print("✅ Datenbankschema repariert")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Reparieren des Schemas: {e}")
        return False
    finally:
        conn.close()

def verify_api_functionality():
    """Überprüft ob alle notwendigen API-Routen funktionieren"""
    print("🔍 Überprüfe API-Funktionalität...")
    
    admin_db = Path("databases/admin.db")
    if not admin_db.exists():
        print("❌ Admin-Datenbank nicht gefunden")
        return False
    
    conn = sqlite3.connect(str(admin_db))
    c = conn.cursor()
    
    try:
        # Test: User-Liste abrufen
        c.execute("""
            SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.last_login,
                   u.can_edit_links, u.can_delete_links, u.can_add_links,
                   COUNT(DISTINCT gm.group_id) as group_count
            FROM users u
            LEFT JOIN group_members gm ON u.id = gm.user_id
            WHERE u.is_admin = 0
            GROUP BY u.id
            LIMIT 1
        """)
        
        # Test: Gruppen-Liste abrufen
        c.execute("""
            SELECT g.id, g.name, g.description, g.created_at,
                   COUNT(DISTINCT gm.user_id) as member_count,
                   COUNT(DISTINCT l.id) as link_count
            FROM groups g
            LEFT JOIN group_members gm ON g.id = gm.group_id
            LEFT JOIN links l ON g.id = l.group_id
            GROUP BY g.id
            LIMIT 1
        """)
        
        print("✅ API-Queries funktionieren")
        return True
        
    except Exception as e:
        print(f"❌ API-Test fehlgeschlagen: {e}")
        return False
    finally:
        conn.close()

def create_clean_admin_credentials():
    """Erstellt frische Admin-Zugangsdaten"""
    print("🔑 Erstelle frische Admin-Zugangsdaten...")
    
    import secrets
    import string
    
    # Neues sicheres Admin-Passwort generieren
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    admin_password = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    # Passwort-Hash erstellen (falls Argon2 verfügbar)
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        password_hash = ph.hash(admin_password)
        print("   ✅ Argon2-Hash erstellt")
    except ImportError:
        import hashlib
        import secrets
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', admin_password.encode(), salt.encode(), 100000).hex()
        print("   ✅ PBKDF2-Hash erstellt")
    
    # Admin in Datenbank aktualisieren
    admin_db = Path("databases/admin.db")
    if admin_db.exists():
        conn = sqlite3.connect(str(admin_db))
        c = conn.cursor()
        
        # Bestehenden Admin aktualisieren oder erstellen
        c.execute("""
            INSERT OR REPLACE INTO admin_users (id, username, password_hash, created_at, is_active)
            VALUES (1, 'admin', ?, ?, 1)
        """, (password_hash, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # Zugangsdaten speichern
        with open('admin_credentials_clean.txt', 'w', encoding='utf-8') as f:
            f.write(f"=== BEREINIGTE ADMIN-ZUGANGSDATEN ===\n")
            f.write(f"Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Username: admin\n")
            f.write(f"Password: {admin_password}\n\n")
            f.write(f"URL: http://localhost:5000/admin/login\n\n")
            f.write(f"WICHTIG: Passwort nach erstem Login ändern!\n")
        
        print(f"✅ Neue Admin-Zugangsdaten erstellt")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print(f"   (Gespeichert in: admin_credentials_clean.txt)")
        
        return admin_password
    
    return None

def cleanup_log_files():
    """Bereinigt alte Log-Dateien"""
    print("📄 Bereinige Log-Dateien...")
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            try:
                # Erstelle Backup der wichtigen Logs
                if log_file.stat().st_size > 0:
                    backup_name = f"{log_file.stem}_backup_{datetime.now().strftime('%Y%m%d')}.log"
                    shutil.copy2(log_file, logs_dir / backup_name)
                
                # Lösche ursprüngliche Log-Datei
                log_file.unlink()
                print(f"   ✅ {log_file.name} bereinigt")
            except Exception as e:
                print(f"   ⚠️  Warnung bei {log_file.name}: {e}")

def main():
    """Hauptfunktion für Bereinigung"""
    print("=" * 60)
    print("🧹 DASHBOARD CLEANUP & REPAIR")
    print("=" * 60)
    print()
    
    # 1. Backup erstellen
    backup_dir = backup_database()
    
    # 2. Beispieldaten entfernen
    clean_example_data()
    
    # 3. Datenbankschema reparieren
    schema_ok = fix_user_creation_schema()
    
    # 4. API-Funktionalität überprüfen
    api_ok = verify_api_functionality()
    
    # 5. Frische Admin-Zugangsdaten
    admin_password = create_clean_admin_credentials()
    
    # 6. Log-Dateien bereinigen
    cleanup_log_files()
    
    print()
    print("=" * 60)
    print("✅ CLEANUP ABGESCHLOSSEN")
    print("=" * 60)
    print()
    
    if backup_dir:
        print(f"💾 Backup: {backup_dir}")
    print(f"🔑 Admin-Login: admin / {admin_password if admin_password else 'Siehe admin_credentials_clean.txt'}")
    print(f"🌐 URL: http://localhost:5000/admin/login")
    print()
    
    if schema_ok and api_ok:
        print("✅ System bereit für User-Erstellung!")
    else:
        print("⚠️  Bitte prüfen Sie die Fehlermeldungen oben")
    
    print()
    print("Nächste Schritte:")
    print("1. python app.py")
    print("2. Admin-Dashboard öffnen")
    print("3. Neue User erstellen")

if __name__ == "__main__":
    main()