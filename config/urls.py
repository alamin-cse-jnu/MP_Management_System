from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('', include('apps.accounts.urls', namespace='accounts')),
    path('master/', include('apps.master.urls', namespace='master')),
    path('parliament/', include('apps.parliament.urls', namespace='parliament')),
    path('mp/', include('apps.mp.urls', namespace='mp')),
    path('ministry/', include('apps.ministry.urls', namespace='ministry')),
    path('committee/', include('apps.committee.urls', namespace='committee')),
    path('institution/', include('apps.institution.urls', namespace='institution')),
    path('travel/', include('apps.travel.urls', namespace='travel')),
    path('office/', include('apps.office.urls', namespace='office')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
