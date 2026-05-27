from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Menu, Role, SubMenu


class _BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.TextInput, forms.NumberInput,
                               forms.EmailInput, forms.PasswordInput)):
                w.attrs.setdefault('class', 'form-control')
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('rows', '3')
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
                w.attrs.setdefault('data-select2', '')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')


class RoleForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name_bn', 'name_en', 'description_bn', 'description_en']


class CustomUserCreateForm(_BootstrapMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ['username', 'full_name_bn', 'full_name_en', 'email',
                  'role', 'is_superadmin', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # password1 / password2 widgets added by UserCreationForm
        for fname in ('password1', 'password2'):
            if fname in self.fields:
                self.fields[fname].widget.attrs['class'] = 'form-control'


class CustomUserUpdateForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'full_name_bn', 'full_name_en', 'email',
                  'role', 'is_superadmin', 'is_active']


class MenuForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name_bn', 'name_en', 'icon', 'url_name', 'ordering', 'is_active']


class SubMenuForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = SubMenu
        fields = ['menu', 'name_bn', 'name_en', 'url_name', 'ordering', 'is_active']
