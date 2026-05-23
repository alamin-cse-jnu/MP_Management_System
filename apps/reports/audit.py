"""
Audit signal handlers for CREATE / UPDATE / DELETE tracking.

Uses thread-local request storage (set by RolePermissionMiddleware) to
capture the current user and IP address without passing request through
the ORM layer.
"""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from apps.accounts.middleware import get_client_ip, get_current_user

# ── Models to audit ───────────────────────────────────────────────────────────
# Import lazily inside connect_signals() to avoid circular imports at startup.

AUDITED_MODELS = [
    ('apps.mp',          'MP'),
    ('apps.mp',          'ElectionInfo'),
    ('apps.mp',          'Spouse'),
    ('apps.mp',          'Child'),
    ('apps.mp',          'Education'),
    ('apps.mp',          'Address'),
    ('apps.mp',          'ForeignLanguageSkill'),
    ('apps.mp',          'BankAccount'),
    ('apps.mp',          'CovidVaccination'),
    ('apps.mp',          'PreviousParliamentaryHistory'),
    ('apps.mp',          'Organization'),
    ('apps.mp',          'Award'),
    ('apps.mp',          'SocialService'),
    ('apps.mp',          'SpecialPositionHistory'),
    ('apps.mp',          'Publication'),
    ('apps.ministry',    'MinistryAssignment'),
    ('apps.committee',   'CommitteeAssignment'),
    ('apps.institution', 'InstitutionAssignment'),
    ('apps.travel',      'ForeignTour'),
    ('apps.travel',      'ForeignTourParticipant'),
    ('apps.office',      'ParliamentOfficeAddress'),
    ('apps.parliament',  'Parliament'),
    ('apps.parliament',  'Constituency'),
    ('apps.accounts',    'CustomUser'),
    ('apps.accounts',    'Role'),
]

# Fields to skip when comparing (binary, large text, auto fields)
_SKIP_FIELDS = {'photo', 'password', '_state'}


def _safe_repr(instance):
    try:
        return str(instance)[:300]
    except Exception:
        return ''


def _get_field_values(instance):
    """Return a flat dict of serialisable field values."""
    try:
        data = model_to_dict(instance)
    except Exception:
        data = {}
    # Also capture direct CharField/DateField values not in model_to_dict
    for field in instance._meta.get_fields():
        fname = getattr(field, 'name', None)
        if fname and fname not in data and fname not in _SKIP_FIELDS:
            try:
                data[fname] = getattr(instance, fname)
            except Exception:
                pass
    return {k: str(v) if v is not None else '' for k, v in data.items()
            if k not in _SKIP_FIELDS}


def _compute_changes(old_data, new_data):
    changes = {}
    all_keys = set(old_data) | set(new_data)
    for key in all_keys:
        old_val = old_data.get(key, '')
        new_val = new_data.get(key, '')
        if old_val != new_val:
            changes[key] = [old_val, new_val]
    return changes


def _write_log(sender, instance, action, changes=None):
    from .models import AuditLog
    try:
        AuditLog.objects.create(
            user=get_current_user(),
            app_label=sender._meta.app_label,
            model_name=sender._meta.model_name,
            object_id=str(instance.pk),
            object_repr=_safe_repr(instance),
            action=action,
            changes=changes or {},
            ip_address=get_client_ip(),
        )
    except Exception:
        pass  # never let audit failure break the main operation


# ── Generic pre-save: snapshot old state ─────────────────────────────────────

def _pre_save_handler(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._audit_old = _get_field_values(old)
        except sender.DoesNotExist:
            instance._audit_old = None
    else:
        instance._audit_old = None


# ── Generic post-save: compare and log ───────────────────────────────────────

def _post_save_handler(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    changes = {}
    if not created:
        old_data = getattr(instance, '_audit_old', None) or {}
        new_data = _get_field_values(instance)
        changes = _compute_changes(old_data, new_data)
        if not changes:
            return  # nothing changed — skip the log entry
    _write_log(sender, instance, action, changes)


# ── Generic post-delete: log deletion ────────────────────────────────────────

def _post_delete_handler(sender, instance, **kwargs):
    _write_log(sender, instance, 'DELETE', {})


# ── Connect signals for all audited models ────────────────────────────────────

def connect_signals():
    from django.apps import apps
    for app_label_dotted, model_name in AUDITED_MODELS:
        # app_label_dotted is like 'apps.mp' — the actual app_label is 'mp'
        actual_label = app_label_dotted.split('.')[-1]
        try:
            model = apps.get_model(actual_label, model_name)
        except LookupError:
            continue

        pre_save.connect(_pre_save_handler,   sender=model, weak=False)
        post_save.connect(_post_save_handler,  sender=model, weak=False)
        post_delete.connect(_post_delete_handler, sender=model, weak=False)
