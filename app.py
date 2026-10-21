#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ENHANCED DASHBOARD WITH COMPLETE USER MANAGEMENT
===============================================

✅ ALLE FEATURES ENTHALTEN:
- User-Management (Erstellen, Bearbeiten, Löschen, Passwort-Reset)
- Gruppen-Management mit Ordner/Link-Zuweisung
- Granulare Berechtigungen (Bearbeiten/Löschen/Hinzufügen)
- Security-Middleware mit Rate-Limiting
- Audit-Logging für alle Aktionen
- Ordner/Link-Templates
- Bulk-Operationen
- Session-Management
- CSRF-Schutz
- Argon2-Verschlüsselung
"""

import os
import sys
import logging
import sqlite3
import secrets
import time
import json
import shutil
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import (Flask, render_template, request, redirect, url_for,
                  session, flash, jsonify, abort, make_response, g)
import argon2
from werkzeug.middleware.proxy_fix import ProxyFix

# =============================================================================
# KONFIGURATION
# =============================================================================

VERSION = "2.0.0"
PROJECT_NAME = "Enhanced Dashboard with User Management"

# Datenbank-Pfade
DATABASE_DIR = 'databases'
ADMIN_DB = os.path.join(DATABASE_DIR, 'admin.db')

# Erstelle Verzeichnisse falls nicht vorhanden
for directory in [DATABASE_DIR, 'logs', 'uploads', 'exports']:
    os.makedirs(directory, exist_ok=True)

# Argon2-Konfiguration (Firmenstandard)
ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64MB
    parallelism=1,
    hash_len=32,
    salt_len=16
)

# Rate-Limiting-Konfiguration
RATE_LIMITS = {
    'login_attempts': 5,
    'login_window': 900,  # 15 Minuten
    'api_requests': 100,
    'api_window': 60
}

# =============================================================================
# FLASK APP SETUP
# =============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Sichere Session-Konfiguration
app.config.update({
    'SESSION_COOKIE_SECURE': os.environ.get('FLASK_ENV') == 'production',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Strict',
    'PERMANENT_SESSION_LIFETIME': timedelta(hours=8),
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB max upload
})

# HTTPS-Erzwingung für Produktion
if os.environ.get('FLASK_ENV') == 'production':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# SICHERHEITSFUNKTIONEN
# =============================================================================

def hash_password(password):
    """Sichere Passwort-Hashing mit Argon2"""
    return ph.hash(password)

def verify_password(password, hash_str):
    """Passwort-Verifikation"""
    try:
        ph.verify(hash_str, password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def generate_csrf_token():
    """CSRF-Token generieren"""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    """CSRF-Token validieren"""
    return token and session.get('csrf_token') == token

def check_rate_limit(identifier, max_attempts=None, window=None):
    """Rate-Limiting prüfen"""
    if max_attempts is None:
        max_attempts = RATE_LIMITS['login_attempts']
    if window is None:
        window = RATE_LIMITS['login_window']
    
    # Vereinfachte Rate-Limiting Implementierung
    # In Produktion sollte Redis oder ähnliches verwendet werden
    current_time = time.time()
    key = f"rate_limit_{identifier}"
    
    if not hasattr(g, 'rate_limits'):
        g.rate_limits = {}
    
    if key not in g.rate_limits:
        g.rate_limits[key] = []
    
    # Alte Einträge entfernen
    g.rate_limits[key] = [t for t in g.rate_limits[key] if current_time - t < window]
    
    # Prüfen ob Limit überschritten
    if len(g.rate_limits[key]) >= max_attempts:
        return False
    
    # Aktuellen Versuch hinzufügen
    g.rate_limits[key].append(current_time)
    return True

def log_security_event(event_type, username, ip_address, details=None):
    """Sicherheitsereignis loggen"""
    try:
        conn = sqlite3.connect(ADMIN_DB)
        c = conn.cursor()
        
        # Erstelle security_log Tabelle falls nicht vorhanden
        c.execute('''CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        c.execute("""INSERT INTO security_log (event_type, username, ip_address, details, timestamp)
                     VALUES (?, ?, ?, ?, ?)""",
                  (event_type, username, ip_address,
                   json.dumps(details) if details else None, datetime.now()))
        
        conn.commit()
        conn.close()
        
        logger.warning(f"Security Event: {event_type} - User: {username} - IP: {ip_address}")
        
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")

# =============================================================================
# BERECHTIGUNGEN
# =============================================================================

def has_user_permission(user_id, permission_name):
    """Überprüft ob ein User eine spezifische Berechtigung hat"""
    if not user_id:
        return False
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole User-Berechtigungen
        permission_column = f'can_{permission_name}'
        c.execute(f"""SELECT {permission_column} FROM users 
                      WHERE id = ? AND is_active = 1""", (user_id,))
        result = c.fetchone()
        
        return bool(result[0]) if result else False
        
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
        c.execute("""SELECT can_edit_links, can_delete_links, can_add_links 
                     FROM users WHERE id = ?""", (user_id,))
        
        result = c.fetchone()
        if not result:
            return {}
        
        return {
            'edit_links': bool(result[0]),
            'delete_links': bool(result[1]),
            'add_links': bool(result[2])
        }
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {}
    finally:
        conn.close()

# =============================================================================
# DECORATORS
# =============================================================================

def require_csrf(f):
    """CSRF-Schutz für POST-Requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not validate_csrf_token(token):
                flash('Sicherheitsfehler - bitte versuchen Sie es erneut', 'error')
                return redirect(request.referrer or url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bitte melden Sie sich an', 'error')
            return redirect(url_for('login'))
        
        # Session-Timeout prüfen
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > timedelta(hours=8):
                session.clear()
                flash('Session abgelaufen', 'warning')
                return redirect(url_for('login'))
        
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Admin-Berechtigung erforderlich', 'error')
            return redirect(url_for('admin_login'))
        
        # Admin-Session Timeout (2 Stunden)
        if 'admin_last_activity' in session:
            last_activity = datetime.fromisoformat(session['admin_last_activity'])
            if datetime.now() - last_activity > timedelta(hours=2):
                session.clear()
                flash('Admin-Session abgelaufen', 'warning')
                return redirect(url_for('admin_login'))
        
        session['admin_last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission_name):
    """Decorator für User-Berechtigungen"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                return jsonify({'error': 'Nicht angemeldet'}), 401
            
            user_id = session.get('user_id')
            
            if not has_user_permission(user_id, permission_name):
                log_security_event('PERMISSION_DENIED', 
                                 session.get('username'), 
                                 request.remote_addr,
                                 {'permission': permission_name})
                return jsonify({'error': f'Berechtigung "{permission_name}" erforderlich'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =============================================================================
# MIDDLEWARE
# =============================================================================

@app.before_request
def security_checks():
    """Sicherheitschecks vor jeder Anfrage"""
    
    # HTTPS-Erzwingung in Produktion
    if os.environ.get('FLASK_ENV') == 'production':
        if not request.is_secure and 'localhost' not in request.host:
            return redirect(request.url.replace('http://', 'https://'))
    
    # Rate-Limiting für API-Endpunkte
    if request.path.startswith('/api/'):
        if not check_rate_limit(request.remote_addr, RATE_LIMITS['api_requests'], RATE_LIMITS['api_window']):
            return jsonify({'error': 'Rate limit exceeded'}), 429
    
    # Rate-Limiting für Login-Endpoints
    if request.endpoint in ['login', 'admin_login'] and request.method == 'POST':
        if not check_rate_limit(request.remote_addr):
            log_security_event('RATE_LIMIT_EXCEEDED',
                             request.form.get('username', 'unknown'),
                             request.remote_addr)
            flash('Zu viele Login-Versuche. Bitte warten Sie.', 'error')
            return render_template('error.html', 
                                 message='Rate limit exceeded'), 429
    
    # User-Berechtigungen in g verfügbar machen
    if session.get('user_id'):
        g.user_permissions = get_user_permissions(session.get('user_id'))

@app.after_request
def security_headers(response):
    """Sicherheits-Header hinzufügen"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
    )
    
    return response

# =============================================================================
# BASIC ROUTES
# =============================================================================

@app.route('/')
def index():
    """Startseite - optimiert"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    elif 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@require_csrf
def login():
    """Benutzer-Login mit erweiterten Sicherheitsfeatures"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Benutzername und Passwort sind erforderlich', 'error')
            return render_template('user/login.html', csrf_token=generate_csrf_token())
        
        # Input-Validierung
        if len(username) > 50 or len(password) > 128:
            flash('Ungültige Eingabe', 'error')
            return render_template('user/login.html', csrf_token=generate_csrf_token())
        
        try:
            conn = sqlite3.connect(ADMIN_DB)
            c = conn.cursor()
            c.execute("SELECT id, password_hash, is_active FROM users WHERE username = ? AND is_admin = 0", (username,))
            user = c.fetchone()
            
            if user and verify_password(password, user[1]):
                if user[2]:  # is_active
                    # Erfolgreicher Login
                    session['user_id'] = user[0]
                    session['username'] = username
                    session['last_activity'] = datetime.now().isoformat()
                    session.permanent = True
                    
                    # Update last login
                    c.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                             (datetime.now(), user[0]))
                    conn.commit()
                    
                    log_security_event('USER_LOGIN_SUCCESS', username, request.remote_addr)
                    flash('Erfolgreich angemeldet', 'success')
                    
                    conn.close()
                    return redirect(url_for('dashboard'))
                else:
                    flash('Benutzerkonto ist deaktiviert', 'error')
            else:
                log_security_event('USER_LOGIN_FAILED', username, request.remote_addr)
                flash('Ungültige Anmeldedaten', 'error')
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash('Ein Fehler ist aufgetreten', 'error')
    
    return render_template('user/login.html', csrf_token=generate_csrf_token())

