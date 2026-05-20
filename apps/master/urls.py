from django.urls import path

from . import views
from .views import MASTER_SPECS, _url_name

app_name = 'master'

urlpatterns = [
    # Overview
    path('', views.master_home, name='home'),
    # HTMX cascade endpoints
    path('htmx/district-options/', views.district_options, name='district_options'),
    path('htmx/upazila-options/', views.upazila_options, name='upazila_options'),
]

# Dynamically register CRUD URLs for every master model
for _spec in MASTER_SPECS:
    _key = _spec['key']
    _list_view, _create_view, _update_view, _toggle_view = views.get_views(_key)
    _id = _key.replace('-', '_')   # URL-safe Python identifier for names

    urlpatterns += [
        path(f'{_key}/',           _list_view,   name=f'{_id}_list'),
        path(f'{_key}/add/',       _create_view, name=f'{_id}_create'),
        path(f'{_key}/<int:pk>/edit/',   _update_view, name=f'{_id}_update'),
        path(f'{_key}/<int:pk>/toggle/', _toggle_view, name=f'{_id}_toggle'),
    ]
