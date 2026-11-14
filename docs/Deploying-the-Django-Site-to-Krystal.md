# Deploying the Django Site to Krystal

Oct 9, 2026 · @Maria

## Overview

The site moves from the Linux Apache test server to Krystal's cPanel hosting, keeping SQLite and Wagtail CRX, and replaces the old Joomla 3 site on the same account, in 14 steps: 5 to do now, 9 once cPanel access arrives.

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

# Wagtail: used for links in admin emails and notifications
WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "http://localhost")

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

### J1. Prepare redirects for the old Joomla URLs

Old Joomla addresses such as `/index.php/about-us` will 404 on the new site, breaking bookmarks and search results. Set up redirects now, because they are stored in `db.sqlite3` and travel to Krystal in step 5.

1. List the old URLs people actually use: main menu pages and anything linked from elsewhere.
2. In the Wagtail admin on the test server, go to **Settings → Redirects** and map each old path to its new page.

### J2. Agree a content cut-off

Tell collaborators the date after which edits should stop on the test site, so nothing is lost when `db.sqlite3` is packaged in step 5. Package on or after that date.

### 5. Package the site

From the folder that contains `mgsite`:

```bash
cd /home/me
tar --exclude="mgsite/.env" --exclude="mgsite/cache" --exclude="*/__pycache__" -czf mgsite.tar.gz mgsite
```

The virtualenv (`~/.venv`) sits outside `mgsite`, so it is left out automatically. The CRX page cache (`cache/`) is temporary and Django recreates it on Krystal. The test server's `.env` is excluded because its secret key and hosts do not belong on Krystal. Check the bundle holds `manage.py`, `db.sqlite3` and `media/`, and no `.env`:

```bash
tar -tzf mgsite.tar.gz | less
```

## Replacing the Joomla site

The old Joomla 3 site lives in `public_html` on the same Krystal account, where the Django site needs to go. Its files, its `.htaccess` rewrite rules and its own `media/` and `images/` folders would clash with steps 7 and 10, so Joomla moves out first. Joomla 3 has had no security updates since August 2023, so do not leave the old files around for long.

The plan is a one-step switch at a quiet time: the old site goes offline for the hour or two the deployment takes, and the backup is the fallback. (The alternative, deploying first on a subdomain such as `new.yourdomain.co.uk`, means deploying twice, which is more than a small site needs.)

J1 and J2 happen on the test server, so they sit in Part 1 just before step 5. J3 to J5 below happen on Krystal.

### J3. Back up the Joomla site (after step 6, before step 7)

1. In cPanel, open **Backup** (or **Backup Wizard**) and download a **home directory** backup.
2. Find Joomla's database name in `public_html/configuration.php` (the `$db` line), then download that **MySQL database** backup from the same page.
3. If Joomla has Akeeba Backup installed, download a `.jpa` backup from it as a second copy.
4. Keep all backups off the server.

### J4. Move Joomla out of public\_html (straight after J3)

1. In **File Manager**, open **Settings** and tick **Show Hidden Files**, so `.htaccess` and `.well-known` are visible.
2. Create a folder outside `public_html`, e.g. `~/joomla-old`.
3. Select everything inside `public_html` **except `.well-known`** and **Move** it to `~/joomla-old`. Include `.htaccess`.
4. Check that `public_html` now holds only `.well-known` (AutoSSL needs it to issue and renew your certificate).

Moving rather than deleting means Joomla can be put back quickly: stop the Python app, move the files back, and the old site returns. Then continue with step 7: creating the Python app writes fresh Passenger rules into `public_html/.htaccess`.

### J5. Tidy up (once the new site is settled)

- [ ] Old Joomla URLs from J1 redirect to the right new pages
- [ ] Delete `~/joomla-old` after a few weeks without problems
- [ ] Delete the Joomla database in cPanel's **MySQL Databases**, keeping the downloaded backup

Email on the domain is separate from the website and keeps working throughout.

## Part 2: Deploy on Krystal

Do these in order once you can log in to cPanel. Between steps 6 and 7, do J3 and J4 above to move the Joomla site out.

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
| `WAGTAILADMIN_BASE_URL` | `https://yourdomain.co.uk` |

Also set a **Passenger log file**, e.g. `/home/CPANELUSER/mgsite/passenger.log`, so errors are recorded. Save.

### 12. Install packages and collect static

Terminal does not see the variables from step 11. Create `~/mgsite/env.sh` in File Manager containing:

```bash
export DJANGO_SETTINGS_MODULE=mgsite.settings.prod
export DJANGO_SECRET_KEY='your-key-here'
export DJANGO_ALLOWED_HOSTS=yourdomain.co.uk,www.yourdomain.co.uk
export DJANGO_STATIC_ROOT=/home/CPANELUSER/public_html/static
export DJANGO_MEDIA_ROOT=/home/CPANELUSER/public_html/media
export WAGTAILADMIN_BASE_URL=https://yourdomain.co.uk
```

