# security_middleware.py - Erweiterte Sicherheitsfunktionen für User-Management

import sqlite3
import os
import time
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, jsonify, redirect, url_for, g
import logging

# ============================================================================
# BERECHTIGUNGS-MIDDLEWARE
# ============================================================================

def check_user_permission(permission_name):
    """Decorator um User-Berechtigungen zu überprüfen"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return jsonify({'error': 'Nicht angemeldet'}), 401
            
            user_id = session.get('user_id')
            
            if not has_user_permission(user_id, permission_name):
                log_security_event('PERMISSION_DENIED', 
                                 f"User {session.get('username')} attempted {permission_name}", 
                                 request.remote_addr)
                return jsonify({'error': f'Berechtigung "{permission_name}" erforderlich'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_user_permission(user_id, permission_name):
    """Überprüft ob ein User eine spezifische Berechtigung hat"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole User-Berechtigungen aus users-Tabelle
        permission_column = f'can_{permission_name}'
        c.execute(f"SELECT {permission_column} FROM users WHERE id = ? AND is_active = 1", (user_id,))
        result = c.fetchone()
        
        if result:
            return bool(result[0])
        
        # Falls nicht in Haupt-Spalten, prüfe user_permissions Tabelle
        c.execute("""SELECT permission_value FROM user_permissions 
                     WHERE user_id = ? AND permission_name = ?""", 
                  (user_id, permission_name))
        
        perm_result = c.fetchone()
        return bool(perm_result[0]) if perm_result else False
        
    except Exception as e:
        logger.error(f"Error checking user permission: {e}")
        return False
    finally:
        conn.close()

