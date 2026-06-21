from django.conf import settings
from django.db import models

from apps.master.models import Country, OfficerDesignation, TravelPurpose, TravelType
from apps.mp.models import MP
from apps.parliament.models import Parliament
from utils.go_files import validate_go_file


class ForeignTour(models.Model):
    go_number         = models.CharField(max_length=200)
    go_date           = models.DateField()
    go_file           = models.FileField(upload_to='go/travel/', blank=True, null=True,
                                         validators=[validate_go_file])
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

    @property
    def overall_from_date(self):
        """Earliest country from_date — the tour's start, applies to all participants."""
        dates = [c.from_date for c in self.countries.all() if c.from_date]
        return min(dates) if dates else None

    @property
    def overall_to_date(self):
        """Latest country to_date — the tour's end, applies to all participants."""
        dates = [c.to_date for c in self.countries.all() if c.to_date]
        return max(dates) if dates else None


class ForeignTourParticipant(models.Model):
    tour           = models.ForeignKey(ForeignTour, on_delete=models.CASCADE, related_name='participants')
    mp             = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='travel_participations')
    remarks_bn     = models.TextField(blank=True)
    remarks_en     = models.TextField(blank=True)

    class Meta:
        ordering = ['mp__name_bn']
        unique_together = [('tour', 'mp')]

    def __str__(self):
        return f"{self.mp.name_bn} — {self.tour.go_number}"


class ForeignTourOfficer(models.Model):
    """Officer accompanying MPs on a tour. ID & name are free text; designation
    comes from master data (OfficerDesignation) for reporting."""
    tour        = models.ForeignKey(ForeignTour, on_delete=models.CASCADE, related_name='officers')
    officer_id  = models.CharField(max_length=50, blank=True)   # free text, searchable
    name        = models.CharField(max_length=200)              # free text, searchable
    designation = models.ForeignKey(OfficerDesignation, on_delete=models.PROTECT,
                                    related_name='tour_officers')
    remarks_bn  = models.TextField(blank=True)
    remarks_en  = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} — {self.tour.go_number}"


class ForeignTourCountry(models.Model):
    tour      = models.ForeignKey(ForeignTour, on_delete=models.CASCADE, related_name='countries')
    country   = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='tour_visits')
    from_date = models.DateField(null=True, blank=True)
    to_date   = models.DateField(null=True, blank=True)
    ordering  = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering']
        unique_together = [('tour', 'country')]

    def __str__(self):
        return f"{self.tour.go_number} — {self.country.name_bn}"
