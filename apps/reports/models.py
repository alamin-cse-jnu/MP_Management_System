from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'তৈরি'),
        ('UPDATE', 'পরিবর্তন'),
        ('DELETE', 'মুছে ফেলা'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name='ব্যবহারকারী',
    )
    app_label   = models.CharField(max_length=50, blank=True)
    model_name  = models.CharField(max_length=100, verbose_name='মডেল')
    object_id   = models.CharField(max_length=50, verbose_name='রেকর্ড আইডি')
    object_repr = models.CharField(max_length=300, blank=True, verbose_name='রেকর্ড')
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='কার্যক্রম')
    changes     = models.JSONField(default=dict, blank=True, verbose_name='পরিবর্তন')
    timestamp   = models.DateTimeField(auto_now_add=True, verbose_name='সময়')
    ip_address  = models.GenericIPAddressField(null=True, blank=True, verbose_name='আইপি')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Audit Log'

    def __str__(self):
        return f"{self.action} {self.model_name} #{self.object_id}"

    def get_action_display_bn(self):
        return dict(self.ACTION_CHOICES).get(self.action, self.action)
