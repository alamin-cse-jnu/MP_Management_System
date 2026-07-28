from django.urls import path

from . import views
from .views import MASTER_SPECS, _url_name

app_name = 'master'

urlpatterns = [
    # Overview
    path('', views.master_home, name='home'),
    # Education — single-page manager (replaces the 7 separate education CRUD pages)
    path('education/', views.education_master, name='education_master'),
    path('education/<slug:key>/panel/', views.education_panel, name='education_panel'),
    path('education/<slug:key>/form/', views.education_form, name='education_form_add'),
    path('education/<slug:key>/form/<int:pk>/', views.education_form, name='education_form_edit'),
    path('education/<slug:key>/toggle/<int:pk>/', views.education_toggle, name='education_toggle'),
    # HTMX cascade endpoints
    path('htmx/district-options/', views.district_options, name='district_options'),
    path('htmx/upazila-options/', views.upazila_options, name='upazila_options'),
    path('htmx/education-level-cascade/', views.education_level_cascade, name='education_level_cascade'),
    path('htmx/subject-options/', views.subject_options, name='subject_options'),
    path('htmx/result-fields/', views.result_fields, name='result_fields'),
]

# Dynamically register CRUD URLs for every standalone master model
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

# Grouped single-page managers (Geography, Personal, Professional, Travel,
# Language) — each with its own named URLs so menu links + permission checks
# resolve just like the Education manager.
for _group in views.MASTER_GROUPS:
    _gkey = _group['key']
    _g_master, _g_panel, _g_form, _g_toggle = views.get_group_views(_gkey)
    urlpatterns += [
        path(f'{_gkey}/',                            _g_master, name=f'{_gkey}_master'),
        path(f'{_gkey}/<slug:key>/panel/',           _g_panel,  name=f'{_gkey}_panel'),
        path(f'{_gkey}/<slug:key>/form/',            _g_form,   name=f'{_gkey}_form_add'),
        path(f'{_gkey}/<slug:key>/form/<int:pk>/',   _g_form,   name=f'{_gkey}_form_edit'),
        path(f'{_gkey}/<slug:key>/toggle/<int:pk>/', _g_toggle, name=f'{_gkey}_toggle'),
    ]
