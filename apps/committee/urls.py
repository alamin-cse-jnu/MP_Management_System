from django.urls import path
from . import views

app_name = 'committee'

urlpatterns = [
    path('',                              views.assignment_list,   name='assignment_list'),
    path('create/',                       views.assignment_create, name='assignment_create'),
    path('create/positions/',             views.assign_positions,  name='assign_positions'),
    path('htmx/sub-committees/',          views.subcommittee_options, name='subcommittee_options'),
    path('htmx/member-picker/',           views.member_picker,        name='member_picker'),
    path('<int:pk>/edit/',                views.assignment_update, name='assignment_update'),
    path('<int:pk>/delete/',              views.assignment_delete, name='assignment_delete'),
    path('<int:pk>/toggle/',              views.assignment_toggle, name='assignment_toggle'),
]
