from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',                        views.index,                  name='index'),
    path('all-mp/',                 views.all_mp,                 name='all_mp'),
    path('women-mp/',               views.women_mp,               name='women_mp'),
    path('party-wise/',             views.party_wise,             name='party_wise'),
    path('district-wise/',          views.district_wise,          name='district_wise'),
    path('qualification-wise/',     views.qualification_wise,     name='qualification_wise'),
    path('cabinet/',                views.cabinet,                name='cabinet'),
    path('committee-members/',      views.committee_members,      name='committee_members'),
    path('mp-committee-summary/',   views.mp_committee_summary,   name='mp_committee_summary'),
    path('institution-assignments/',views.institution_assignments,name='institution_assignments'),
    path('foreign-tours/',          views.foreign_tours,          name='foreign_tours'),
    path('mp-biodata/',             views.mp_biodata,             name='mp_biodata'),
    path('contact-list/',           views.contact_list,           name='contact_list'),
    path('custom-report/',           views.custom_report,          name='custom_report'),
    path('family-report/',           views.family_report,          name='family_report'),
    path('audit-log/',              views.audit_log_list,         name='audit_log_list'),
    path('audit-log/<int:pk>/',     views.audit_log_detail,       name='audit_log_detail'),
    path('pa-ps-list/',             views.pa_ps_list,             name='pa_ps_list'),
]
