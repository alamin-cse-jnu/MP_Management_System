from .base import *
from decouple import config

DEBUG = False

# Always-on hardening (safe over HTTP)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ── TLS-dependent hardening ──────────────────────────────────────────────────
# OFF by default so login works over plain HTTP on the internal IP.
# When you add HTTPS (cert + domain), set USE_TLS=True in the server .env to
# turn on secure cookies, HSTS and the HTTP→HTTPS redirect — no code change.
USE_TLS = config('USE_TLS', default=False, cast=bool)

SESSION_COOKIE_SECURE = USE_TLS
CSRF_COOKIE_SECURE = USE_TLS
SECURE_SSL_REDIRECT = USE_TLS
SECURE_HSTS_SECONDS = 31536000 if USE_TLS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_TLS
SECURE_HSTS_PRELOAD = USE_TLS

# Behind the nginx reverse proxy: trust X-Forwarded-Proto so Django knows the
# original scheme (relevant once TLS is terminated at nginx).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Hosts/origins allowed to submit forms. Comma-separated in the .env, e.g.
# CSRF_TRUSTED_ORIGINS=http://172.16.220.158,https://mp.example.gov.bd
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in config(
        'CSRF_TRUSTED_ORIGINS',
        default='http://172.16.220.158',
    ).split(',') if o.strip()
]
