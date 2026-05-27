from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import Ministry, MinisterType
from apps.mp.form_fields import MPChoiceField
from apps.parliament.models import Parliament
from .models import MinistryAssignment


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


class MinistryAssignmentForm(_BootstrapMixin, forms.ModelForm):
    mp = MPChoiceField(required=True)
    ministry = BilingualChoiceField(
        queryset=Ministry.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- মন্ত্রণালয় নির্বাচন করুন / Select Ministry --',
    )

    class Meta:
        model  = MinistryAssignment
        fields = [
            'mp',
            'parliament', 'ministry', 'minister_type',
            'start_date', 'end_date', 'go_number', 'go_date',
            'is_active', 'remarks_bn', 'remarks_en',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'go_date':    forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, mp_preset=False, **kwargs):
        super().__init__(*args, **kwargs)
        if mp_preset:
            self.fields.pop('mp')
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['minister_type'].queryset = MinisterType.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['end_date'].required = False
        self.fields['go_date'].required = False
