from django.conf import settings
from django.db import models

from apps.master.models import Country, TravelPurpose, TravelType
from apps.mp.models import MP
from apps.parliament.models import Parliament


class ForeignTour(models.Model):
    go_number         = models.CharField(max_length=200)
    go_date           = models.DateField()
    parliament        = models.ForeignKey(Parliament, on_delete=models.PROTECT, related_name='foreign_tours')
    tour_type         = models.ForeignKey(TravelType, on_delete=models.PROTECT, related_name='tours')
    purpose           = models.ForeignKey(TravelPurpose, on_delete=models.PROTECT, related_name='tours')
    purpose_detail_bn = models.TextField(blank=True)
    purpose_detail_en = models.TextField(blank=True)
    created_by        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='created_tours')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-go_date']

    def __str__(self):
        return f"{self.go_number} ({self.go_date})"


class ForeignTourParticipant(models.Model):
    tour           = models.ForeignKey(ForeignTour, on_delete=models.CASCADE, related_name='participants')
    mp             = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='travel_participations')
    departure_date = models.DateField(null=True, blank=True)
    return_date    = models.DateField(null=True, blank=True)
    remarks_bn     = models.TextField(blank=True)
    remarks_en     = models.TextField(blank=True)

    class Meta:
        ordering = ['mp__name_bn']
        unique_together = [('tour', 'mp')]

    def __str__(self):
        return f"{self.mp.name_bn} — {self.tour.go_number}"


class ForeignTourCountry(models.Model):
    tour     = models.ForeignKey(ForeignTour, on_delete=models.CASCADE, related_name='countries')
    country  = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='tour_visits')
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering']
        unique_together = [('tour', 'country')]

    def __str__(self):
        return f"{self.tour.go_number} — {self.country.name_bn}"
