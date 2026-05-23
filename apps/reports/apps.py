from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports'
    label = 'reports'

    def ready(self):
        from apps.reports.audit import connect_signals
        connect_signals()
