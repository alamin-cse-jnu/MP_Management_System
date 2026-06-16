from django.db import models

from apps.mp.models import MP


class ParliamentOfficeAddress(models.Model):
    mp              = models.OneToOneField(MP, on_delete=models.CASCADE, related_name='office_address')
    room_number     = models.CharField(max_length=50, blank=True)
    building_bn     = models.CharField(max_length=200, blank=True)
    building_en     = models.CharField(max_length=200, blank=True)
    address_bn      = models.CharField(
        max_length=500,
        default='জাতীয় সংসদ ভবন, শের-ই-বাংলা নগর, ঢাকা-১২০৭'
    )
    address_en      = models.CharField(
        max_length=500,
        default='National Parliament House, Sher-e-Bangla Nagar, Dhaka-1207'
    )
    telephone       = models.CharField(max_length=30, blank=True)
    extension       = models.CharField(max_length=20, blank=True)
    fax             = models.CharField(max_length=30, blank=True)
    official_email  = models.EmailField(blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.mp.name_bn} — অফিস ঠিকানা"


class MPPAStaff(models.Model):
    """PA/PS (Personal Assistant / Private Secretary) assigned to an MP's office."""
    office      = models.ForeignKey(
        ParliamentOfficeAddress, on_delete=models.CASCADE, related_name='pa_staff'
    )
    name_bn     = models.CharField(max_length=200)
    name_en     = models.CharField(max_length=200, blank=True)
    designation = models.ForeignKey(
        'master.PADesignation', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='staff_members'
    )
    mobile      = models.CharField(max_length=20, blank=True)
    ordering    = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return self.name_bn
