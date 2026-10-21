# Flask-Link-Dashboard

> ⚠️ **Archiviertes Testprojekt**
>
> Dieses Repository war ein privates Test- und Lernprojekt (Juni/Juli 2025) und wird
> hier nur noch als Archiv bereitgestellt. Es wird **nicht weiterentwickelt** und es gibt
> **keinen Support**. Eine Funktion kann **nicht garantiert** werden – Nutzung auf
> eigene Gefahr. Nicht ohne eigene Prüfung produktiv einsetzen.
>
> *Archived test project. No maintenance, no support, no guarantee that anything works.
> Use at your own risk.*

## Was ist das?

Ein selbst gehostetes Link-/Lesezeichen-Dashboard auf Basis von **Flask** und **SQLite**
mit getrenntem Admin- und User-Bereich:

- **Admin-Bereich** (`/admin/login`): User anlegen, bearbeiten, deaktivieren, löschen,
  Passwörter zurücksetzen, Gruppen verwalten, Statistiken
- **User-Bereich** (`/login`): persönliches Dashboard mit Link-Sammlungen in Ordnern/Reitern
- **Gruppen**: Ordner und Links können auf Gruppenebene zugewiesen werden
- **Berechtigungen** pro User: Links hinzufügen / bearbeiten / löschen
- **Sicherheit**: Argon2-Passwort-Hashing, CSRF-Schutz, Rate-Limiting,
  Login-Sperre nach Fehlversuchen, Security-/Audit-Log

## Schnellstart

Voraussetzung: Python 3.10+

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Danach:

- User-Login: <http://localhost:5000/login>
- Admin-Login: <http://localhost:5000/admin/login>

Beim ersten Start wird `databases/admin.db` angelegt und ein Standard-Admin erzeugt.
Die Zugangsdaten stehen in `admin_credentials.txt` – **Passwort sofort ändern und die
Datei danach löschen.**

### Konfiguration (optional)

Über Umgebungsvariablen:

| Variable     | Bedeutung                                                   | Standard        |
|--------------|-------------------------------------------------------------|-----------------|
| `SECRET_KEY` | Flask-Session-Schlüssel (ohne Angabe bei jedem Start neu → alle Sessions ungültig) | zufällig |
| `PORT`       | Port des Servers                                            | `5000`          |
| `FLASK_ENV`  | `production` aktiviert Secure-Cookies/HTTPS-Header, `development` den Debug-Modus | – |

Eine Vorlage liegt in `.env.example`. `app.py` lädt diese Datei **nicht** automatisch –
die Variablen müssen selbst gesetzt werden (z. B. `export SECRET_KEY=...`).

## Bekannter Stand / Einschränkungen

Kurz getestet (Oktober 2026, Python 3.14, frische Datenbank): Start, Admin-Login,
User anlegen, User-Login und Berechtigungs-API funktionieren. Alles andere ist ungetestet.

- `folder_link_management.py` ist nur ein **Code-Fragment** (nutzt `app` ohne Import) und
  ist nicht in `app.py` eingebunden – die Ordner-/Link-APIs pro Gruppe sind daher unvollständig.
- Es gibt mehrere sich überschneidende Setup-/Migrationsskripte aus verschiedenen
  Entwicklungsständen (`setup_dashboard.py`, `secure_setup.py`, `final_setup.py`,
  `install_user_management.py`, `database_update.py`, `migrate_database.py`, `cleanup.py`).
  Für einen frischen Start werden sie **nicht** benötigt – `app.py` legt die Datenbank selbst an.
- Die Setup-Skripte enthalten feste **Demo-Passwörter** (z. B. `Demo123!`). Diese sind nur
  Beispiele und dürfen niemals produktiv verwendet werden.
- Läuft mit dem Flask-Entwicklungsserver. Für echten Betrieb wäre ein WSGI-Server
  (gunicorn, waitress) plus Reverse-Proxy mit HTTPS nötig.

## Lizenz

[MIT](LICENSE)
