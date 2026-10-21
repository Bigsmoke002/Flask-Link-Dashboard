# 🚀 User-Management Installation Guide

## Quick Start

1. **Datenbank initialisieren:**
   ```bash
   python database_update.py   # optional, app.py legt die DB auch selbst an
   ```

2. **App.py ersetzen:**
   - (entfällt – app.py im Repo ist bereits die aktuelle Version)

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
