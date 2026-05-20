from django import forms

from .models import ParliamentOfficeAddress


class _BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.TextInput, forms.NumberInput, forms.EmailInput,
                               forms.URLInput, forms.PasswordInput)):
                w.attrs.setdefault('class', 'form-control')
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('rows', 3)
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')


class OfficeAddressForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = ParliamentOfficeAddress
        fields = [
            'room_number', 'building_bn', 'building_en',
            'address_bn', 'address_en',
            'telephone', 'extension', 'fax', 'official_email',
            'secretary_name_bn', 'secretary_name_en', 'secretary_mobile',
            'is_active',
        ]
