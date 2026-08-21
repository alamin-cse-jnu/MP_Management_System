from django.conf import settings
from django.db import models

from apps.master.models import Country, TravelPurpose, TravelType
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
    """An officer accompanying MPs on a tour.

    Normally picked from the PRP-synced roster (``officer`` FK). The name /
    designation / ID columns are a **frozen snapshot** taken at save time, so a
    past GO keeps rendering exactly as it was recorded even after the officer's
    designation changes or he leaves the service. ``is_external`` marks someone
    typed in by hand because they are outside the Secretariat (e.g. a ministry
    or embassy officer on the same GO) — sync never touches those rows.
    """
    tour           = models.ForeignKey(ForeignTour, on_delete=models.CASCADE, related_name='officers')
    officer        = models.ForeignKey('officer.Officer', on_delete=models.PROTECT,
                                       null=True, blank=True, related_name='tour_assignments')
    is_external    = models.BooleanField(default=False)
    prp_id         = models.CharField('PRP ID', max_length=50, blank=True)   # snapshot, searchable
    name_bn        = models.CharField(max_length=200)                        # snapshot, searchable
    name_en        = models.CharField(max_length=200, blank=True)
    designation_bn = models.CharField('পদবী / Designation', max_length=200, blank=True)
    designation_en = models.CharField(max_length=200, blank=True)
    remarks_bn     = models.TextField(blank=True)
    remarks_en     = models.TextField(blank=True)

    class Meta:
        ordering = ['name_bn']

    def __str__(self):
        return f"{self.name_bn} — {self.tour.go_number}"

    @classmethod
    def snapshot_fields(cls, officer):
        """Freeze a roster Officer into this row's own columns."""
        return {
            'prp_id':         officer.prp_id,
            'name_bn':        officer.display_name_bn,
            'name_en':        officer.display_name_en,
            'designation_bn': officer.designation_bn,
            'designation_en': officer.designation_en,
            'is_external':    False,
        }

    @property
    def is_retired(self):
        """True when this row is linked to an officer who is no longer selectable."""
        return bool(self.officer_id) and not self.officer.is_active


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
