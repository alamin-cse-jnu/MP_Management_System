from django.urls import path
from . import views

app_name = 'travel'

urlpatterns = [
    path('',                                       views.tour_list,         name='tour_list'),
    path('create/',                                views.tour_create,       name='tour_create'),
    path('<int:pk>/',                              views.tour_detail,       name='tour_detail'),
    path('<int:pk>/edit/',                         views.tour_update,       name='tour_update'),
    path('<int:pk>/delete/',                       views.tour_delete,       name='tour_delete'),
    path('<int:pk>/participant/add/',              views.participant_add,   name='participant_add'),
    path('<int:pk>/participant/<int:ppk>/remove/', views.participant_remove, name='participant_remove'),
    path('<int:pk>/officer/add/',                  views.officer_add,       name='officer_add'),
    path('<int:pk>/officer/<int:opk>/remove/',     views.officer_remove,    name='officer_remove'),
    path('<int:pk>/country/add/',                  views.country_add,       name='country_add'),
    path('<int:pk>/country/<int:cpk>/remove/',     views.country_remove,    name='country_remove'),
]
