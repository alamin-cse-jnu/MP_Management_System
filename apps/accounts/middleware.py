from django.http import HttpResponseForbidden
from django.urls import resolve


class RolePermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not getattr(request.user, 'is_superadmin', False):
            try:
                from apps.accounts.models import SubMenu, RolePermission
                # view_name includes namespace e.g. "master:division_list"
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
