from django.urls import path

from . import views

app_name = 'noc'

urlpatterns = [
    path('',                    views.noc_list,     name='noc_list'),
    path('settings/',           views.noc_settings, name='noc_settings'),
    path('settings/template/<int:pk>/', views.noc_template_edit, name='noc_template_edit'),
    # Issued from the tour page, for one participant, in one language.
    path('create/<int:tour_pk>/<int:mp_pk>/', views.noc_create, name='noc_create'),
    path('<int:pk>/',           views.noc_detail,     name='noc_detail'),
    path('<int:pk>/edit/',      views.noc_edit,       name='noc_edit'),
    path('<int:pk>/regenerate/', views.noc_regenerate, name='noc_regenerate'),
    path('<int:pk>/delete/',    views.noc_delete,     name='noc_delete'),
]
