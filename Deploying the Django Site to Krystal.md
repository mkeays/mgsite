# Deploying the Django Site to Krystal

Oct 9, 2026 · @Maria

## Overview

The site moves from the Linux Apache test server to Krystal's cPanel hosting, keeping SQLite, in 14 steps: 5 to do now, 9 once cPanel access arrives.

Assumptions used throughout (replace with your real names):

- Project folder: `mgsite`, containing `manage.py` and `db.sqlite3`
- Project package: `mgsite`, with settings in `mgsite/settings/base.py`, `dev.py` and `prod.py`
- `MEDIA_ROOT` and `MEDIA_URL` are defined in `base.py`; images live in `media/images`
- `CPANELUSER` = your Krystal cPanel username; your home folder is `/home/CPANELUSER`
- `yourdomain.co.uk` = the live domain

On Krystal, `public_html` does the job the Apache `Alias` lines do on the test server: anything inside it is served directly. Krystal support only covers getting a basic Python demo app running, not your Django setup.

## Part 1: Prepare on the test server

These steps can all be done now, before cPanel access.

### 1. Note your versions

In your virtualenv, record the Python and Django versions and save your packages. Krystal offers Python up to 3.13; pick the closest match later.

```bash
python --version
python -m django --version
pip freeze > requirements.txt
```

Keep `requirements.txt` in the project root, next to `manage.py`.

### 2. Make prod.py work on both servers

The test server and Krystal need different hosts and file paths, so environment variables override them. The defaults suit the test server. Replace the relevant parts of `prod.py` with:

```python
import os
from .base import *

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"   # your test hosts
).split(",")

# Krystal points these into public_html; the test server keeps base.py values
STATIC_ROOT = os.environ.get("DJANGO_STATIC_ROOT", STATIC_ROOT)
MEDIA_ROOT = os.environ.get("DJANGO_MEDIA_ROOT", MEDIA_ROOT)

# Only switch on once HTTPS works on Krystal
if os.environ.get("DJANGO_HTTPS") == "True":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

Put your test server's hostnames in the `ALLOWED_HOSTS` default. Reload Apache and check the test site still works, images included.

### 3. Confirm wsgi.py defaults to prod

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mgsite.settings.prod")
```

Leave `manage.py` defaulting to dev, so local commands keep working.

### 4. Generate a secret key for the live site

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Store it somewhere safe, not in Git. You will paste it into cPanel in step 11.

### 5. Package the site

From the folder above `mgsite`:

```bash
tar --exclude="mgsite/venv" --exclude="*/__pycache__" -czf mgsite.tar.gz mgsite
```

Use your virtualenv's real folder name, or drop that exclude if it lives elsewhere. Check the bundle holds `manage.py`, `db.sqlite3` and `media/`:

```bash
tar -tzf mgsite.tar.gz | less
```

## Part 2: Deploy on Krystal

Do these in order once you can log in to cPanel.

### 6. Check the basics

Log in to cPanel and note your cPanel username. Confirm you can see **Terminal** (under Advanced) and **Setup Python App** (under Software). Make sure your domain is set up on the account and points to Krystal.

### 7. Create the Python app

Go to **Software → Setup Python App → Create Application** and set:

- **Python version:** closest to your test server's
- **Application root:** `mgsite`
- **Application URL:** your domain, path left blank
- **Startup file and entry point:** blank

Click **Create**, then copy the "enter the virtual environment" command shown at the top of the page.

### 8. Upload and extract

In **File Manager**, go to your home folder (not `public_html`). Upload `mgsite.tar.gz`, right-click it and choose **Extract**. It merges into the `mgsite` folder cPanel created; keep cPanel's `passenger_wsgi.py`. Check `/home/CPANELUSER/mgsite/manage.py` exists.

### 9. Point Passenger at Django

Edit `mgsite/passenger_wsgi.py` in File Manager and replace its contents with:

```python
from mgsite.wsgi import application
```

