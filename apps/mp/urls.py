from django.urls import path
from . import views

app_name = 'mp'

urlpatterns = [
    # List + Create
    path('',      views.mp_list,   name='mp_list'),
    path('add/',  views.mp_create, name='mp_create'),

    # Detail (tabbed)
    path('<int:pk>/', views.mp_detail, name='mp_detail'),

    # Section saves (POST only)
    path('<int:pk>/section/general/',  views.mp_section_general,  name='mp_section_general'),
    path('<int:pk>/section/election/', views.mp_section_election, name='mp_section_election'),
    path('<int:pk>/address/<str:atype>/', views.mp_address_save,  name='mp_address_save'),

    # Spouse CRUD
    path('<int:pk>/spouse/add/',             views.spouse_create, name='spouse_create'),
    path('<int:pk>/spouse/<int:spk>/edit/',  views.spouse_update, name='spouse_update'),
    path('<int:pk>/spouse/<int:spk>/delete/',views.spouse_delete, name='spouse_delete'),

    # Children CRUD
    path('<int:pk>/child/add/',            views.child_create, name='child_create'),
    path('<int:pk>/child/<int:ck>/edit/',  views.child_update, name='child_update'),
    path('<int:pk>/child/<int:ck>/delete/',views.child_delete, name='child_delete'),

    # Education CRUD
    path('<int:pk>/education/add/',            views.education_create, name='education_create'),
    path('<int:pk>/education/<int:ek>/edit/',  views.education_update, name='education_update'),
    path('<int:pk>/education/<int:ek>/delete/',views.education_delete, name='education_delete'),

    # Foreign Language Skills CRUD
    path('<int:pk>/language/add/',            views.language_create, name='language_create'),
    path('<int:pk>/language/<int:lk>/edit/',  views.language_update, name='language_update'),
    path('<int:pk>/language/<int:lk>/delete/',views.language_delete, name='language_delete'),

    # Bank Accounts CRUD
    path('<int:pk>/bank/add/',            views.bank_create, name='bank_create'),
    path('<int:pk>/bank/<int:bk>/edit/',  views.bank_update, name='bank_update'),
    path('<int:pk>/bank/<int:bk>/delete/',views.bank_delete, name='bank_delete'),

    # COVID Vaccination CRUD
    path('<int:pk>/covid/add/',            views.covid_create, name='covid_create'),
    path('<int:pk>/covid/<int:ck>/edit/',  views.covid_update, name='covid_update'),
    path('<int:pk>/covid/<int:ck>/delete/',views.covid_delete, name='covid_delete'),

    # Parliamentary History CRUD
    path('<int:pk>/history/add/',            views.history_create, name='history_create'),
    path('<int:pk>/history/<int:hk>/edit/',  views.history_update, name='history_update'),
    path('<int:pk>/history/<int:hk>/delete/',views.history_delete, name='history_delete'),

    # Organizations CRUD
    path('<int:pk>/organization/add/',            views.organization_create, name='organization_create'),
    path('<int:pk>/organization/<int:ok>/edit/',  views.organization_update, name='organization_update'),
    path('<int:pk>/organization/<int:ok>/delete/',views.organization_delete, name='organization_delete'),

    # Awards CRUD
    path('<int:pk>/award/add/',            views.award_create, name='award_create'),
    path('<int:pk>/award/<int:ak>/edit/',  views.award_update, name='award_update'),
    path('<int:pk>/award/<int:ak>/delete/',views.award_delete, name='award_delete'),

    # Social Service (create-or-update)
    path('<int:pk>/social-service/', views.social_service_save, name='social_service_save'),

    # Special Positions CRUD
    path('<int:pk>/special-position/add/',              views.special_position_create, name='special_position_create'),
    path('<int:pk>/special-position/<int:spk>/edit/',   views.special_position_update, name='special_position_update'),
    path('<int:pk>/special-position/<int:spk>/delete/', views.special_position_delete, name='special_position_delete'),

    # Publications CRUD
    path('<int:pk>/publication/add/',               views.publication_create, name='publication_create'),
    path('<int:pk>/publication/<int:pubk>/edit/',   views.publication_update, name='publication_update'),
    path('<int:pk>/publication/<int:pubk>/delete/', views.publication_delete, name='publication_delete'),

    # Toggle active/inactive
    path('<int:pk>/toggle/', views.mp_toggle, name='mp_toggle'),
]
