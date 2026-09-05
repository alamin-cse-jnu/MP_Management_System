from django import forms

from utils.form_dates import normalize_date_fields

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import District, SpecialRoleType
from apps.mp.form_fields import MPChoiceField
from apps.mp.models import SpecialPositionHistory
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
        normalize_date_fields(self)


class ParliamentForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Parliament
        fields = ['name_bn', 'name_en', 'ordinal', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ConstituencyForm(_BootstrapMixin, forms.ModelForm):
    district = BilingualChoiceField(
        queryset=District.objects.filter(is_active=True).select_related('division').order_by('name_bn'),
        required=False,
        empty_label='-- জেলা নির্বাচন করুন / Select District --',
    )

    class Meta:
        model = Constituency
        fields = ['display_bn', 'display_en', 'district', 'ordering']


class SpecialPositionForm(_BootstrapMixin, forms.ModelForm):
    """Speaker / Deputy Speaker / Chief Whip / Whip / Leader of the House …

    The MP field is dropped when the form is opened from a profile (the member
    is already known); from the module it is a searchable picker. Technocrat
    ministers hold no seat, so they cannot hold an office of the House.

    The "only one sitting Speaker" guard lives in `SpecialPositionHistory.clean()`
    — ModelForm's `_post_clean` runs it on both routes and lands the message on
    the role field, so there is nothing to repeat here.
    """
    role = BilingualChoiceField(
        queryset=SpecialRoleType.objects.filter(is_active=True).order_by('ordering', 'name_bn'),
        empty_label='-- পদ নির্বাচন করুন / Select Position --',
    )

    class Meta:
        model  = SpecialPositionHistory
        fields = ['mp', 'parliament', 'role', 'from_date', 'to_date',
                  'go_number', 'go_date', 'is_active', 'remarks_bn', 'remarks_en']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date'}),
            'to_date':   forms.DateInput(attrs={'type': 'date'}),
            'go_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, mp_preset=False, **kwargs):
        super().__init__(*args, **kwargs)
        if mp_preset:
            self.fields.pop('mp')
        else:
            self.fields['mp'] = MPChoiceField(required=True, include_technocrats=False)
            self.fields['mp'].widget.attrs.setdefault('class', 'form-select')
            self.fields['mp'].widget.attrs.setdefault('data-select2', '')
        self.fields['parliament'].queryset = Parliament.objects.order_by('-ordinal')
        for optional in ('from_date', 'to_date', 'go_date'):
            self.fields[optional].required = False
