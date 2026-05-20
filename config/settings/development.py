from .base import *

DEBUG = True

INSTALLED_APPS += ['django.contrib.admin']  # Only for dev shell convenience; no admin UI exposed

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relaxed password validation in development
AUTH_PASSWORD_VALIDATORS = []

# Show all SQL queries in development (optional — uncomment to enable)
# LOGGING = {
#     'version': 1,
#     'handlers': {'console': {'class': 'logging.StreamHandler'}},
#     'loggers': {'django.db.backends': {'handlers': ['console'], 'level': 'DEBUG'}},
# }
