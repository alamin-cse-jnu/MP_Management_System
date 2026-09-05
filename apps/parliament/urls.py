from django.urls import path
from . import views

app_name = 'parliament'

urlpatterns = [
    # Parliament
    path('',                          views.parliament_list,     name='parliament_list'),
    path('add/',                      views.parliament_create,   name='parliament_create'),
    path('<int:pk>/edit/',            views.parliament_update,   name='parliament_update'),
    path('<int:pk>/activate/',        views.parliament_activate, name='parliament_activate'),

    # Constituency
    path('constituency/',             views.constituency_list,   name='constituency_list'),
    path('constituency/add/',         views.constituency_create, name='constituency_create'),
    path('constituency/<int:pk>/edit/',   views.constituency_update, name='constituency_update'),
    path('constituency/<int:pk>/toggle/', views.constituency_toggle, name='constituency_toggle'),

    # Parliamentary positions (Speaker / Deputy Speaker / Chief Whip / Whip / …)
    path('positions/',                 views.position_list,   name='position_list'),
    path('positions/add/',             views.position_create, name='position_create'),
    path('positions/<int:pk>/edit/',   views.position_update, name='position_update'),
    path('positions/<int:pk>/toggle/', views.position_toggle, name='position_toggle'),
    path('positions/<int:pk>/delete/', views.position_delete, name='position_delete'),
]