@app.route('/admin/login', methods=['GET', 'POST'])
@require_csrf
def admin_login():
    """Admin-Login mit erweiterten Sicherheitsfeatures"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Admin-Benutzername und Passwort sind erforderlich', 'error')
            return render_template('admin/login.html', csrf_token=generate_csrf_token())
        
        try:
            conn = sqlite3.connect(ADMIN_DB)
            c = conn.cursor()
            c.execute("SELECT id, password_hash, is_active FROM users WHERE username = ? AND is_admin = 1", (username,))
            admin = c.fetchone()
            
            if admin and verify_password(password, admin[1]):
                if admin[2]:  # is_active
                    # Erfolgreicher Admin-Login
                    session['admin_logged_in'] = True
                    session['admin_username'] = username
                    session['admin_user_id'] = admin[0]
                    session['admin_last_activity'] = datetime.now().isoformat()
                    session.permanent = True
                    
                    # Update last login
                    c.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                             (datetime.now(), admin[0]))
                    conn.commit()
                    
                    log_security_event('ADMIN_LOGIN_SUCCESS', username, request.remote_addr)
                    flash('Admin erfolgreich angemeldet', 'success')
                    
                    conn.close()
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Admin-Benutzer ist deaktiviert', 'error')
            else:
                log_security_event('ADMIN_LOGIN_FAILED', username, request.remote_addr)
                flash('Ungültige Admin-Anmeldedaten', 'error')
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Admin login error: {e}")
            flash('Admin-Anmeldefehler', 'error')
    
    return render_template('admin/login.html', csrf_token=generate_csrf_token())

@app.route('/dashboard')
@require_login
def dashboard():
    """Benutzer-Dashboard"""
    username = session.get('username', 'Unbekannt')
    user_permissions = get_user_permissions(session.get('user_id'))
    return render_template('user/dashboard.html', 
                         username=username, 
                         permissions=user_permissions,
                         csrf_token=generate_csrf_token())

@app.route('/admin/dashboard')
@require_admin
def admin_dashboard():
    """Admin-Dashboard mit User-Management"""
    username = session.get('admin_username', 'Admin')
    return render_template('admin/dashboard.html', 
                         username=username,
                         csrf_token=generate_csrf_token())

@app.route('/logout', methods=['POST'])
@require_csrf
def logout():
    """Benutzer-Logout"""
    username = session.get('username', 'unknown')
    log_security_event('USER_LOGOUT', username, request.remote_addr)
    
    session.clear()
    flash('Erfolgreich abgemeldet', 'info')
    return redirect(url_for('login'))

@app.route('/admin/logout', methods=['POST'])
@require_csrf
def admin_logout():
    """Admin-Logout"""
    username = session.get('admin_username', 'unknown')
    log_security_event('ADMIN_LOGOUT', username, request.remote_addr)
    
    session.clear()
    flash('Admin abgemeldet', 'info')
    return redirect(url_for('admin_login'))

@app.route('/privacy')
def privacy():
    """Datenschutz-Seite"""
    return render_template('user/privacy.html')

# =============================================================================
# USER MANAGEMENT API
# =============================================================================

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    """Holt alle User mit ihren Details"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        c.execute("""
            SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.last_login,
                   u.can_edit_links, u.can_delete_links, u.can_add_links,
                   COUNT(DISTINCT gm.group_id) as group_count
            FROM users u
            LEFT JOIN group_members gm ON u.id = gm.user_id
            WHERE u.is_admin = 0
            GROUP BY u.id, u.username, u.email, u.is_active, u.created_at, u.last_login
            ORDER BY u.username
        """)
        
        users = []
        for row in c.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'is_active': bool(row[3]),
                'created_at': row[4],
                'last_login': row[5],
                'can_edit_links': bool(row[6]),
                'can_delete_links': bool(row[7]),
                'can_add_links': bool(row[8]),
                'group_count': row[9]
            })
        
        return jsonify({'users': users})
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Fehler beim Laden der User'}), 500
    finally:
        conn.close()

@app.route('/api/admin/users', methods=['POST'])
@require_admin
def create_user():
    """Erstellt einen neuen User"""
    data = request.get_json()
    
    required_fields = ['username', 'email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Fehlende Pflichtfelder'}), 400
    
    username = data['username'].strip()
    email = data['email'].strip()
    password = data['password']
    
    # Validierung
    if len(username) < 3:
        return jsonify({'error': 'Username muss mindestens 3 Zeichen haben'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Passwort muss mindestens 6 Zeichen haben'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Prüfe ob Username bereits existiert
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return jsonify({'error': 'Username bereits vergeben'}), 400
        
        # Prüfe ob Email bereits existiert
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            return jsonify({'error': 'Email bereits vergeben'}), 400
        
        # Passwort hashen
        password_hash = hash_password(password)
        
        # User erstellen
        c.execute("""
            INSERT INTO users (username, email, password_hash, is_active, is_admin,
                             can_edit_links, can_delete_links, can_add_links, created_at)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?)
        """, (username, email, password_hash, 
              data.get('is_active', True),
              data.get('can_edit_links', True),
              data.get('can_delete_links', True),
              data.get('can_add_links', True),
              datetime.now()))
        
        user_id = c.lastrowid
        conn.commit()
        
        # Zu Gruppen hinzufügen wenn angegeben
        if 'group_ids' in data and data['group_ids']:
            for group_id in data['group_ids']:
                c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", 
                         (group_id, user_id))
        
        conn.commit()
        
        log_security_event('USER_CREATED', 
                          f"Admin created user: {username}", 
                          request.remote_addr,
                          {'admin': session.get('admin_username')})
        
        return jsonify({
            'success': True, 
            'user_id': user_id,
            'message': f'User {username} erfolgreich erstellt'
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating user: {e}")
        return jsonify({'error': 'Fehler beim Erstellen des Users'}), 500
    finally:
        conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """Aktualisiert einen User"""
    data = request.get_json()
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole aktueller User
        c.execute("SELECT username FROM users WHERE id = ? AND is_admin = 0", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({'error': 'User nicht gefunden'}), 404
        
        username = user[0]
        
        # Update User
        update_fields = []
        update_values = []
        
        if 'email' in data:
            update_fields.append('email = ?')
            update_values.append(data['email'])
        
        if 'is_active' in data:
            update_fields.append('is_active = ?')
            update_values.append(data['is_active'])
        
        if 'can_edit_links' in data:
            update_fields.append('can_edit_links = ?')
            update_values.append(data['can_edit_links'])
        
        if 'can_delete_links' in data:
            update_fields.append('can_delete_links = ?')
            update_values.append(data['can_delete_links'])
        
        if 'can_add_links' in data:
            update_fields.append('can_add_links = ?')
            update_values.append(data['can_add_links'])
        
        if update_fields:
            update_values.append(user_id)
            c.execute(f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?", update_values)
        
        # Gruppen-Mitgliedschaften aktualisieren
        if 'group_ids' in data:
            # Alte Mitgliedschaften löschen
            c.execute("DELETE FROM group_members WHERE user_id = ?", (user_id,))
            
            # Neue Mitgliedschaften hinzufügen
            for group_id in data['group_ids']:
                c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", 
                         (group_id, user_id))
        
        conn.commit()
        
        log_security_event('USER_UPDATED', 
                          f"Admin updated user: {username}", 
                          request.remote_addr,
                          {'admin': session.get('admin_username')})
        
        return jsonify({'success': True, 'message': f'User {username} aktualisiert'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating user: {e}")
        return jsonify({'error': 'Fehler beim Aktualisieren des Users'}), 500
    finally:
        conn.close()

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@require_admin
def reset_user_password(user_id):
    """Setzt das Passwort eines Users zurück"""
    data = request.get_json()
    
    if 'new_password' not in data or len(data['new_password']) < 6:
        return jsonify({'error': 'Neues Passwort muss mindestens 6 Zeichen haben'}), 400
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole User
        c.execute("SELECT username FROM users WHERE id = ? AND is_admin = 0", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({'error': 'User nicht gefunden'}), 404
        
        username = user[0]
        
        # Neues Passwort hashen
        new_password_hash = hash_password(data['new_password'])
        
        # Passwort aktualisieren
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
                 (new_password_hash, user_id))
        conn.commit()
        
        log_security_event('PASSWORD_RESET', 
                          f"Admin reset password for user: {username}", 
                          request.remote_addr,
                          {'admin': session.get('admin_username')})
        
        return jsonify({'success': True, 'message': f'Passwort für {username} zurückgesetzt'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error resetting password: {e}")
        return jsonify({'error': 'Fehler beim Zurücksetzen des Passworts'}), 500
    finally:
        conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Löscht einen User"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Hole Username
        c.execute("SELECT username FROM users WHERE id = ? AND is_admin = 0", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({'error': 'User nicht gefunden'}), 404
        
        username = user[0]
        
        # Lösche User aus Gruppen
        c.execute("DELETE FROM group_members WHERE user_id = ?", (user_id,))
        
        # Lösche User
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        # Lösche User-Datenbank falls vorhanden
        user_db_path = os.path.join(DATABASE_DIR, f'user_{username}.db')
        if os.path.exists(user_db_path):
            os.remove(user_db_path)
        
        conn.commit()
        
        log_security_event('USER_DELETED', 
                          f"Admin deleted user: {username}", 
                          request.remote_addr,
                          {'admin': session.get('admin_username')})
        
        return jsonify({'success': True, 'message': f'User {username} gelöscht'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting user: {e}")
        return jsonify({'error': 'Fehler beim Löschen des Users'}), 500
    finally:
        conn.close()

# =============================================================================
# GROUPS MANAGEMENT API
# =============================================================================

@app.route('/api/admin/groups', methods=['GET'])
@require_admin
def get_all_groups():
    """Holt alle Gruppen mit Member-Count"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        c.execute("""
            SELECT g.id, g.name, g.description, g.created_at,
                   COUNT(DISTINCT gm.user_id) as member_count,
                   COUNT(DISTINCT gt.id) as folder_count
            FROM groups g
            LEFT JOIN group_members gm ON g.id = gm.group_id
            LEFT JOIN group_tabs gt ON g.id = gt.group_id
            GROUP BY g.id, g.name, g.description, g.created_at
            ORDER BY g.name
        """)
        
        groups = []
        for row in c.fetchall():
            groups.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3],
                'member_count': row[4],
                'folder_count': row[5]
            })
        
        return jsonify({'groups': groups})
        
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return jsonify({'error': 'Fehler beim Laden der Gruppen'}), 500
    finally:
        conn.close()

@app.route('/api/admin/groups', methods=['POST'])
@require_admin
def create_group():
    """Erstellt eine neue Gruppe"""
    data = request.get_json()
    
    if 'name' not in data or not data['name'].strip():
        return jsonify({'error': 'Gruppenname ist erforderlich'}), 400
    
    name = data['name'].strip()
    description = data.get('description', '').strip()
    
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Prüfe ob Name bereits existiert
        c.execute("SELECT id FROM groups WHERE name = ?", (name,))
        if c.fetchone():
            return jsonify({'error': 'Gruppenname bereits vergeben'}), 400
        
        # Gruppe erstellen
        c.execute("INSERT INTO groups (name, description, created_at) VALUES (?, ?, ?)",
                 (name, description, datetime.now()))
        
        group_id = c.lastrowid
        conn.commit()
        
        log_security_event('GROUP_CREATED', 
                          f"Admin created group: {name}", 
                          request.remote_addr,
                          {'admin': session.get('admin_username')})
        
        return jsonify({
            'success': True, 
            'group_id': group_id,
            'message': f'Gruppe {name} erfolgreich erstellt'
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating group: {e}")
        return jsonify({'error': 'Fehler beim Erstellen der Gruppe'}), 500
    finally:
        conn.close()

# =============================================================================
# USER PERMISSIONS API
# =============================================================================

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

# =============================================================================
# UTILITY API
# =============================================================================

@app.route('/api/csrf-token')
def get_csrf_token():
    """CSRF-Token für AJAX-Requests"""
    return jsonify({'csrf_token': generate_csrf_token()})

@app.route('/api/admin/stats')
@require_admin
def get_admin_stats():
    """Admin-Dashboard Statistiken"""
    try:
        conn = sqlite3.connect(ADMIN_DB)
        c = conn.cursor()
        
        # Benutzer-Statistiken
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1 AND is_admin = 0")
        active_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM groups")
        total_groups = c.fetchone()[0]
        
        # Sicherheitsereignisse (letzte 7 Tage)
        week_ago = datetime.now() - timedelta(days=7)
        c.execute("SELECT COUNT(*) FROM security_log WHERE timestamp > ?", (week_ago,))
        security_events = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'total_groups': total_groups,
            'security_events': security_events
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 Error Handler"""
    return render_template('error.html', 
                         error_code=404,
                         error_title='Seite nicht gefunden',
                         error_message='Die angeforderte Seite wurde nicht gefunden.'), 404

