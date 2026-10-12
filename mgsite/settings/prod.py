from .base import *  # noqa
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)

# Add your site's domain name(s) here.
ALLOWED_HOSTS = os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1"
    ).split(",")

STATIC_ROOT = os.environ.get( "DJANGO_STATIC_ROOT", STATIC_ROOT )
MEDIA_ROOT = os.environ.get( "DJANGO_MEDIA_ROOT", MEDIA_ROOT )

WAGTAILADMIN_BASE_URL = os.environ.get( "WAGTAILADMIN_BASE_URL", "http://localhost" )

# Only switch on once HTTPS works on Krystal
if os.environ.get("DJANGO_HTTPS") == "True":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# To send email from the server, we recommend django_sendmail_backend
# Or specify your own email backend such as an SMTP server.
# https://docs.djangoproject.com/en/5.2/ref/settings/#email-backend
# EMAIL_BACKEND = "django_sendmail_backend.backends.EmailBackend"

# Default email address used to send messages from the website.
DEFAULT_FROM_EMAIL = "Mother Goose Pre-School <info@mothergoosepreschool.co.uk>"

# A list of people who get error notifications.
ADMINS = [
    ("maria", "maria.keays@gmail.com"),
]

# A list in the same format as ADMINS that specifies who should get broken link
# (404) notifications when BrokenLinkEmailsMiddleware is enabled.
MANAGERS = ADMINS

# Email address used to send error messages to ADMINS.
SERVER_EMAIL = DEFAULT_FROM_EMAIL

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / "cache",  # noqa
        "KEY_PREFIX": "coderedcms",
        "TIMEOUT": 14400,  # in seconds
    }
}
