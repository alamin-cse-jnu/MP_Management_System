from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import Country, OfficerDesignation, TravelPurpose, TravelType
from apps.mp.form_fields import MPChoiceField, MPMultipleChoiceField
from apps.parliament.models import Parliament
from utils.go_files import GO_FILE_ACCEPT
from .models import (ForeignTour, ForeignTourCountry, ForeignTourOfficer,
                     ForeignTourParticipant)


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
            'parliament', 'go_number', 'go_date', 'go_file',
            'tour_type', 'purpose', 'purpose_detail_bn', 'purpose_detail_en',
        ]
        widgets = {
            'go_date': forms.DateInput(attrs={'type': 'date'}),
            'go_file': forms.ClearableFileInput(attrs={'accept': GO_FILE_ACCEPT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['tour_type'].queryset = TravelType.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['purpose'].queryset = TravelPurpose.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['go_file'].required = False


class ParticipantBulkForm(forms.Form):
    """Add several MPs to a tour at once (one GO covering multiple MPs)."""
    mps = MPMultipleChoiceField(required=True, label='সংসদ সদস্যগণ / Members of Parliament')

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        exclude_ids = None
        if tour is not None:
            exclude_ids = list(tour.participants.values_list('mp_id', flat=True))
        self.fields['mps'].queryset = MPChoiceField.annotated_queryset(exclude_pks=exclude_ids)


class OfficerForm(_BootstrapMixin, forms.ModelForm):
    designation = BilingualChoiceField(
        queryset=OfficerDesignation.objects.filter(is_active=True).order_by('ordering', 'name_bn'),
        empty_label='-- পদবী নির্বাচন করুন / Select Designation --',
    )

    class Meta:
        model  = ForeignTourOfficer
        fields = ['officer_id', 'name', 'designation', 'remarks_bn', 'remarks_en']


class TourCountryForm(_BootstrapMixin, forms.ModelForm):
    country = BilingualChoiceField(
        queryset=Country.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- দেশ নির্বাচন করুন / Select Country --',
    )

    class Meta:
        model  = ForeignTourCountry
        fields = ['country', 'from_date', 'to_date', 'ordering']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date'}),
            'to_date':   forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ('from_date', 'to_date'):
            self.fields[f].required = False
        if tour is not None:
            existing_ids = list(tour.countries.values_list('country_id', flat=True))
            self.fields['country'].queryset = Country.objects.filter(
                is_active=True).exclude(pk__in=existing_ids).order_by('name_bn')
        else:
            self.fields['country'].queryset = Country.objects.filter(
                is_active=True).order_by('name_bn')
