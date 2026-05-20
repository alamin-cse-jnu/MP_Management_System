def navigation_menus(request):
    if not request.user.is_authenticated:
        return {'menus': []}
    try:
        from apps.accounts.models import Menu
        menus = Menu.objects.filter(is_active=True).prefetch_related('submenus')
        return {'menus': menus}
    except Exception:
        return {'menus': []}
