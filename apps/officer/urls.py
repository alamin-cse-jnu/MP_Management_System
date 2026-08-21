from django.urls import path

from . import views

app_name = 'officer'

urlpatterns = [
    path('',      views.officer_list,     name='officer_list'),
    path('sync/', views.officer_sync_run, name='officer_sync_run'),
]
