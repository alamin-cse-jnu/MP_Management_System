from django import forms

from .models import Constituency, Parliament


class _BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.TextInput, forms.NumberInput, forms.DateInput)):
                w.attrs.setdefault('class', 'form-control')
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('rows', '3')
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
                w.attrs.setdefault('data-select2', '')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')


class ParliamentForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Parliament
        fields = ['name_bn', 'name_en', 'ordinal', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ConstituencyForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Constituency
        fields = ['display_bn', 'display_en', 'ordering']
