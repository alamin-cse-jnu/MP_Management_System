from django import forms

from apps.master.models import CommitteePosition, StandingCommittee
from apps.parliament.models import Parliament
from .models import CommitteeAssignment


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
            elif isinstance(w, forms.DateInput):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('type', 'date')


class CommitteeAssignmentForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = CommitteeAssignment
        fields = [
            'parliament', 'committee', 'position',
            'start_date', 'end_date', 'go_number', 'go_date',
            'is_active', 'remarks_bn', 'remarks_en',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'go_date':    forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['committee'].queryset = StandingCommittee.objects.filter(is_active=True).order_by('name_bn')
        self.fields['position'].queryset = CommitteePosition.objects.filter(is_active=True).order_by('ordering')
        self.fields['end_date'].required = False
        self.fields['go_date'].required = False
