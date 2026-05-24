from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "=%ra$l!@r3=x14qmp&y&4z677boe93ajw#pgtnyi8f)i0*oto_"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [  # noqa
    "django_sass",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

WAGTAIL_CACHE = False

try:
    from .local import *  # noqa
except ImportError:
    pass