### 10. Move media into public\_html

This replaces the Apache `Alias /media/` block. In **Terminal**:

```bash
mv ~/mgsite/media ~/public_html/media
```

### 11. Set environment variables

In **Setup Python App**, edit your app and add these variables:

| Variable | Value |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `mgsite.settings.prod` |
| `DJANGO_SECRET_KEY` | the key from step 4 |
| `DJANGO_ALLOWED_HOSTS` | `yourdomain.co.uk,www.yourdomain.co.uk` |
| `DJANGO_STATIC_ROOT` | `/home/CPANELUSER/public_html/static` |
| `DJANGO_MEDIA_ROOT` | `/home/CPANELUSER/public_html/media` |

Also set a **Passenger log file**, e.g. `/home/CPANELUSER/mgsite/passenger.log`, so errors are recorded. Save.

### 12. Install packages and collect static

Terminal does not see the variables from step 11. Create `~/mgsite/env.sh` in File Manager containing:

```bash
export DJANGO_SETTINGS_MODULE=mgsite.settings.prod
export DJANGO_SECRET_KEY='your-key-here'
export DJANGO_ALLOWED_HOSTS=yourdomain.co.uk,www.yourdomain.co.uk
export DJANGO_STATIC_ROOT=/home/CPANELUSER/public_html/static
export DJANGO_MEDIA_ROOT=/home/CPANELUSER/public_html/media
```

In Terminal, paste the virtualenv command from step 7, then run:

```bash
cd ~/mgsite
source env.sh
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
python manage.py check --deploy
```

`migrate` should report nothing to do, since `db.sqlite3` is already up to date. `check --deploy` warns about HTTPS until step 14; that is expected.

### 13. Restart and test

Click **Restart** in Setup Python App, then check:

- [ ] Home page loads
- [ ] An image opens directly at `https://yourdomain.co.uk/media/images/...`
- [ ] Images show on the pages
- [ ] Admin login works

### 14. Turn on HTTPS

In cPanel's **SSL/TLS Status**, confirm a certificate covers your domain; AutoSSL usually issues one automatically. Once `https://yourdomain.co.uk` loads:

1. Add `DJANGO_HTTPS` = `True` in Setup Python App.
2. Add `export DJANGO_HTTPS=True` to `env.sh`.
3. Click **Restart** and run `python manage.py check --deploy` again.

## Troubleshooting

Most problems show up as one of these symptoms; `~/mgsite/passenger.log` usually names the cause.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Bad Request (400) | Address not in `DJANGO_ALLOWED_HOSTS` | Add the hostname (no `https://`) and restart |
| Server Error (500) or "Something went wrong" | Error in the app or settings | Read `passenger.log` |
| Images missing | `media` not in `public_html`, or path mismatch | Check `DJANGO_MEDIA_ROOT` matches the folder exactly |
| CSS missing | Static files not collected to `public_html` | `source env.sh`, re-run `collectstatic`, check `DJANGO_STATIC_ROOT` |
| "attempt to write a readonly database" | `mgsite` folder or `db.sqlite3` not writable | `chmod u+w ~/mgsite ~/mgsite/db.sqlite3` |
| Redirect loop | `DJANGO_HTTPS=True` before SSL works | Remove the variable until the certificate is issued |
| Commands use the wrong database or settings | `env.sh` not sourced in Terminal | Run `source env.sh` in each new Terminal session |

## Updating the site later

Upload only changed code, and never overwrite the live `db.sqlite3` if content was edited on the live site.

1. Download a copy of `~/mgsite/db.sqlite3` as a backup.
2. Upload the changed files to `~/mgsite` in File Manager.
3. In Terminal: enter the virtualenv, `cd ~/mgsite`, `source env.sh`.
4. Run `python manage.py migrate` if models changed, and `python manage.py collectstatic` if static files changed.
5. Click **Restart** in Setup Python App, or run `touch ~/mgsite/tmp/restart.txt`.
