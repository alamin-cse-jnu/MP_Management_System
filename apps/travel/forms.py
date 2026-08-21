from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import Country, TravelPurpose, TravelType
from apps.mp.form_fields import MPChoiceField, MPMultipleChoiceField
from apps.officer.form_fields import OfficerMultipleChoiceField, selectable_queryset
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


class TourOfficersForm(forms.Form):
    """Accompanying officers, picked from the PRP-synced roster.

    The queryset is set per-tour so officers already attached stay selectable
    even after they retire (see officer.form_fields.selectable_queryset).
    """
    officers = OfficerMultipleChoiceField(required=False)

    def __init__(self, *args, attached_pks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['officers'].queryset = selectable_queryset(include_pks=attached_pks)


class OfficerForm(_BootstrapMixin, forms.ModelForm):
    """Manual entry for an officer who is NOT in the PRP roster — e.g. a
    ministry or embassy officer travelling on the same GO. Rows saved through
    this form carry `is_external=True` and are never touched by sync."""

    class Meta:
        model  = ForeignTourOfficer
        fields = ['name_bn', 'name_en', 'designation_bn', 'designation_en']
        widgets = {
            'name_bn':        forms.TextInput(attrs={'placeholder': 'নাম (বাংলা)'}),
            'name_en':        forms.TextInput(attrs={'placeholder': 'Name (English)'}),
            'designation_bn': forms.TextInput(attrs={'placeholder': 'যেমন: যুগ্ম সচিব'}),
            'designation_en': forms.TextInput(attrs={'placeholder': 'e.g. Joint Secretary'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ('name_en', 'designation_bn', 'designation_en'):
            self.fields[f].required = False


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


class TourParticipantsForm(forms.Form):
    """Participant picker for the single-page tour form. Unlike ParticipantBulkForm
    it lists ALL MPs (existing ones pre-checked) so the save step can reconcile
    the participant set (add newly-checked, drop unchecked)."""
    mps = MPMultipleChoiceField(required=False, label='সংসদ সদস্যগণ / Members of Parliament')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mps'].queryset = MPChoiceField.annotated_queryset()


# ── Inline formsets for the single-submit create/edit page (Phase 17.10) ───────
# `TourCountryForm`/`OfficerForm` are instantiated by the factory without the
# `tour` kwarg, so their queryset/init defaults handle the formset case.
CountryFormSet = forms.inlineformset_factory(
    ForeignTour, ForeignTourCountry, form=TourCountryForm,
    extra=1, can_delete=True,
)
# External (non-PRP) officers only — the roster-picked rows are reconciled by
# TourOfficersForm. The two sets are disjoint (officer FK set vs null), so the
# picker and this formset never fight over the same row.
OfficerFormSet = forms.inlineformset_factory(
    ForeignTour, ForeignTourOfficer, form=OfficerForm,
    extra=1, can_delete=True,
)
