# ================================================================================
# DATENBANK-ERWEITERUNG FÜR LINKS IN ORDNERN
# ================================================================================

import sqlite3
import os

# 1. NEUE TABELLEN FÜR ADMIN.DB
def extend_admin_database():
    """Erweitert die Admin-Datenbank um Link-Funktionalität"""
    conn = sqlite3.connect('databases/admin.db')
    c = conn.cursor()
    
    # Neue Tabelle für Folder-Links in Gruppen
    c.execute('''CREATE TABLE IF NOT EXISTS group_folder_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        folder_tab_id INTEGER NOT NULL,  -- Bezieht sich auf group_tabs.id
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        icon TEXT DEFAULT '🔗',
        color TEXT DEFAULT '#10b981',
        position INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
        FOREIGN KEY (folder_tab_id) REFERENCES group_tabs (id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()

# 2. NEUE TABELLEN FÜR USER-DBS
def extend_user_database(username):
    """Erweitert eine User-Datenbank um Link-Funktionalität"""
    user_db_path = f'databases/user_{username}.db'
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    # Neue Tabelle für Links in Ordnern
    c.execute('''CREATE TABLE IF NOT EXISTS folder_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_tab_id INTEGER NOT NULL,  -- Bezieht sich auf tabs.id (wo is_folder=1)
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        icon TEXT DEFAULT '🔗',
        color TEXT DEFAULT '#10b981',
        position INTEGER DEFAULT 0,
        is_group_link BOOLEAN DEFAULT 0,  -- Ob der Link von einer Gruppe kommt
        group_id INTEGER,  -- Nur gesetzt wenn is_group_link=1
        group_link_id INTEGER,  -- Referenz zur group_folder_links.id
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (folder_tab_id) REFERENCES tabs (id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()

# ================================================================================
# NEUE API ENDPOINTS FÜR LINKS
# ================================================================================

from flask import request, jsonify, session

# ============================================================================
# ADMIN ENDPOINTS - GRUPPEN-ORDNER-LINKS
# ============================================================================

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>/links')
@require_admin
def get_group_folder_links(group_id, folder_id):
    """Holt alle Links eines Gruppen-Ordners"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    c.execute("""SELECT id, name, url, icon, color, position, created_at
                 FROM group_folder_links 
                 WHERE group_id = ? AND folder_tab_id = ?
                 ORDER BY position""", (group_id, folder_id))
    
    links = []
    for row in c.fetchall():
        links.append({
            'id': row[0],
            'name': row[1],
            'url': row[2],
            'icon': row[3],
            'color': row[4],
            'position': row[5],
            'created_at': row[6]
        })
    
    conn.close()
    return jsonify(links)

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>/links', methods=['POST'])
@require_admin
def create_group_folder_link(group_id, folder_id):
    """Erstellt einen neuen Link in einem Gruppen-Ordner"""
    data = request.get_json()
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    # Position bestimmen
    c.execute("SELECT MAX(position) FROM group_folder_links WHERE group_id = ? AND folder_tab_id = ?",
              (group_id, folder_id))
    max_pos = c.fetchone()[0]
    position = (max_pos or 0) + 1
    
    # Link erstellen
    c.execute("""INSERT INTO group_folder_links (group_id, folder_tab_id, name, url, icon, color, position)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (group_id, folder_id, data['name'], data['url'], 
               data.get('icon', '🔗'), data.get('color', '#10b981'), position))
    
    link_id = c.lastrowid
    
    # Link zu allen Gruppenmitgliedern hinzufügen
    c.execute("""SELECT u.username FROM users u
                 JOIN group_members gm ON u.id = gm.user_id
                 WHERE gm.group_id = ?""", (group_id,))
    
    members = c.fetchall()
    
    for member in members:
        user_db_path = os.path.join(DATABASE_DIR, f'user_{member[0]}.db')
        if os.path.exists(user_db_path):
            user_conn = sqlite3.connect(user_db_path)
            user_c = user_conn.cursor()
            
            # Finde den entsprechenden Ordner-Tab in der User-DB
            user_c.execute("""SELECT id FROM tabs 
                              WHERE group_id = ? AND is_group_tab = 1 AND is_folder = 1
                              AND position = (SELECT position FROM group_tabs WHERE id = ?)""",
                           (group_id, folder_id))
            
            user_folder_result = user_c.fetchone()
            if user_folder_result:
                user_folder_id = user_folder_result[0]
                
                # Position in User-DB bestimmen
                user_c.execute("SELECT MAX(position) FROM folder_links WHERE folder_tab_id = ?", 
                               (user_folder_id,))
                user_max_pos = user_c.fetchone()[0]
                user_position = (user_max_pos or 0) + 1
                
                # Link hinzufügen
                user_c.execute("""INSERT INTO folder_links 
                                  (folder_tab_id, name, url, icon, color, position, is_group_link, group_id, group_link_id)
                                  VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                               (user_folder_id, data['name'], data['url'],
                                data.get('icon', '🔗'), data.get('color', '#10b981'),
                                user_position, group_id, link_id))
            
            user_conn.commit()
            user_conn.close()
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'link_id': link_id})

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>/links/<int:link_id>', methods=['PUT'])
@require_admin
def update_group_folder_link(group_id, folder_id, link_id):
    """Aktualisiert einen Gruppen-Ordner-Link"""
    data = request.get_json()
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    # Link aktualisieren
    c.execute("""UPDATE group_folder_links 
                 SET name = ?, url = ?, icon = ?, color = ?
                 WHERE id = ? AND group_id = ? AND folder_tab_id = ?""",
              (data['name'], data['url'], data['icon'], data['color'], 
               link_id, group_id, folder_id))
    
    # Link in allen User-Datenbanken aktualisieren
    c.execute("""SELECT u.username FROM users u
                 JOIN group_members gm ON u.id = gm.user_id
                 WHERE gm.group_id = ?""", (group_id,))
    
    members = c.fetchall()
    
    for member in members:
        user_db_path = os.path.join(DATABASE_DIR, f'user_{member[0]}.db')
        if os.path.exists(user_db_path):
            user_conn = sqlite3.connect(user_db_path)
            user_c = user_conn.cursor()
            
            user_c.execute("""UPDATE folder_links 
                              SET name = ?, url = ?, icon = ?, color = ?
                              WHERE group_link_id = ? AND is_group_link = 1""",
                           (data['name'], data['url'], data['icon'], data['color'], link_id))
            
            user_conn.commit()
            user_conn.close()
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>/links/<int:link_id>', methods=['DELETE'])
@require_admin
def delete_group_folder_link(group_id, folder_id, link_id):
    """Löscht einen Gruppen-Ordner-Link"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    # Link aus group_folder_links löschen
    c.execute("DELETE FROM group_folder_links WHERE id = ? AND group_id = ? AND folder_tab_id = ?", 
              (link_id, group_id, folder_id))
    
    # Link aus allen User-Datenbanken löschen
    c.execute("""SELECT u.username FROM users u
                 JOIN group_members gm ON u.id = gm.user_id
                 WHERE gm.group_id = ?""", (group_id,))
    
    members = c.fetchall()
    
    for member in members:
        user_db_path = os.path.join(DATABASE_DIR, f'user_{member[0]}.db')
        if os.path.exists(user_db_path):
            user_conn = sqlite3.connect(user_db_path)
            user_c = user_conn.cursor()
            
            user_c.execute("DELETE FROM folder_links WHERE group_link_id = ? AND is_group_link = 1", 
                           (link_id,))
            
            user_conn.commit()
            user_conn.close()
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ============================================================================
# USER ENDPOINTS - ORDNER-LINKS ANZEIGEN
# ============================================================================

@app.route('/api/folders/<int:folder_id>/links')
@require_login
def get_folder_links(folder_id):
    """Holt alle Links eines Ordners für den aktuellen User"""
    db_path = get_user_db_path()
    if not db_path:
        return jsonify({'error': 'Keine Benutzerdatenbank gefunden'}), 404

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""SELECT id, name, url, icon, color, position, is_group_link, group_id
                 FROM folder_links 
                 WHERE folder_tab_id = ?
                 ORDER BY position""", (folder_id,))
    
    links = []
    for row in c.fetchall():
        links.append({
            'id': row[0],
            'name': row[1],
            'url': row[2],
            'icon': row[3],
            'color': row[4],
            'position': row[5],
            'is_group_link': bool(row[6]),
            'group_id': row[7]
        })
    
    conn.close()
    return jsonify(links)

@app.route('/api/folders/<int:folder_id>/links', methods=['POST'])
@require_login
def create_user_folder_link(folder_id):
    """Erstellt einen neuen persönlichen Link in einem Ordner"""
    # Berechtigung prüfen
    if not check_user_permissions(session['user_id'], 'add_delete'):
        return jsonify({'success': False, 'error': 'Keine Berechtigung'}), 403

    data = request.json
    db_path = get_user_db_path()
    if not db_path:
        return jsonify({'error': 'Keine Benutzerdatenbank gefunden'}), 404

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Position bestimmen
    c.execute("SELECT MAX(position) FROM folder_links WHERE folder_tab_id = ?", (folder_id,))
    max_pos = c.fetchone()[0]
    position = (max_pos or 0) + 1

    c.execute("""INSERT INTO folder_links (folder_tab_id, name, url, icon, color, position, is_group_link)
                 VALUES (?, ?, ?, ?, ?, ?, 0)""",
              (folder_id, data['name'], data['url'], 
               data.get('icon', '🔗'), data.get('color', '#10b981'), position))

    link_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'link_id': link_id})

# ============================================================================
# SYNCHRONISATION BEIM GRUPPENBEITRITT
# ============================================================================

def sync_group_links_to_user(group_id, username):
    """Synchronisiert alle Gruppen-Links zu einem neuen Gruppenmitglied"""
    admin_conn = sqlite3.connect(ADMIN_DB)
    admin_c = admin_conn.cursor()
    
    # Hole alle Links aller Ordner dieser Gruppe
    admin_c.execute("""
        SELECT gfl.id, gfl.folder_tab_id, gfl.name, gfl.url, gfl.icon, gfl.color, gfl.position
        FROM group_folder_links gfl
        WHERE gfl.group_id = ?
        ORDER BY gfl.folder_tab_id, gfl.position
    """, (group_id,))
    
    group_links = admin_c.fetchall()
    admin_conn.close()
    
    if not group_links:
        return
    
    # Füge Links zur User-DB hinzu
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    user_conn = sqlite3.connect(user_db_path)
    user_c = user_conn.cursor()
    
    for link in group_links:
        group_link_id, group_folder_id, name, url, icon, color, position = link
        
        # Finde den entsprechenden Ordner-Tab in der User-DB
        user_c.execute("""SELECT id FROM tabs 
                          WHERE group_id = ? AND is_group_tab = 1 AND is_folder = 1""",
                       (group_id,))
        
        user_folders = user_c.fetchall()
        
        for user_folder in user_folders:
            user_folder_id = user_folder[0]
            
            # Position in User-DB bestimmen
            user_c.execute("SELECT MAX(position) FROM folder_links WHERE folder_tab_id = ?", 
                           (user_folder_id,))
            user_max_pos = user_c.fetchone()[0]
            user_position = (user_max_pos or 0) + 1
            
            # Link hinzufügen
            user_c.execute("""INSERT INTO folder_links 
                              (folder_tab_id, name, url, icon, color, position, is_group_link, group_id, group_link_id)
                              VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                           (user_folder_id, name, url, icon, color, user_position, group_id, group_link_id))
    
    user_conn.commit()
    user_conn.close()

# ============================================================================
# AKTUALISIERUNG DER BESTEHENDEN FUNKTIONEN
# ============================================================================

# Den add_group_member Endpoint erweitern:
@app.route('/api/admin/groups/<int:group_id>/members', methods=['POST'])
@require_admin
def add_group_member_extended(group_id):
    """Fügt einen User zu einer Gruppe hinzu (mit Link-Synchronisation)"""
    data = request.get_json()
    user_id = data['user_id']
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
                  (group_id, user_id))
        
        # Kopiere Gruppen-Tabs in User-Datenbank
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = c.fetchone()[0]
        
        # Erst die Tabs kopieren (wie bisher)
        c.execute("""SELECT name, url, color, icon, position, parent_id, is_folder
                     FROM group_tabs WHERE group_id = ? ORDER BY position""", (group_id,))
        group_tabs = c.fetchall()
        
        if group_tabs:
            user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
            user_conn = sqlite3.connect(user_db_path)
            user_c = user_conn.cursor()
            
            for tab in group_tabs:
                user_c.execute("""INSERT INTO tabs (name, url, color, icon, position, parent_id, is_folder, is_group_tab, group_id)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                               (*tab, group_id))
            
            user_conn.commit()
            user_conn.close()
        
        # Dann die Links synchronisieren (NEU!)
        sync_group_links_to_user(group_id, username)
        
        conn.commit()
        return jsonify({'success': True})
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User ist bereits Mitglied dieser Gruppe'}), 400
    finally:
        conn.close()

# ================================================================================
# MIGRATIONS-SCRIPT ZUM ERWEITERN BESTEHENDER DATENBANKEN
# ================================================================================

def migrate_existing_databases():
    """Migriert bestehende Datenbanken zur neuen Link-Struktur"""
    print("🔄 Migriere Datenbanken für Link-Funktionalität...")
    
    # 1. Admin-DB erweitern
    extend_admin_database()
    print("✅ Admin-Datenbank erweitert")
    
    # 2. Alle User-DBs finden und erweitern
    import glob
    user_dbs = glob.glob('databases/user_*.db')
    
    for user_db_path in user_dbs:
        # Username aus Pfad extrahieren
        username = user_db_path.split('user_')[1].split('.db')[0]
        extend_user_database(username)
        print(f"✅ User-Datenbank für {username} erweitert")
    
    print("🎉 Migration abgeschlossen!")

if __name__ == "__main__":
    migrate_existing_databases()