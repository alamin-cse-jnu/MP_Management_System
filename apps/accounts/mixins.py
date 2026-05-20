from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.conf import settings


class PermissionMixin:
    """
    CBV mixin for role-based permission checks.
    Superadmin bypasses all checks.
    Detects required action from URL name suffix:
      _list / _home → view
      _create / _add → add
      _update / _edit → edit
      _toggle / _delete / _deactivate → delete
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        if getattr(request.user, 'is_superadmin', False):
            return super().dispatch(request, *args, **kwargs)

        try:
            from django.urls import resolve
            from apps.accounts.models import SubMenu, RolePermission
            view_name = resolve(request.path).view_name
            submenu = SubMenu.objects.filter(url_name=view_name, is_active=True).first()

            if submenu and request.user.role:
                perm = RolePermission.objects.filter(
                    role=request.user.role, submenu=submenu
                ).first()
                action = self._detect_action(view_name, request.method)
                if not perm or not getattr(perm, f'can_{action}', False):
                    raise PermissionDenied
        except PermissionDenied:
            raise
        except Exception:
            pass   # fail-open: if lookup fails, allow access

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _detect_action(view_name, method):
        if method == 'GET':
            return 'view'
        name = view_name.split(':')[-1]   # strip namespace
        if '_create' in name or name.endswith('_add'):
            return 'add'
        if '_update' in name or name.endswith('_edit'):
            return 'edit'
        if '_toggle' in name or '_delete' in name or '_deactivate' in name:
            return 'delete'
        return 'view'
