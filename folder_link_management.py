# folder_link_management.py - API für Ordner- und Link-Zuweisung

import sqlite3
import os
import json
from datetime import datetime
from flask import request, jsonify, session

# ============================================================================
# ORDNER-MANAGEMENT FÜR GRUPPEN
# ============================================================================

@app.route('/api/admin/groups/<int:group_id>/folders', methods=['GET'])
@require_admin
def get_group_folders(group_id):
    """Holt alle Ordner einer Gruppe"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    c.execute("""SELECT id, name, icon, color, position, created_at
                 FROM group_tabs 
                 WHERE group_id = ?
                 ORDER BY position""", (group_id,))
    
    folders = []
    for row in c.fetchall():
        # Zähle Links in diesem Ordner
        c.execute("SELECT COUNT(*) FROM group_folder_links WHERE group_id = ? AND folder_tab_id = ?", 
                 (group_id, row[0]))
        link_count = c.fetchone()[0]
        
        folders.append({
            'id': row[0],
            'name': row[1],
            'icon': row[2],
            'color': row[3],
            'position': row[4],
            'created_at': row[5],
            'link_count': link_count
        })
    
    conn.close()
    return jsonify({'folders': folders})

@app.route('/api/admin/groups/<int:group_id>/folders', methods=['POST'])
@require_admin
def create_group_folder(group_id):
    """Erstellt einen neuen Ordner für eine Gruppe"""
    data = request.get_json()
    
    required_fields = ['name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Ordnername ist erforderlich'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Position bestimmen
        c.execute("SELECT MAX(position) FROM group_tabs WHERE group_id = ?", (group_id,))
        max_pos = c.fetchone()[0]
        position = (max_pos or 0) + 1
        
        # Ordner erstellen
        c.execute("""INSERT INTO group_tabs (group_id, name, icon, color, position, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (group_id, data['name'], data.get('icon', '📂'), 
                   data.get('color', '#10b981'), position, datetime.now()))
        
        folder_id = c.lastrowid
        
        # Ordner zu allen Gruppenmitgliedern hinzufügen
        c.execute("""SELECT u.username FROM users u
                     JOIN group_members gm ON u.id = gm.user_id
                     WHERE gm.group_id = ?""", (group_id,))
        
        members = c.fetchall()
        
        for member in members:
            username = member[0]
            add_folder_to_user(username, {
                'name': data['name'],
                'icon': data.get('icon', '📂'),
                'color': data.get('color', '#10b981'),
                'is_group_tab': True,
                'group_id': group_id
            })
        
        conn.commit()
        
        log_security_event('GROUP_FOLDER_CREATED', 
                          f"Admin created folder '{data['name']}' for group {group_id}", 
                          request.remote_addr)
        
        return jsonify({
            'success': True, 
            'folder_id': folder_id,
            'message': f"Ordner '{data['name']}' erstellt und {len(members)} Mitgliedern zugewiesen"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating group folder: {e}")
        return jsonify({'error': 'Fehler beim Erstellen des Ordners'}), 500
    finally:
        conn.close()

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>', methods=['PUT'])
@require_admin
def update_group_folder(group_id, folder_id):
    """Aktualisiert einen Gruppen-Ordner"""
    data = request.get_json()
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Ordner aktualisieren
        update_fields = []
        update_values = []
        
        if 'name' in data:
            update_fields.append('name = ?')
            update_values.append(data['name'])
        
        if 'icon' in data:
            update_fields.append('icon = ?')
            update_values.append(data['icon'])
        
        if 'color' in data:
            update_fields.append('color = ?')
            update_values.append(data['color'])
        
        if update_fields:
            update_values.extend([folder_id, group_id])
            c.execute(f"""UPDATE group_tabs 
                          SET {', '.join(update_fields)} 
                          WHERE id = ? AND group_id = ?""", update_values)
        
        # Änderungen zu allen Gruppenmitgliedern propagieren
        c.execute("""SELECT u.username FROM users u
                     JOIN group_members gm ON u.id = gm.user_id
                     WHERE gm.group_id = ?""", (group_id,))
        
        members = c.fetchall()
        
        for member in members:
            username = member[0]
            update_folder_for_user(username, group_id, data)
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Ordner aktualisiert'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating group folder: {e}")
        return jsonify({'error': 'Fehler beim Aktualisieren des Ordners'}), 500
    finally:
        conn.close()

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>', methods=['DELETE'])
@require_admin
def delete_group_folder(group_id, folder_id):
    """Löscht einen Gruppen-Ordner"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole Ordnername für Logging
        c.execute("SELECT name FROM group_tabs WHERE id = ? AND group_id = ?", (folder_id, group_id))
        folder_name = c.fetchone()
        if not folder_name:
            return jsonify({'error': 'Ordner nicht gefunden'}), 404
        
        folder_name = folder_name[0]
        
        # Lösche alle Links in diesem Ordner
        c.execute("DELETE FROM group_folder_links WHERE group_id = ? AND folder_tab_id = ?", 
                 (group_id, folder_id))
        
        # Lösche Ordner
        c.execute("DELETE FROM group_tabs WHERE id = ? AND group_id = ?", (folder_id, group_id))
        
        # Entferne Ordner von allen Gruppenmitgliedern
        c.execute("""SELECT u.username FROM users u
                     JOIN group_members gm ON u.id = gm.user_id
                     WHERE gm.group_id = ?""", (group_id,))
        
        members = c.fetchall()
        
        for member in members:
            username = member[0]
            remove_folder_from_user(username, group_id, folder_id)
        
        conn.commit()
        
        log_security_event('GROUP_FOLDER_DELETED', 
                          f"Admin deleted folder '{folder_name}' from group {group_id}", 
                          request.remote_addr)
        
        return jsonify({'success': True, 'message': f"Ordner '{folder_name}' gelöscht"})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting group folder: {e}")
        return jsonify({'error': 'Fehler beim Löschen des Ordners'}), 500
    finally:
        conn.close()

# ============================================================================
# LINK-MANAGEMENT FÜR GRUPPEN
# ============================================================================

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>/links', methods=['GET'])
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
    return jsonify({'links': links})

@app.route('/api/admin/groups/<int:group_id>/folders/<int:folder_id>/links', methods=['POST'])
@require_admin
def create_group_folder_link(group_id, folder_id):
    """Erstellt einen neuen Link in einem Gruppen-Ordner"""
    data = request.get_json()
    
    required_fields = ['name', 'url']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Name und URL sind erforderlich'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Position bestimmen
        c.execute("""SELECT MAX(position) FROM group_folder_links 
                     WHERE group_id = ? AND folder_tab_id = ?""", (group_id, folder_id))
        max_pos = c.fetchone()[0]
        position = (max_pos or 0) + 1
        
        # Link erstellen
        c.execute("""INSERT INTO group_folder_links 
                     (group_id, folder_tab_id, name, url, icon, color, position, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (group_id, folder_id, data['name'], data['url'], 
                   data.get('icon', '🔗'), data.get('color', '#10b981'), 
                   position, datetime.now()))
        
        link_id = c.lastrowid
        
        # Link zu allen Gruppenmitgliedern hinzufügen
        c.execute("""SELECT u.username FROM users u
                     JOIN group_members gm ON u.id = gm.user_id
                     WHERE gm.group_id = ?""", (group_id,))
        
        members = c.fetchall()
        
        for member in members:
            username = member[0]
            add_link_to_user_folder(username, group_id, folder_id, {
                'name': data['name'],
                'url': data['url'],
                'icon': data.get('icon', '🔗'),
                'color': data.get('color', '#10b981'),
                'is_group_link': True,
                'group_id': group_id,
                'group_link_id': link_id
            })
        
        conn.commit()
        
        log_security_event('GROUP_LINK_CREATED', 
                          f"Admin created link '{data['name']}' in group {group_id} folder {folder_id}", 
                          request.remote_addr)
        
        return jsonify({
            'success': True, 
            'link_id': link_id,
            'message': f"Link '{data['name']}' erstellt und {len(members)} Mitgliedern zugewiesen"
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating group folder link: {e}")
        return jsonify({'error': 'Fehler beim Erstellen des Links'}), 500
    finally:
        conn.close()

# ============================================================================
# INDIVIDUELLE ORDNER/LINK-ZUWEISUNG
# ============================================================================

@app.route('/api/admin/users/<int:user_id>/folders', methods=['GET'])
@require_admin
def get_user_folders(user_id):
    """Holt alle Ordner eines Users"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    # Hole Username
    c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404
    
    username = user[0]
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    if not os.path.exists(user_db_path):
        return jsonify({'folders': []})
    
    user_conn = sqlite3.connect(user_db_path)
    user_c = user_conn.cursor()
    
    user_c.execute("""SELECT id, name, icon, color, position, is_folder, is_group_tab, group_id, created_at
                      FROM tabs 
                      WHERE is_folder = 1
                      ORDER BY position""")
    
    folders = []
    for row in user_c.fetchall():
        # Zähle Links in diesem Ordner
        user_c.execute("SELECT COUNT(*) FROM folder_links WHERE folder_tab_id = ?", (row[0],))
        link_count = user_c.fetchone()[0]
        
        folders.append({
            'id': row[0],
            'name': row[1],
            'icon': row[2],
            'color': row[3],
            'position': row[4],
            'is_folder': bool(row[5]),
            'is_group_tab': bool(row[6]),
            'group_id': row[7],
            'created_at': row[8],
            'link_count': link_count
        })
    
    user_conn.close()
    conn.close()
    
    return jsonify({'folders': folders})

@app.route('/api/admin/users/<int:user_id>/folders', methods=['POST'])
@require_admin
def assign_folder_to_user(user_id):
    """Weist einem User einen individuellen Ordner zu"""
    data = request.get_json()
    
    required_fields = ['name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Ordnername ist erforderlich'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole Username
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({'error': 'User nicht gefunden'}), 404
        
        username = user[0]
        
        # Füge Ordner zu User hinzu
        folder_data = {
            'name': data['name'],
            'icon': data.get('icon', '📂'),
            'color': data.get('color', '#10b981'),
            'is_group_tab': False,
            'group_id': None
        }
        
        folder_id = add_folder_to_user(username, folder_data)
        
        # Links hinzufügen falls angegeben
        if 'links' in data and data['links']:
            for link_data in data['links']:
                add_link_to_user_folder_by_id(username, folder_id, {
                    'name': link_data['name'],
                    'url': link_data['url'],
                    'icon': link_data.get('icon', '🔗'),
                    'color': link_data.get('color', '#10b981'),
                    'is_group_link': False
                })
        
        log_security_event('USER_FOLDER_ASSIGNED', 
                          f"Admin assigned folder '{data['name']}' to user {username}", 
                          request.remote_addr)
        
        return jsonify({
            'success': True, 
            'folder_id': folder_id,
            'message': f"Ordner '{data['name']}' zu {username} hinzugefügt"
        })
        
    except Exception as e:
        logger.error(f"Error assigning folder to user: {e}")
        return jsonify({'error': 'Fehler beim Zuweisen des Ordners'}), 500
    finally:
        conn.close()

@app.route('/api/admin/users/<int:user_id>/folders/<int:folder_id>/links', methods=['POST'])
@require_admin
def assign_link_to_user_folder(user_id, folder_id):
    """Weist einem User-Ordner einen Link zu"""
    data = request.get_json()
    
    required_fields = ['name', 'url']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Name und URL sind erforderlich'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole Username
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({'error': 'User nicht gefunden'}), 404
        
        username = user[0]
        
        # Füge Link hinzu
        add_link_to_user_folder_by_id(username, folder_id, {
            'name': data['name'],
            'url': data['url'],
            'icon': data.get('icon', '🔗'),
            'color': data.get('color', '#10b981'),
            'is_group_link': False
        })
        
        log_security_event('USER_LINK_ASSIGNED', 
                          f"Admin assigned link '{data['name']}' to user {username}", 
                          request.remote_addr)
        
        return jsonify({
            'success': True,
            'message': f"Link '{data['name']}' zu {username} hinzugefügt"
        })
        
    except Exception as e:
        logger.error(f"Error assigning link to user: {e}")
        return jsonify({'error': 'Fehler beim Zuweisen des Links'}), 500
    finally:
        conn.close()

# ============================================================================
# HELPER FUNKTIONEN
# ============================================================================

def add_folder_to_user(username, folder_data):
    """Fügt einen Ordner zu einer User-Datenbank hinzu"""
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    # Erstelle User-DB falls nicht vorhanden
    if not os.path.exists(user_db_path):
        create_user_database(username)
    
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    try:
        # Position bestimmen
        c.execute("SELECT MAX(position) FROM tabs")
        max_pos = c.fetchone()[0]
        position = (max_pos or 0) + 1
        
        # Ordner hinzufügen
        c.execute("""INSERT INTO tabs (name, icon, color, position, is_folder, is_group_tab, group_id, created_at)
                     VALUES (?, ?, ?, ?, 1, ?, ?, ?)""",
                  (folder_data['name'], folder_data['icon'], folder_data['color'], 
                   position, folder_data.get('is_group_tab', False), 
                   folder_data.get('group_id'), datetime.now()))
        
        folder_id = c.lastrowid
        conn.commit()
        
        return folder_id
        
    finally:
        conn.close()

def add_link_to_user_folder(username, group_id, folder_id, link_data):
    """Fügt einen Link zu einem User-Ordner hinzu (für Gruppen-Sync)"""
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    if not os.path.exists(user_db_path):
        return
    
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    try:
        # Finde den entsprechenden Ordner-Tab in der User-DB
        c.execute("""SELECT id FROM tabs 
                     WHERE group_id = ? AND is_group_tab = 1 AND is_folder = 1""",
                  (group_id,))
        
        user_folders = c.fetchall()
        
        for user_folder in user_folders:
            user_folder_id = user_folder[0]
            
            # Position bestimmen
            c.execute("SELECT MAX(position) FROM folder_links WHERE folder_tab_id = ?", 
                     (user_folder_id,))
            max_pos = c.fetchone()[0]
            position = (max_pos or 0) + 1
            
            # Link hinzufügen
            c.execute("""INSERT INTO folder_links 
                         (folder_tab_id, name, url, icon, color, position, is_group_link, group_id, group_link_id)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (user_folder_id, link_data['name'], link_data['url'],
                       link_data['icon'], link_data['color'], position,
                       link_data.get('is_group_link', False), 
                       link_data.get('group_id'), 
                       link_data.get('group_link_id')))
        
        conn.commit()
        
    finally:
        conn.close()

def add_link_to_user_folder_by_id(username, folder_id, link_data):
    """Fügt einen Link zu einem spezifischen User-Ordner hinzu"""
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    if not os.path.exists(user_db_path):
        return
    
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    try:
        # Position bestimmen
        c.execute("SELECT MAX(position) FROM folder_links WHERE folder_tab_id = ?", (folder_id,))
        max_pos = c.fetchone()[0]
        position = (max_pos or 0) + 1
        
        # Link hinzufügen
        c.execute("""INSERT INTO folder_links 
                     (folder_tab_id, name, url, icon, color, position, is_group_link, group_id, group_link_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (folder_id, link_data['name'], link_data['url'],
                   link_data['icon'], link_data['color'], position,
                   link_data.get('is_group_link', False), 
                   link_data.get('group_id'), 
                   link_data.get('group_link_id')))
        
        conn.commit()
        
    finally:
        conn.close()

def update_folder_for_user(username, group_id, update_data):
    """Aktualisiert einen Gruppen-Ordner für einen User"""
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    if not os.path.exists(user_db_path):
        return
    
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    try:
        # Update Felder vorbereiten
        update_fields = []
        update_values = []
        
        if 'name' in update_data:
            update_fields.append('name = ?')
            update_values.append(update_data['name'])
        
        if 'icon' in update_data:
            update_fields.append('icon = ?')
            update_values.append(update_data['icon'])
        
        if 'color' in update_data:
            update_fields.append('color = ?')
            update_values.append(update_data['color'])
        
        if update_fields:
            update_values.append(group_id)
            c.execute(f"""UPDATE tabs 
                          SET {', '.join(update_fields)} 
                          WHERE group_id = ? AND is_group_tab = 1""", update_values)
            conn.commit()
        
    finally:
        conn.close()

def remove_folder_from_user(username, group_id, folder_id):
    """Entfernt einen Gruppen-Ordner von einem User"""
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    if not os.path.exists(user_db_path):
        return
    
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    try:
        # Lösche alle Links in Gruppen-Ordnern
        c.execute("DELETE FROM folder_links WHERE group_id = ?", (group_id,))
        
        # Lösche Gruppen-Ordner
        c.execute("DELETE FROM tabs WHERE group_id = ? AND is_group_tab = 1", (group_id,))
        
        conn.commit()
        
    finally:
        conn.close()

# ============================================================================
# BULK-OPERATIONEN
# ============================================================================

@app.route('/api/admin/bulk/assign-folders', methods=['POST'])
@require_admin
def bulk_assign_folders():
    """Weist mehreren Usern gleichzeitig Ordner zu"""
    data = request.get_json()
    
    required_fields = ['user_ids', 'folders']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'User-IDs und Ordner-Daten sind erforderlich'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        success_count = 0
        errors = []
        
        for user_id in data['user_ids']:
            try:
                # Hole Username
                c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                user = c.fetchone()
                if not user:
                    errors.append(f"User mit ID {user_id} nicht gefunden")
                    continue
                
                username = user[0]
                
                # Füge alle Ordner hinzu
                for folder_data in data['folders']:
                    folder_id = add_folder_to_user(username, folder_data)
                    
                    # Füge Links hinzu falls vorhanden
                    if 'links' in folder_data:
                        for link_data in folder_data['links']:
                            add_link_to_user_folder_by_id(username, folder_id, link_data)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Fehler bei User {user_id}: {str(e)}")
        
        message = f"{success_count} User erfolgreich aktualisiert"
        if errors:
            message += f", {len(errors)} Fehler aufgetreten"
        
        log_security_event('BULK_FOLDER_ASSIGNMENT', 
                          f"Admin assigned folders to {success_count} users", 
                          request.remote_addr)
        
        return jsonify({
            'success': True,
            'message': message,
            'success_count': success_count,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error in bulk folder assignment: {e}")
        return jsonify({'error': 'Fehler bei der Bulk-Zuweisung'}), 500
    finally:
        conn.close()

# ============================================================================
# TEMPLATE-SYSTEM FÜR ORDNER/LINKS
# ============================================================================

@app.route('/api/admin/templates/folders', methods=['GET'])
@require_admin
def get_folder_templates():
    """Holt vordefinierte Ordner-Templates"""
    templates = [
        {
            'id': 'development',
            'name': 'Entwicklung',
            'description': 'Standard-Ordner für Entwickler',
            'folders': [
                {
                    'name': 'GitHub',
                    'icon': '🐙',
                    'color': '#f1502f',
                    'links': [
                        {'name': 'GitHub', 'url': 'https://github.com', 'icon': '🐙'},
                        {'name': 'GitHub Desktop', 'url': 'https://desktop.github.com', 'icon': '💻'}
                    ]
                },
                {
                    'name': 'Dokumentation',
                    'icon': '📚',
                    'color': '#10b981',
                    'links': [
                        {'name': 'MDN Web Docs', 'url': 'https://developer.mozilla.org', 'icon': '📖'},
                        {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com', 'icon': '❓'}
                    ]
                }
            ]
        },
        {
            'id': 'marketing',
            'name': 'Marketing',
            'description': 'Standard-Ordner für Marketing-Team',
            'folders': [
                {
                    'name': 'Social Media',
                    'icon': '📱',
                    'color': '#e11d48',
                    'links': [
                        {'name': 'Facebook', 'url': 'https://facebook.com', 'icon': '📘'},
                        {'name': 'Twitter', 'url': 'https://twitter.com', 'icon': '🐦'},
                        {'name': 'LinkedIn', 'url': 'https://linkedin.com', 'icon': '💼'}
                    ]
                },
                {
                    'name': 'Analytics',
                    'icon': '📊',
                    'color': '#8b5cf6',
                    'links': [
                        {'name': 'Google Analytics', 'url': 'https://analytics.google.com', 'icon': '📈'},
                        {'name': 'Google Ads', 'url': 'https://ads.google.com', 'icon': '💰'}
                    ]
                }
            ]
        }
    ]
    
    return jsonify({'templates': templates})

@app.route('/api/admin/templates/folders/<template_id>/apply', methods=['POST'])
@require_admin
def apply_folder_template(template_id):
    """Wendet ein Ordner-Template auf User/Gruppen an"""
    data = request.get_json()
    
    # Hole Template
    templates_response = get_folder_templates()
    templates = templates_response.get_json()['templates']
    
    template = next((t for t in templates if t['id'] == template_id), None)
    if not template:
        return jsonify({'error': 'Template nicht gefunden'}), 404
    
    try:
        if 'user_ids' in data:
            # Auf User anwenden
            result = bulk_assign_folders()
            return result
        elif 'group_id' in data:
            # Auf Gruppe anwenden
            group_id = data['group_id']
            
            for folder_data in template['folders']:
                # Erstelle Ordner für Gruppe
                create_result = create_group_folder(group_id)
                if not create_result.get_json().get('success'):
                    continue
                
                folder_id = create_result.get_json()['folder_id']
                
                # Füge Links hinzu
                for link_data in folder_data.get('links', []):
                    create_group_folder_link(group_id, folder_id)
            
            return jsonify({'success': True, 'message': 'Template erfolgreich angewendet'})
        else:
            return jsonify({'error': 'User-IDs oder Gruppen-ID erforderlich'}), 400
            
    except Exception as e:
        logger.error(f"Error applying template: {e}")
        return jsonify({'error': 'Fehler beim Anwenden des Templates'}), 500