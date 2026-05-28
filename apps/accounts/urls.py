from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('login/',    views.login_view,  name='login'),
    path('logout/',   views.logout_view, name='logout'),
    path('',          views.dashboard,   name='dashboard'),
    path('set-language/', views.set_language, name='set_language'),
    path('search/',       views.mp_search,    name='mp_search'),

    # Roles
    path('roles/',                      views.role_list,        name='role_list'),
    path('roles/add/',                  views.role_create,      name='role_create'),
    path('roles/<int:pk>/edit/',        views.role_update,      name='role_update'),
    path('roles/<int:pk>/toggle/',      views.role_toggle,      name='role_toggle'),
    path('roles/<int:pk>/permissions/', views.role_permissions, name='role_permissions'),

    # Users
    path('users/',                 views.user_list,   name='user_list'),
    path('users/add/',             views.user_create, name='user_create'),
    path('users/<int:pk>/edit/',   views.user_update, name='user_update'),
    path('users/<int:pk>/toggle/', views.user_toggle, name='user_toggle'),

    # Menus
    path('menus/',                    views.menu_list,   name='menu_list'),
    path('menus/add/',                views.menu_create, name='menu_create'),
    path('menus/<int:pk>/edit/',      views.menu_update, name='menu_update'),
    path('menus/<int:pk>/toggle/',    views.menu_toggle, name='menu_toggle'),

    # SubMenus
    path('submenus/add/',              views.submenu_create, name='submenu_create'),
    path('submenus/<int:pk>/edit/',    views.submenu_update, name='submenu_update'),
    path('submenus/<int:pk>/toggle/',  views.submenu_toggle, name='submenu_toggle'),
]
