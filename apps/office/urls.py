from django.urls import path
from . import views

app_name = 'office'

urlpatterns = [
    path('<int:mp_pk>/edit/', views.office_edit, name='office_edit'),
]
