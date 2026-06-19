from django.db import models


class Parliament(models.Model):
    name_bn    = models.CharField(max_length=200)   # ১৩তম জাতীয় সংসদ
    name_en    = models.CharField(max_length=200)   # 13th National Parliament
    ordinal    = models.IntegerField(default=0)     # 13  (used for ordering)
    start_date = models.DateField(null=True, blank=True)
    end_date   = models.DateField(null=True, blank=True)
    is_active  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ordinal']
        verbose_name = 'Parliament'

    def save(self, *args, **kwargs):
        # Mutex: only one Parliament can be active at a time
        if self.is_active:
            Parliament.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Constituency(models.Model):
    """300 directly-elected seats. Admin enters both Bangla and English names."""
    display_bn = models.CharField(max_length=100)   # ১ পঞ্চগড়-১
    display_en = models.CharField(max_length=100)   # 1 Panchagarh-1
    # Geographic district this constituency belongs to. Enables division/district
    # reports based on constituency (not just the MP's home district). Division
    # is reached via district.division.
    district   = models.ForeignKey('master.District', on_delete=models.PROTECT,
                                   null=True, blank=True, related_name='constituencies')
    is_active  = models.BooleanField(default=True)
    ordering   = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'display_en']
        verbose_name = 'Constituency'
        verbose_name_plural = 'Constituencies'

    def __str__(self):
        return f"{self.display_bn} ({self.display_en})"
