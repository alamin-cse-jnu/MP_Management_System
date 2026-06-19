from django.db import models

from apps.master.models import Ministry, MinisterType
from apps.mp.models import MP
from apps.parliament.models import Parliament
from utils.go_files import validate_go_file


class MinistryAssignment(models.Model):
    mp            = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='ministry_assignments')
    parliament    = models.ForeignKey(Parliament, on_delete=models.PROTECT, related_name='ministry_assignments')
    ministry      = models.ForeignKey(Ministry, on_delete=models.PROTECT, related_name='assignments')
    minister_type = models.ForeignKey(MinisterType, on_delete=models.PROTECT, related_name='assignments')
    start_date    = models.DateField()
    end_date      = models.DateField(null=True, blank=True)
    go_number     = models.CharField(max_length=100, blank=True)
    go_date       = models.DateField(null=True, blank=True)
    go_file       = models.FileField(upload_to='go/ministry/', blank=True, null=True,
                                     validators=[validate_go_file])
    is_active     = models.BooleanField(default=True)
    remarks_bn    = models.TextField(blank=True)
    remarks_en    = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['minister_type__ordering', 'ministry__name_bn']

    def __str__(self):
        return f"{self.mp.name_bn} — {self.ministry.name_bn}"
