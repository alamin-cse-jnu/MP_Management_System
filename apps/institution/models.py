from django.db import models

from apps.master.models import GovernmentInstitution, InstitutionRole
from apps.mp.models import MP
from apps.parliament.models import Parliament


class InstitutionAssignment(models.Model):
    mp              = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='institution_assignments')
    parliament      = models.ForeignKey(Parliament, on_delete=models.PROTECT, related_name='institution_assignments')
    institution     = models.ForeignKey(GovernmentInstitution, on_delete=models.PROTECT, related_name='assignments')
    role            = models.ForeignKey(InstitutionRole, on_delete=models.PROTECT, related_name='assignments')
    start_date      = models.DateField()
    end_date        = models.DateField(null=True, blank=True)
    go_number       = models.CharField(max_length=200, blank=True)
    go_date         = models.DateField(null=True, blank=True)
    nomination_date = models.DateField(null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    remarks_bn      = models.TextField(blank=True)
    remarks_en      = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['institution__name_bn']

    def __str__(self):
        return f"{self.mp.name_bn} — {self.institution.name_bn}"
