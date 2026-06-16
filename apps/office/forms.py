from django import forms
from django.forms import inlineformset_factory

from .models import MPPAStaff, ParliamentOfficeAddress


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
                w.attrs.setdefault('data-select2', '')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')


class OfficeAddressForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = ParliamentOfficeAddress
        fields = [
            'room_number', 'building_bn', 'building_en',
            'address_bn', 'address_en',
            'telephone', 'extension', 'fax', 'official_email',
            'is_active',
        ]


class MPPAStaffForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = MPPAStaff
        fields = ['name_bn', 'name_en', 'designation', 'mobile', 'ordering']


PAStaffFormSet = inlineformset_factory(
    ParliamentOfficeAddress,
    MPPAStaff,
    form=MPPAStaffForm,
    extra=1,
    can_delete=True,
)
