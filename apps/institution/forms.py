from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import GovernmentInstitution, InstitutionRole
from apps.mp.form_fields import MPChoiceField
from apps.parliament.models import Parliament
from .models import InstitutionAssignment


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
            elif isinstance(w, forms.DateInput):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('type', 'date')


class InstitutionAssignmentForm(_BootstrapMixin, forms.ModelForm):
    mp = MPChoiceField(required=True)
    institution = BilingualChoiceField(
        queryset=GovernmentInstitution.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- প্রতিষ্ঠান নির্বাচন করুন / Select Institution --',
    )

    class Meta:
        model  = InstitutionAssignment
        fields = [
            'mp',
            'parliament', 'institution', 'role',
            'start_date', 'end_date', 'go_number', 'go_date',
            'nomination_date', 'is_active', 'remarks_bn', 'remarks_en',
        ]
        widgets = {
            'start_date':      forms.DateInput(attrs={'type': 'date'}),
            'end_date':        forms.DateInput(attrs={'type': 'date'}),
            'go_date':         forms.DateInput(attrs={'type': 'date'}),
            'nomination_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, mp_preset=False, **kwargs):
        super().__init__(*args, **kwargs)
        if mp_preset:
            self.fields.pop('mp')
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['role'].queryset = InstitutionRole.objects.filter(
            is_active=True).order_by('ordering')
        for f in ('end_date', 'go_date', 'nomination_date'):
            self.fields[f].required = False
