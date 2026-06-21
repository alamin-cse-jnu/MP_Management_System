from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import CommitteePosition, StandingCommittee
from apps.mp.form_fields import MPChoiceField, MPMultipleChoiceField
from apps.parliament.models import Parliament
from utils.go_files import GO_FILE_ACCEPT
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
                w.attrs.setdefault('data-select2', '')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')
            elif isinstance(w, forms.DateInput):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('type', 'date')


class CommitteeAssignmentForm(_BootstrapMixin, forms.ModelForm):
    mp = MPChoiceField(required=True)
    committee = BilingualChoiceField(
        queryset=StandingCommittee.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- কমিটি নির্বাচন করুন / Select Committee --',
    )

    class Meta:
        model  = CommitteeAssignment
        fields = [
            'mp',
            'parliament', 'committee', 'position',
            'start_date', 'end_date', 'go_number', 'go_date', 'go_file',
            'remarks_bn', 'remarks_en',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'go_date':    forms.DateInput(attrs={'type': 'date'}),
            'go_file':    forms.ClearableFileInput(attrs={'accept': GO_FILE_ACCEPT}),
        }

    def __init__(self, *args, mp_preset=False, **kwargs):
        super().__init__(*args, **kwargs)
        if mp_preset:
            self.fields.pop('mp')
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['position'].queryset = CommitteePosition.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['end_date'].required = False
        self.fields['go_date'].required = False
        self.fields['go_file'].required = False


class CommitteeBulkStep1Form(_BootstrapMixin, forms.Form):
    """
    Step 1 of bulk committee assignment: pick the committee, the (guide-only)
    total member count, and the MPs. Positions are chosen per-MP in step 2.
    """
    parliament  = forms.ModelChoiceField(
        queryset=Parliament.objects.order_by('-start_date'),
        empty_label='-- সংসদ নির্বাচন করুন / Select Parliament --',
    )
    committee   = BilingualChoiceField(
        queryset=StandingCommittee.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- কমিটি নির্বাচন করুন / Select Committee --',
    )
    total_count = forms.IntegerField(
        required=False, min_value=1,
        label='মোট সদস্য সংখ্যা / Total members',
        help_text='শুধু নির্দেশিকা — সংরক্ষিত হয় না। Guide only, not stored.',
    )
    mps         = MPMultipleChoiceField(required=True,
                                        label='সংসদ সদস্যগণ / Members of Parliament')
    start_date  = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date    = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    go_number   = forms.CharField(required=False, max_length=100)
    go_date     = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
