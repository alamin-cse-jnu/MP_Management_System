from django import forms

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import GovernmentInstitution, InstitutionRole
from apps.mp.form_fields import MPChoiceField, MPMultipleChoiceField
from apps.parliament.models import Parliament
from utils.go_files import GO_FILE_ACCEPT
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
    """Single-MP form — used for edit and create-from-MP-profile."""
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
            'start_date', 'end_date', 'go_number', 'go_date', 'go_file',
            'nominated_by', 'remarks_bn', 'remarks_en',
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
        self.fields['role'].queryset = InstitutionRole.objects.filter(
            is_active=True).order_by('ordering')
        for f in ('end_date', 'go_date', 'go_file'):
            self.fields[f].required = False


class InstitutionBulkAssignForm(_BootstrapMixin, forms.ModelForm):
    """Multi-MP form — one GO covering several MPs creates one row per MP."""
    mps = MPMultipleChoiceField(required=True, label='সংসদ সদস্যগণ / Members of Parliament')
    institution = BilingualChoiceField(
        queryset=GovernmentInstitution.objects.filter(is_active=True).order_by('name_bn'),
        empty_label='-- প্রতিষ্ঠান নির্বাচন করুন / Select Institution --',
    )

    class Meta:
        model  = InstitutionAssignment
        fields = [
            'parliament', 'institution', 'role',
            'start_date', 'end_date', 'go_number', 'go_date', 'go_file',
            'nominated_by', 'remarks_bn', 'remarks_en',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'type': 'date'}),
            'go_date':    forms.DateInput(attrs={'type': 'date'}),
            'go_file':    forms.ClearableFileInput(attrs={'accept': GO_FILE_ACCEPT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parliament'].queryset = Parliament.objects.order_by('-start_date')
        self.fields['role'].queryset = InstitutionRole.objects.filter(
            is_active=True).order_by('ordering')
        for f in ('end_date', 'go_date', 'go_file'):
            self.fields[f].required = False

    def save_rows(self):
        """Create one InstitutionAssignment per selected MP. Returns the count."""
        cd = self.cleaned_data
        mps = list(cd['mps'])
        shared = dict(
            parliament=cd['parliament'], institution=cd['institution'], role=cd['role'],
            start_date=cd['start_date'], end_date=cd['end_date'],
            go_number=cd['go_number'], go_date=cd['go_date'],
            nominated_by=cd['nominated_by'],
            remarks_bn=cd['remarks_bn'], remarks_en=cd['remarks_en'],
        )
        file_name = None
        for i, mp_obj in enumerate(mps):
            obj = InstitutionAssignment(mp=mp_obj, **shared)
            if i == 0:
                obj.go_file = cd.get('go_file')
                obj.save()
                file_name = obj.go_file.name if obj.go_file else None
            else:
                if file_name:
                    obj.go_file = file_name
                obj.save()
        return len(mps)
