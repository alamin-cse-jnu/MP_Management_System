from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import Country, TravelPurpose, TravelType
from apps.mp.form_fields import MPChoiceField
from apps.parliament.models import Parliament
from .models import ForeignTour, ForeignTourCountry, ForeignTourParticipant


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


class ForeignTourForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = ForeignTour
        fields = [
            'parliament', 'go_number', 'go_date',
            'tour_type', 'purpose', 'purpose_detail_bn', 'purpose_detail_en',
        ]
        widgets = {
            'go_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['tour_type'].queryset = TravelType.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['purpose'].queryset = TravelPurpose.objects.filter(
            is_active=True).order_by('ordering')


class ParticipantForm(_BootstrapMixin, forms.ModelForm):
    mp = MPChoiceField(required=True)

    class Meta:
        model  = ForeignTourParticipant
        fields = ['mp', 'departure_date', 'return_date', 'remarks_bn', 'remarks_en']
        widgets = {
            'departure_date': forms.DateInput(attrs={'type': 'date'}),
            'return_date':    forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        exclude_ids = None
        if tour is not None:
            exclude_ids = list(tour.participants.values_list('mp_id', flat=True))
        self.fields['mp'].queryset = MPChoiceField.annotated_queryset(exclude_pks=exclude_ids)
        for f in ('departure_date', 'return_date'):
            self.fields[f].required = False


class TourCountryForm(_BootstrapMixin, forms.ModelForm):
    country = BilingualChoiceField(
        queryset=Country.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- দেশ নির্বাচন করুন / Select Country --',
    )

    class Meta:
        model  = ForeignTourCountry
        fields = ['country', 'ordering']

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tour is not None:
            existing_ids = list(tour.countries.values_list('country_id', flat=True))
            self.fields['country'].queryset = Country.objects.filter(
                is_active=True).exclude(pk__in=existing_ids).order_by('name_bn')
        else:
            self.fields['country'].queryset = Country.objects.filter(
                is_active=True).order_by('name_bn')
