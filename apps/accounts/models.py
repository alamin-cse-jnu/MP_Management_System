from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    role = models.ForeignKey(
        'Role', null=True, blank=True, on_delete=models.SET_NULL, related_name='users'
    )
    is_superadmin = models.BooleanField(default=False)
    full_name_bn = models.CharField(max_length=200, blank=True)
    full_name_en = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users'
    )

    class Meta:
        verbose_name = 'User'

    def __str__(self):
        return self.full_name_bn or self.username


class Menu(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True)
    url_name = models.CharField(max_length=100, blank=True)
    ordering = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordering']

    def __str__(self):
        return self.name_en


class SubMenu(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='submenus')
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    url_name = models.CharField(max_length=100)
    ordering = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordering']

    def __str__(self):
        return self.name_en


class Role(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    description_bn = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    created_by = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name_en


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    submenu = models.ForeignKey(SubMenu, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)

    class Meta:
        unique_together = ['role', 'submenu']
