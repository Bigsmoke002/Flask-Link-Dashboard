# 🚀 User Management Installation Guide

> See [README.md](README.md) first – this is an archived test project, no guarantee that anything works.

## Quick Start

1. **Initialize the database (optional):**
   ```bash
   python database_update.py   # optional, app.py also creates the database by itself
   ```

2. **Start the server:**
   ```bash
   python app.py
   ```

3. **Open the admin dashboard:**
   - URL: http://localhost:5000/admin/login
   - Credentials: see `admin_credentials.txt` (created on first start)

## What is included?

✅ **User management:**
- Create/edit/delete users
- Reset passwords
- Assign permissions

✅ **Group system:**
- Create and manage groups
- Assign users to groups
- Folders/links at group level

✅ **Security:**
- Argon2 password hashing
- Rate limiting
- CSRF protection
- Audit logging

✅ **API endpoints:**
- `/api/admin/users` – user management
- `/api/admin/groups` – group management
- `/api/user/permissions` – permissions

## Next steps

1. Log in as admin
2. Create your first users
3. Create groups and assign users
4. Configure permissions

## Files

- Logs: `logs/dashboard.log`
- Credentials: `admin_credentials.txt`
