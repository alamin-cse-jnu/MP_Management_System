from django.db import models

from apps.master.models import CommitteePosition, StandingCommittee
from apps.mp.models import MP
from apps.parliament.models import Parliament


class CommitteeAssignment(models.Model):
    mp         = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='committee_assignments')
    parliament = models.ForeignKey(Parliament, on_delete=models.PROTECT, related_name='committee_assignments')
    committee  = models.ForeignKey(StandingCommittee, on_delete=models.PROTECT, related_name='assignments')
    position   = models.ForeignKey(CommitteePosition, on_delete=models.PROTECT, related_name='assignments')
    start_date = models.DateField()
    end_date   = models.DateField(null=True, blank=True)
    go_number  = models.CharField(max_length=100, blank=True)
    go_date    = models.DateField(null=True, blank=True)
    is_active  = models.BooleanField(default=True)
    remarks_bn = models.TextField(blank=True)
    remarks_en = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['committee__name_bn']

    def __str__(self):
        return f"{self.mp.name_bn} — {self.committee.name_bn}"
