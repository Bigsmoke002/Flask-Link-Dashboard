# Flask-Link-Dashboard

> ⚠️ **Archived test project**
>
> This repository was a private test and learning project (June/July 2025) and is
> provided here as an archive only. It is **not maintained** and there is **no support**.
> **No guarantee is given that anything works** – use at your own risk. Do not run it
> in production without reviewing it yourself.

## What is it?

A self-hosted link/bookmark dashboard built with **Flask** and **SQLite**, with separate
admin and user areas:

- **Admin area** (`/admin/login`): create, edit, deactivate and delete users, reset
  passwords, manage groups, view statistics
- **User area** (`/login`): personal dashboard with link collections organized in folders/tabs
- **Groups**: folders and links can be assigned at group level
- **Per-user permissions**: add / edit / delete links
- **Security**: Argon2 password hashing, CSRF protection, rate limiting,
  lockout after failed logins, security/audit log

> Note: the user interface, log messages and code comments are in **German**.

## Quick start

Requirement: Python 3.10+

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open:

- User login: <http://localhost:5000/login>
- Admin login: <http://localhost:5000/admin/login>

On first start, `databases/admin.db` is created along with a default admin account.
The credentials are written to `admin_credentials.txt` – **change the password right
away and delete that file afterwards.**

### Configuration (optional)

Via environment variables:

| Variable     | Meaning                                                      | Default   |
|--------------|--------------------------------------------------------------|-----------|
| `SECRET_KEY` | Flask session key (if unset, a new one is generated on every start, invalidating all sessions) | random |
| `PORT`       | Server port                                                  | `5000`    |
| `FLASK_ENV`  | `production` enables secure cookies/HTTPS headers, `development` enables debug mode | – |

A template is provided in `.env.example`. `app.py` does **not** load this file
automatically – set the variables yourself (e.g. `export SECRET_KEY=...`).

## Known state / limitations

Briefly tested (October 2026, Python 3.14, fresh database): startup, admin login,
creating a user, user login and the permissions API work. Everything else is untested.

- `folder_link_management.py` is only a **code fragment** (uses `app` without importing it)
  and is not wired into `app.py` – the per-group folder/link APIs are therefore incomplete.
- There are several overlapping setup/migration scripts from different development stages
  (`setup_dashboard.py`, `secure_setup.py`, `final_setup.py`, `install_user_management.py`,
  `database_update.py`, `migrate_database.py`, `cleanup.py`). They are **not** needed for a
  fresh start – `app.py` creates the database by itself.
- The setup scripts contain hard-coded **demo passwords** (e.g. `Demo123!`). These are
  examples only and must never be used in production.
- Runs on the Flask development server. Real deployment would require a WSGI server
  (gunicorn, waitress) behind a reverse proxy with HTTPS.

## License

[MIT](LICENSE)
