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
]
