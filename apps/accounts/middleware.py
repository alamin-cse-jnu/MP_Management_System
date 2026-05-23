import threading

from django.http import HttpResponseForbidden
from django.urls import resolve

_thread_locals = threading.local()


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    request = get_current_request()
    if request and request.user.is_authenticated:
        return request.user
    return None


def get_client_ip(request=None):
    if request is None:
        request = get_current_request()
    if request is None:
        return None
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            if request.user.is_authenticated and not getattr(request.user, 'is_superadmin', False):
                try:
                    from apps.accounts.models import SubMenu, RolePermission
                    view_name = resolve(request.path).view_name
                    submenu = SubMenu.objects.filter(url_name=view_name, is_active=True).first()
                    if submenu and request.user.role:
                        perm = RolePermission.objects.filter(
                            role=request.user.role, submenu=submenu
                        ).first()
                        if not perm or not perm.can_view:
                            return HttpResponseForbidden(
                                '<h3>অ্যাক্সেস অস্বীকৃত</h3><p>এই পাতায় প্রবেশের অনুমতি নেই।</p>'
                            )
                except Exception:
                    pass
            return self.get_response(request)
        finally:
            _thread_locals.request = None
