"""
Django settings for civiq_portal project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# .ENV FILE LOADER (no extra pip package needed)
# ---------------------------------------------------------------------------
# Reads a `.env` file (KEY=VALUE per line) sitting next to manage.py, if one
# exists, and loads it into the environment. This means on Termux you only
# have to type your Gmail credentials ONCE into .env — no more `export`
# commands every time you open a new terminal.
#
# On Render (or any host where you set env vars in the dashboard), this file
# won't exist and this loader simply does nothing — the platform's real
# environment variables are used instead.
import os  # noqa: E402


def _load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-THIS-BEFORE-DEPLOYING-civiq-dev-key-2026",
)

# DEBUG defaults to True for local Termux dev. On Render, set the env var
# DJANGO_DEBUG=False in the dashboard before going live.
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# Comma-separated list, e.g. "civiq.onrender.com,yourdomain.com"
_allowed_hosts_env = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()] or ["*"]

# ---------------------------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "civiq",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files in production (Render)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "civiq_portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "civiq.context_processors.footer_pages",
            ],
        },
    },
]

WSGI_APPLICATION = "civiq_portal.wsgi.application"
ASGI_APPLICATION = "civiq_portal.asgi.application"

# ---------------------------------------------------------------------------
# DATABASE (SQLite — zero setup, works fine on Termux)
# ---------------------------------------------------------------------------
# NOTE: On Render's FREE tier the filesystem is ephemeral — db.sqlite3 (and
# any uploaded photos in MEDIA_ROOT) get WIPED every time the service
# restarts or redeploys. Fine for local Termux testing / demos. For a real
# live grievance portal, use Render's free PostgreSQL add-on instead, or a
# paid plan with a persistent disk — ask me and I'll wire that up.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "civiq" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# AUTH / LOGIN REDIRECTS (officer workspace)
# ---------------------------------------------------------------------------
LOGIN_URL = "officer_login"
LOGIN_REDIRECT_URL = "officer_dashboard"
LOGOUT_REDIRECT_URL = "home"

# ---------------------------------------------------------------------------
# EMAIL (Gmail SMTP) — auto-routes grievances to the department's official
# ---------------------------------------------------------------------------
# Set these once in .env (local) or in your host's dashboard (production) —
# NEVER hardcode your real Gmail password here. Gmail requires a
# 16-character "App Password" (needs 2-Step Verification turned on):
# https://myaccount.google.com/apppasswords
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("CIVIQ_GMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("CIVIQ_GMAIL_APP_PASSWORD", "")
DEFAULT_FROM_EMAIL = f"CIVIQ Grievance Portal <{EMAIL_HOST_USER}>"

# While CIVIQ_GMAIL_USER/PASSWORD aren't set, print emails to the console
# instead of failing silently — lets you test the flow without real Gmail.
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# TERMUX FUSE flock() WORKAROUND
# ---------------------------------------------------------------------------
# /sdcard is a FUSE filesystem and doesn't support flock(), which Django's
# file storage uses when saving uploaded files (ImageField/FileField). This
# monkey-patches lock/unlock to no-ops so uploads don't crash on Termux.
# Safe to leave in even when deploying elsewhere (e.g. Render) — it's a no-op
# there too.
import django.core.files.locks as dj_locks  # noqa: E402

dj_locks.lock = lambda f, flags: True
dj_locks.unlock = lambda f: True