In Terminal, paste the virtualenv command from step 7, then run:

```bash
cd ~/mgsite
source env.sh
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
python manage.py update_index
python manage.py check --deploy
```

`migrate` should report nothing to do, since `db.sqlite3` is already up to date. `check --deploy` warns about HTTPS until step 14; that is expected.

### 13. Restart and test

Click **Restart** in Setup Python App, then check:

- [ ] Home page loads
- [ ] An image opens directly at `https://yourdomain.co.uk/media/images/...`
- [ ] Images show on the pages
- [ ] Wagtail admin login works and a page edit shows on the live site

### 14. Turn on HTTPS

In cPanel's **SSL/TLS Status**, confirm a certificate covers your domain; AutoSSL usually issues one automatically. Once `https://yourdomain.co.uk` loads:

1. Add `DJANGO_HTTPS` = `True` in Setup Python App.
2. Add `export DJANGO_HTTPS=True` to `env.sh`.
3. Click **Restart** and run `python manage.py check --deploy` again.

## Wagtail and CRX

The steps above work unchanged for Wagtail CRX, which deploys like any other Wagtail or Django site. Wagtail writes files while it runs, so these extra checks apply.

### Media must be writable

Wagtail saves resized images (renditions) under `MEDIA_ROOT`, in `media/images/`. After step 10, confirm your account can write to `~/public_html/media`. If uploads work but resized images fail, run:

```bash
chmod -R u+w ~/public_html/media
```

### WAGTAILADMIN\_BASE\_URL

Wagtail uses this for links in admin emails and notifications. It is included in the `prod.py` code in step 2, the variables in step 11 and `env.sh` in step 12.

### CRX page cache

CRX projects usually use wagtail-cache, which stores cached pages in a folder on disk. Check your settings for a `CACHES` block using `FileBasedCache`:

- Its `LOCATION` folder must exist and be writable on Krystal.
- Keep it inside `~/mgsite`, not `public_html`.
- If a page does not update after an edit, clear the cache in the Wagtail admin under **Settings → Cache**.

### Protected media

If you use `CRX_PROTECTED_MEDIA_ROOT` (for form uploads), leave that folder in `~/mgsite`. It must not go in `public_html`, or the files become public.

### Search index

Step 12 includes `python manage.py update_index`, which rebuilds Wagtail's search index on the server. Run it again after large content changes if search results look stale.

### Compiled CSS

If you have customised CRX's Sass files, compile them to CSS on the test server before packaging in step 5. The compiled `.css` then travels in the bundle and `collectstatic` picks it up.

### Versions

`requirements.txt` pins Wagtail, CRX and Pillow. In step 7, pick a Python version your Wagtail and CRX releases support; 3.12 is a safe choice. Pillow installs from pre-built wheels, so it should not need compiling.

## Troubleshooting

Most problems show up as one of these symptoms; `~/mgsite/passenger.log` usually names the cause.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Bad Request (400) | Address not in `DJANGO_ALLOWED_HOSTS` | Add the hostname (no `https://`) and restart |
| Server Error (500) or "Something went wrong" | Error in the app or settings | Read `passenger.log` |
| Images missing | `media` not in `public_html`, or path mismatch | Check `DJANGO_MEDIA_ROOT` matches the folder exactly |
| Original images show but resized ones fail | Wagtail cannot write renditions | `chmod -R u+w ~/public_html/media` |
| Page edits do not appear on the site | CRX page cache serving an old copy | Clear it in Wagtail admin, **Settings → Cache** |
| CSS missing | Static files not collected to `public_html` | `source env.sh`, re-run `collectstatic`, check `DJANGO_STATIC_ROOT` |
| "attempt to write a readonly database" | `mgsite` folder or `db.sqlite3` not writable | `chmod u+w ~/mgsite ~/mgsite/db.sqlite3` |
| Redirect loop | `DJANGO_HTTPS=True` before SSL works | Remove the variable until the certificate is issued |
| Commands use the wrong database or settings | `env.sh` not sourced in Terminal | Run `source env.sh` in each new Terminal session |

## Updating the site later

Upload only changed code, and never overwrite the live `db.sqlite3` if content was edited on the live site.

1. Download a copy of `~/mgsite/db.sqlite3` as a backup.
2. Upload the changed files to `~/mgsite` in File Manager.
3. In Terminal: enter the virtualenv, `cd ~/mgsite`, `source env.sh`.
4. Run `python manage.py migrate` if models changed, and `python manage.py collectstatic` if static files or compiled CSS changed.
5. Click **Restart** in Setup Python App, or run `touch ~/mgsite/tmp/restart.txt`.
6. Clear the CRX page cache in the Wagtail admin under **Settings → Cache**.
