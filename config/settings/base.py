import tempfile
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1').split(',')

# ── APPLICATIONS ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'django_htmx',
    # Local apps
    'apps.accounts',
    'apps.master',
    'apps.parliament',
    'apps.mp',
    'apps.ministry',
    'apps.committee',
    'apps.institution',
    'apps.travel',
    'apps.officer',
    'apps.noc',
    'apps.office',
    'apps.reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'apps.accounts.middleware.RolePermissionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.navigation_menus',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── DATABASE ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='mp_management'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# ── AUTH ──────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── INTERNATIONALISATION ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'bn'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_L10N = True
USE_TZ = True

from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('bn', _('Bengali')),
    ('en', _('English')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ── STATIC & MEDIA ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'static_collected'
# Django 5.1 removed STATICFILES_STORAGE in favour of STORAGES, so this setting
# has been silently ignored since the upgrade: collectstatic writes plain
# filenames, not content-hashed ones. Switching it on breaks collectstatic —
# the vendored CKEditor bundle points at a `ckeditor.js.map` that is not in the
# package — and a collectstatic failure stops the container from booting
# (entrypoint.sh runs it under `set -e`). So the cache is fixed at the other
# end instead: nginx serves /static/ with `Cache-Control: no-cache`, i.e. keep
# the copy but revalidate, which is a 304 on a LAN and makes a deploy visible
# immediately. Restore hashing only with a fix for that missing source map.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # noqa: F811 (ignored by Django 5.2)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── DEFAULT PK ────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── SESSIONS ──────────────────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 28800  # 8 hours

# ── CACHES ────────────────────────────────────────────────────────────────────
# `reports` holds rendered PDFs. It is file-based on purpose: gunicorn runs
# several worker processes and the default LocMemCache is private to each one,
# so a report cached by worker 1 would still cost a full render on worker 2.
# The directory lives in the system temp dir, NOT under MEDIA_ROOT — nginx
# serves /media/ straight off disk, and a cached report must not become a
# public URL. Losing it on restart is fine; it is only a cache.
REPORT_CACHE_DIR = config(
    'REPORT_CACHE_DIR',
    default=str(Path(tempfile.gettempdir()) / 'mp_report_cache'),
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'mp-default',
    },
    'reports': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': REPORT_CACHE_DIR,
        'TIMEOUT': 900,                       # 15 minutes
        'OPTIONS': {'MAX_ENTRIES': 100},      # ~700 KB each worst case
    },
}