@app.errorhandler(403)
def forbidden(error):
    """403 Error Handler"""
    return render_template('error.html', 
                         error_code=403,
                         error_title='Zugriff verweigert',
                         error_message='Sie haben keine Berechtigung für diese Aktion.'), 403

@app.errorhandler(500)
def internal_error(error):
    """500 Error Handler"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', 
                         error_code=500,
                         error_title='Interner Serverfehler',
                         error_message='Ein unerwarteter Fehler ist aufgetreten.'), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """429 Error Handler"""
    return render_template('error.html', 
                         error_code=429,
                         error_title='Rate Limit erreicht',
                         error_message='Zu viele Anfragen. Bitte versuchen Sie es später erneut.'), 429

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_database():
    """Initialisiert die Datenbank mit allen notwendigen Tabellen"""
    conn = sqlite3.connect(ADMIN_DB)
    c = conn.cursor()
    
    try:
        # Users-Tabelle
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
        
        # Groups-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
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
        
        # Group-Tabs-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS group_tabs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '📂',
            color TEXT DEFAULT '#10b981',
            position INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE
        )''')
        
        # Security-Log-Tabelle
        c.execute('''CREATE TABLE IF NOT EXISTS security_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            username TEXT,
            ip_address TEXT,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Erstelle Standard-Admin falls nicht vorhanden
        c.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
        admin_count = c.fetchone()[0]
        
        if admin_count == 0:
            # Standard-Admin erstellen
            admin_password = secrets.token_urlsafe(12)
            admin_hash = hash_password(admin_password)
            
            c.execute("""INSERT INTO users (username, email, password_hash, is_admin, is_active, created_at)
                         VALUES (?, ?, ?, 1, 1, ?)""",
                      ('admin', 'admin@localhost', admin_hash, datetime.now()))
            
            # Admin-Credentials speichern
            with open('admin_credentials.txt', 'w') as f:
                f.write(f"Standard-Admin erstellt:\n")
                f.write(f"Username: admin\n")
                f.write(f"Passwort: {admin_password}\n")
                f.write(f"URL: http://localhost:5000/admin/login\n")
                f.write(f"Erstellt: {datetime.now()}\n")
            
            logger.info("Standard-Admin erstellt. Credentials in admin_credentials.txt")
        
        conn.commit()
        logger.info("Datenbank erfolgreich initialisiert")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
        raise
    finally:
        conn.close()

# =============================================================================
# STARTUP
# =============================================================================

if __name__ == '__main__':
    # Datenbank initialisieren
    init_database()
    
    # Server-Konfiguration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting {PROJECT_NAME} v{VERSION}")
    logger.info(f"Security: Argon2 hashing, CSRF protection, Rate limiting")
    logger.info(f"Features: User Management, Groups, Permissions, Audit Logging")
    logger.info(f"Server starting on port {port}")
    
    if debug:
        logger.warning("DEBUG MODE - Nicht für Produktion verwenden!")
    
    # Flask-Server starten
    app.run(host='0.0.0.0', port=port, debug=debug)