def get_user_permissions(user_id):
    """Holt alle Berechtigungen eines Users"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole Standard-Berechtigungen
        c.execute("""SELECT can_edit_links, can_delete_links, can_add_links 
                     FROM users WHERE id = ?""", (user_id,))
        
        result = c.fetchone()
        if not result:
            return {}
        
        permissions = {
            'edit_links': bool(result[0]),
            'delete_links': bool(result[1]),
            'add_links': bool(result[2])
        }
        
        # Hole erweiterte Berechtigungen
        c.execute("""SELECT permission_name, permission_value 
                     FROM user_permissions WHERE user_id = ?""", (user_id,))
        
        for perm in c.fetchall():
            permissions[perm[0]] = bool(perm[1])
        
        return permissions
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {}
    finally:
        conn.close()

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.blocked_ips = {}
    
    def is_allowed(self, identifier, max_requests=60, window_seconds=60):
        """Überprüft ob Request erlaubt ist"""
        current_time = time.time()
        
        # Prüfe ob IP blockiert ist
        if identifier in self.blocked_ips:
            block_time = self.blocked_ips[identifier]
            if current_time - block_time < 300:  # 5 Minuten Sperre
                return False
            else:
                del self.blocked_ips[identifier]
        
        # Bereinige alte Requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < window_seconds
            ]
        else:
            self.requests[identifier] = []
        
        # Prüfe Limit
        if len(self.requests[identifier]) >= max_requests:
            self.blocked_ips[identifier] = current_time
            log_security_event('RATE_LIMIT_EXCEEDED', 
                             f"Rate limit exceeded for {identifier}", 
                             identifier)
            return False
        
        # Füge aktuellen Request hinzu
        self.requests[identifier].append(current_time)
        return True

rate_limiter = RateLimiter()

def rate_limit(max_requests=60, window_seconds=60):
    """Rate Limiting Decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            
            if not rate_limiter.is_allowed(identifier, max_requests, window_seconds):
                return jsonify({
                    'error': 'Rate limit exceeded. Versuchen Sie es später erneut.'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ============================================================================
# SESSION-MANAGEMENT
# ============================================================================

def extend_session():
    """Verlängert die Session wenn User aktiv ist"""
    if session.get('user_id'):
        session.permanent = True
        session.modified = True
        
        # Update last_activity in Datenbank
        conn = sqlite3.connect(ADMIN_DB)
        c = conn.cursor()
        
        try:
            c.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                     (datetime.now(), session.get('user_id')))
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating last activity: {e}")
        finally:
            conn.close()

def cleanup_expired_sessions():
    """Bereinigt abgelaufene Sessions"""
    # Diese Funktion sollte regelmäßig aufgerufen werden (z.B. via Cron)
    expiry_time = datetime.now() - timedelta(hours=24)
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Logge abgelaufene Sessions
        c.execute("""SELECT username FROM users 
                     WHERE last_login < ? AND last_login IS NOT NULL""", 
                  (expiry_time,))
        
        expired_users = c.fetchall()
        
        for user in expired_users:
            log_security_event('SESSION_EXPIRED', 
                             f"Session expired for user {user[0]}", 
                             'system')
        
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
    finally:
        conn.close()

# ============================================================================
# AUDIT LOGGING
# ============================================================================

def log_user_action(action, target_type=None, target_id=None, details=None):
    """Loggt User-Aktionen in der User-Datenbank"""
    if not session.get('user_id') or not session.get('username'):
        return
    
    username = session.get('username')
    user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
    
    if not os.path.exists(user_db_path):
        return
    
    conn = sqlite3.connect(user_db_path)
    c = conn.cursor()
    
    try:
        c.execute("""INSERT INTO user_activity 
                     (action, target_type, target_id, details, created_at)
                     VALUES (?, ?, ?, ?, ?)""",
                  (action, target_type, target_id, details, datetime.now()))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging user action: {e}")
    finally:
        conn.close()

def log_admin_action(action, target_type=None, target_id=None, details=None):
    """Loggt Admin-Aktionen in der Admin-Datenbank"""
    if not session.get('admin_username'):
        return
    
    admin_username = session.get('admin_username')
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        c.execute("""INSERT INTO user_audit_log 
                     (user_id, action, target_type, target_id, details, ip_address, user_agent, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (None, f"ADMIN_{action}", target_type, target_id, 
                   f"Admin {admin_username}: {details}", 
                   request.remote_addr, request.headers.get('User-Agent'), datetime.now()))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")
    finally:
        conn.close()

# ============================================================================
# SICHERHEITS-VALIDIERUNG
# ============================================================================

def validate_url(url):
    """Validiert URLs für Sicherheit"""
    if not url:
        return False
    
    # Grundlegende URL-Validierung
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    # Blacklist gefährlicher Domänen/Protokolle
    dangerous_patterns = [
        'javascript:', 'data:', 'vbscript:', 'file:', 'ftp:',
        'localhost', '127.0.0.1', '0.0.0.0', '192.168.', '10.0.', '172.'
    ]
    
    url_lower = url.lower()
    for pattern in dangerous_patterns:
        if pattern in url_lower:
            return False
    
    return True

def sanitize_input(text, max_length=None):
    """Bereinigt User-Input"""
    if not text:
        return ""
    
    # HTML-Tags entfernen
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # SQL-Injection verhindern
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Länge begrenzen
    if max_length:
        text = text[:max_length]
    
    return text.strip()

def check_password_strength(password):
    """Überprüft Passwort-Stärke"""
    if len(password) < 8:
        return False, "Passwort muss mindestens 8 Zeichen haben"
    
    if not any(c.isupper() for c in password):
        return False, "Passwort muss mindestens einen Großbuchstaben enthalten"
    
    if not any(c.islower() for c in password):
        return False, "Passwort muss mindestens einen Kleinbuchstaben enthalten"
    
    if not any(c.isdigit() for c in password):
        return False, "Passwort muss mindestens eine Zahl enthalten"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Passwort muss mindestens ein Sonderzeichen enthalten"
    
    return True, "Passwort ist stark genug"

# ============================================================================
# MIDDLEWARE INTEGRATION
# ============================================================================

def init_security_middleware(app):
    """Initialisiert Security-Middleware"""
    
    @app.before_request
    def security_before_request():
        """Wird vor jedem Request ausgeführt"""
        
        # Rate Limiting für API-Endpunkte
        if request.path.startswith('/api/'):
            if not rate_limiter.is_allowed(request.remote_addr, 100, 60):
                return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Session verlängern bei Aktivität
        if session.get('user_id') or session.get('admin_username'):
            extend_session()
        
        # User-Berechtigungen in g verfügbar machen
        if session.get('user_id'):
            g.user_permissions = get_user_permissions(session.get('user_id'))
        
        # HTTPS-Erzwingung (in Produktion)
        if not request.is_secure and app.config.get('FORCE_HTTPS', False):
            return redirect(request.url.replace('http://', 'https://'))
    
    @app.after_request
    def security_after_request(response):
        """Wird nach jedem Request ausgeführt"""
        
        # Security Headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
        )
        
        return response

# ============================================================================
# BERECHTIGUNGS-HELPER
# ============================================================================

def require_permission(permission):
    """Vereinfachter Berechtigungs-Decorator"""
    return check_user_permission(permission)

def can_edit_links():
    """Prüft ob User Links bearbeiten darf"""
    return has_user_permission(session.get('user_id'), 'edit_links')

def can_delete_links():
    """Prüft ob User Links löschen darf"""
    return has_user_permission(session.get('user_id'), 'delete_links')

def can_add_links():
    """Prüft ob User Links hinzufügen darf"""
    return has_user_permission(session.get('user_id'), 'add_links')

# ============================================================================
# API-ENDPUNKTE FÜR BERECHTIGUNGEN
# ============================================================================

@app.route('/api/user/permissions', methods=['GET'])
@require_login
def get_current_user_permissions():
    """Holt die Berechtigungen des aktuellen Users"""
    user_id = session.get('user_id')
    permissions = get_user_permissions(user_id)
    
    return jsonify({
        'permissions': permissions,
        'user_id': user_id,
        'username': session.get('username')
    })

@app.route('/api/admin/users/<int:user_id>/permissions', methods=['PUT'])
@require_admin
def update_user_permissions(user_id):
    """Aktualisiert die Berechtigungen eines Users"""
    data = request.get_json()
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Standard-Berechtigungen aktualisieren
        standard_perms = ['can_edit_links', 'can_delete_links', 'can_add_links']
        
        for perm in standard_perms:
            if perm in data:
                c.execute(f"UPDATE users SET {perm} = ? WHERE id = ?", 
                         (data[perm], user_id))
        
        # Erweiterte Berechtigungen aktualisieren
        for perm_name, perm_value in data.items():
            if perm_name not in standard_perms and perm_name.startswith('can_'):
                # Entferne 'can_' Prefix für Datenbank
                clean_perm_name = perm_name[4:]
                
                c.execute("""INSERT OR REPLACE INTO user_permissions 
                             (user_id, permission_name, permission_value, granted_by, granted_at)
                             VALUES (?, ?, ?, ?, ?)""",
                          (user_id, clean_perm_name, perm_value, 
                           session.get('user_id'), datetime.now()))
        
        conn.commit()
        
        # Hole Username für Logging
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = c.fetchone()[0]
        
        log_admin_action('PERMISSION_UPDATE', 'user', user_id, 
                        f"Updated permissions for user {username}")
        
        return jsonify({'success': True, 'message': 'Berechtigungen aktualisiert'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating user permissions: {e}")
        return jsonify({'error': 'Fehler beim Aktualisieren der Berechtigungen'}), 500
    finally:
        conn.close()

@app.route('/api/admin/security/logs', methods=['GET'])
@require_admin
def get_security_logs():
    """Holt Security-Logs"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        c.execute("""SELECT event_type, event_data, ip_address, timestamp
                     FROM security_log 
                     ORDER BY timestamp DESC 
                     LIMIT ? OFFSET ?""", (limit, offset))
        
        logs = []
        for row in c.fetchall():
            logs.append({
                'event_type': row[0],
                'event_data': row[1],
                'ip_address': row[2],
                'timestamp': row[3]
            })
        
        # Hole Gesamtanzahl
        c.execute("SELECT COUNT(*) FROM security_log")
        total_count = c.fetchone()[0]
        
        return jsonify({
            'logs': logs,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting security logs: {e}")
        return jsonify({'error': 'Fehler beim Laden der Logs'}), 500
    finally:
        conn.close()

# ============================================================================
# CLEANUP FUNKTIONEN
# ============================================================================

def cleanup_old_logs(days_to_keep=30):
    """Bereinigt alte Log-Einträge"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Lösche alte Security-Logs
        c.execute("DELETE FROM security_log WHERE timestamp < ?", (cutoff_date,))
        security_deleted = c.rowcount
        
        # Lösche alte Audit-Logs
        c.execute("DELETE FROM user_audit_log WHERE created_at < ?", (cutoff_date,))
        audit_deleted = c.rowcount
        
        conn.commit()
        
        logger.info(f"Cleanup completed: {security_deleted} security logs, {audit_deleted} audit logs deleted")
        
    except Exception as e:
        logger.error(f"Error during log cleanup: {e}")
    finally:
        conn.close()

def init_security_cleanup_job(app):
    """Initialisiert regelmäßige Cleanup-Jobs"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            time.sleep(86400)  # 24 Stunden
            with app.app_context():
                cleanup_old_logs()
                cleanup_expired_sessions()
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()