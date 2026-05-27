import functools

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


# ── SHARED HELPERS ────────────────────────────────────────────────────────────

def _detect_action(view_name):
    name = view_name.split(':')[-1]   # strip namespace
    if '_create' in name or name.endswith('_add'):
        return 'add'
    if '_update' in name or '_edit' in name or '_activate' in name:
        return 'edit'
    if '_toggle' in name or '_delete' in name or '_deactivate' in name:
        return 'delete'
    return 'view'


def _find_submenu(view_name, action):
    from apps.accounts.models import SubMenu
    submenu = SubMenu.objects.filter(url_name=view_name, is_active=True).first()
    if submenu:
        return submenu
    # For action URLs, derive the parent _list submenu
    # e.g. master:division_create → master:division_list
    if action != 'view':
        parts = view_name.rsplit(':', 1)
        namespace = parts[0] + ':' if len(parts) > 1 else ''
        name = parts[-1]
        for suffix in ('_create', '_add', '_update', '_edit', '_activate',
                       '_toggle', '_delete', '_deactivate'):
            if name.endswith(suffix):
                list_name = namespace + name[:-len(suffix)] + '_list'
                return SubMenu.objects.filter(url_name=list_name, is_active=True).first()
    return None


def _run_permission_check(request, view_name):
    """Raises PermissionDenied if the user lacks the required permission."""
    if getattr(request.user, 'is_superadmin', False):
        return
    action = _detect_action(view_name)
    submenu = _find_submenu(view_name, action)
    if submenu:
        if not request.user.role:
            raise PermissionDenied
        from apps.accounts.models import RolePermission
        perm = RolePermission.objects.filter(
            role=request.user.role, submenu=submenu
        ).first()
        if not perm or not getattr(perm, f'can_{action}', False):
            raise PermissionDenied


# ── CBV MIXIN ─────────────────────────────────────────────────────────────────

class PermissionMixin:
    """
    CBV mixin for role-based permission checks.
    Superadmin bypasses all checks.

    SubMenu records only store the _list URL name for each module.
    Action URLs (create/update/toggle/activate) are resolved back to their
    parent _list submenu, then the appropriate permission flag is checked:
      _list / _home          → can_view
      _create / _add         → can_add
      _update / _edit /
        _activate            → can_edit
      _toggle / _delete /
        _deactivate          → can_delete
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        from django.urls import resolve
        view_name = resolve(request.path).view_name
        _run_permission_check(request, view_name)

        return super().dispatch(request, *args, **kwargs)


# ── FBV DECORATOR ─────────────────────────────────────────────────────────────

def perm_required(view_func):
    """
    Decorator for function-based views.
    Enforces login + role permission check (replaces @login_required).
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        from django.urls import resolve
        view_name = resolve(request.path).view_name
        _run_permission_check(request, view_name)
        return view_func(request, *args, **kwargs)
    return wrapper
