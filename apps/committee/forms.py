from django import forms

from utils.form_dates import normalize_date_fields

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import CommitteePosition, StandingCommittee, SubCommittee
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
        normalize_date_fields(self)


def _wire_subcommittee_cascade(form):
    """Point the committee <select> at the sub-committee options endpoint.

    Both entry paths carry the same two selects, so the htmx attributes live in
    one place. The committee box is a Select2, which announces a pick with a
    jQuery event that htmx's native listener never sees — the form templates
    carry the jQuery bridge that re-fires it (gotcha 12).
    """
    from django.urls import reverse
    form.fields['committee'].widget.attrs.update({
        'hx-get': reverse('committee:subcommittee_options'),
        # A custom event, not 'change': Select2 announces a pick with a jQuery
        # event that htmx's native change listener never sees (gotcha 12), so
        # the bridge in committee/partials/_cascade_js.html re-fires this one.
        'hx-trigger': 'committee-changed',
        'hx-target': '#id_sub_committee',
        'hx-swap': 'innerHTML',
        'hx-include': 'this',
    })

    # The sub-committee list is scoped to ONE committee, on the server as well
    # as in the browser: a bound POST is validated against the committee it
    # actually carries, so a sub-committee belonging to a different parent is
    # rejected as an invalid choice before the model guard is even reached.
    committee_id = None
    if form.is_bound:
        committee_id = str(form.data.get(form.add_prefix('committee')) or '').strip() or None
    else:
        initial = form.initial.get('committee') or form.fields['committee'].initial
        if initial is None and getattr(form, 'instance', None) is not None:
            initial = getattr(form.instance, 'committee_id', None)
        committee_id = getattr(initial, 'pk', initial)
    qs = form.fields['sub_committee'].queryset
    form.fields['sub_committee'].queryset = (
        qs.filter(committee_id=committee_id) if committee_id else qs.none())


class CommitteeAssignmentForm(_BootstrapMixin, forms.ModelForm):
    # Committee membership requires holding a seat, so technocrat ministers
    # are not selectable here (unlike ministry/travel/institution).
    mp = MPChoiceField(required=True, include_technocrats=False)
    committee = BilingualChoiceField(
        queryset=StandingCommittee.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- কমিটি নির্বাচন করুন / Select Committee --',
    )

    # Every active sub-committee is offered to the *validator*; the browser
    # narrows the visible options to the chosen committee over HTMX. Keeping the
    # queryset wide here means a POST is checked against the real rule
    # (CommitteeAssignment.clean) rather than against whatever the widget
    # happened to be showing.
    sub_committee = BilingualChoiceField(
        queryset=SubCommittee.objects.filter(is_active=True).select_related('committee'),
        required=False,
        empty_label='-- মূল কমিটি (উপ-কমিটি নয়) / Main committee (no sub-committee) --',
    )

    class Meta:
        model  = CommitteeAssignment
        fields = [
            'mp',
            'parliament', 'committee', 'sub_committee', 'position',
            'start_date', 'end_date', 'go_number', 'go_date', 'go_file',
            'remarks_bn', 'remarks_en',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'go_date':    forms.DateInput(attrs={'type': 'date'}),
            'go_file':    forms.ClearableFileInput(attrs={'accept': GO_FILE_ACCEPT}),
        }

    def __init__(self, *args, mp_preset=False, mp_instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        if mp_preset:
            self.fields.pop('mp')
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['position'].queryset = CommitteePosition.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['end_date'].required = False
        self.fields['go_date'].required = False
        self.fields['go_file'].required = False
        _wire_subcommittee_cascade(self)
        if mp_instance is not None:
            # Set before validation, not after save(commit=False) — the
            # sub-committee guard needs to know WHICH member this is.
            self.instance.mp = mp_instance


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
    sub_committee = BilingualChoiceField(
        queryset=SubCommittee.objects.filter(is_active=True).select_related('committee'),
        required=False,
        label='উপ-কমিটি / Sub-Committee',
        empty_label='-- মূল কমিটি (উপ-কমিটি নয়) / Main committee (no sub-committee) --',
        help_text='উপ-কমিটি বাছাই করলে সদস্য তালিকা মূল কমিটির সদস্যদের মধ্যে সীমিত হয়। / '
                  "Choosing a sub-committee limits the member list to the parent committee's members.",
    )
    total_count = forms.IntegerField(
        required=False, min_value=1,
        label='মোট সদস্য সংখ্যা / Total members',
        help_text='শুধু নির্দেশিকা — সংরক্ষিত হয় না। Guide only, not stored.',
    )
    mps         = MPMultipleChoiceField(required=True, include_technocrats=False,
                                        label='সংসদ সদস্যগণ / Members of Parliament')
    start_date  = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date    = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    go_number   = forms.CharField(required=False, max_length=100)
    go_date     = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _wire_subcommittee_cascade(self)

    def clean(self):
        """A sub-committee is staffed from its parent committee's members.

        The picker is narrowed over HTMX, but the rule is enforced here too:
        the browser list is a convenience and a POST can carry anything.
        """
        cleaned = super().clean()
        sub = cleaned.get('sub_committee')
        com = cleaned.get('committee')
        parl = cleaned.get('parliament')
        if sub and com and sub.committee_id != com.pk:
            self.add_error('sub_committee',
                           'এই উপ-কমিটি নির্বাচিত স্থায়ী কমিটির অধীনে নয়। / '
                           'This sub-committee does not belong to the selected standing committee.')
            return cleaned
        if sub and com and parl:
            members = set(CommitteeAssignment.objects.filter(
                parliament=parl, committee=com, sub_committee__isnull=True, is_active=True,
            ).values_list('mp_id', flat=True))
            outsiders = [m for m in cleaned.get('mps') or [] if m.pk not in members]
            if outsiders:
                names = ', '.join(m.name_bn or m.name_en for m in outsiders)
                self.add_error('mps',
                               f'এঁরা মূল কমিটির সদস্য নন — {names}। '
                               f'আগে মূল কমিটিতে যোগ করুন। / Not members of the main '
                               f'committee: {names}. Add their main-committee seat first.')
        return cleaned
