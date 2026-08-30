from django import forms
from django.db import models

from utils.form_dates import normalize_date_fields

from apps.master.form_fields import BilingualChoiceField
from apps.master.models import (
    Country, DegreeName, District, DivisionResult, EducationGroup,
    EducationInstitution, EducationLevel, EducationSubject, ResultType,
    TravelPurpose, Upazila,
)
from .models import (
    MP, ElectionInfo, Spouse, Child, Education, Address,
    ForeignLanguageSkill, BankAccount, CovidVaccination,
    PreviousParliamentaryHistory, Organization, Award,
    SocialService, SpecialPositionHistory, Publication,
    PersonalForeignTravel,
)


class _BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.TextInput, forms.NumberInput,
                               forms.DateInput, forms.EmailInput)):
                w.attrs.setdefault('class', 'form-control')
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('rows', '3')
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
                w.attrs.setdefault('data-select2', '')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')
            elif isinstance(w, forms.SelectMultiple):
                w.attrs.setdefault('class', 'form-select')
        normalize_date_fields(self)


class MPCreateForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = MP
        fields = ['mp_id', 'parliament', 'member_type', 'name_bn', 'name_en']


class MPGeneralForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = MP
        fields = [
            'name_bn', 'name_en',
            'father_name_bn', 'father_name_en',
            'mother_name_bn', 'mother_name_en',
            'dob', 'nid',
            'birth_district', 'gender',
            'home_district', 'marital_status',
            'nationality_bn', 'nationality_en', 'religion',
            'blood_group', 'professions_current',
            'professions_previous', 'tin',
            'professional_qualifications',
            'passport_number', 'passport_issue_date',
            'passport_issue_place', 'passport_expiry_date',
            'is_freedom_fighter', 'is_ff_child', 'is_ff_grandchild',
            'photo',
            'hobbies_bn', 'hobbies_en',
            'other_info_bn', 'other_info_en',
        ]
        widgets = {
            'dob':                  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_issue_date':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'professions_current':         forms.SelectMultiple(
                attrs={'data-select2': '', 'class': 'form-select', 'size': '4'}),
            'professions_previous':        forms.SelectMultiple(
                attrs={'data-select2': '', 'class': 'form-select', 'size': '4'}),
            'professional_qualifications': forms.SelectMultiple(
                attrs={'data-select2': '', 'class': 'form-select', 'size': '4'}),
        }


class ElectionInfoForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = ElectionInfo
        fields = [
            'parliament', 'constituency', 'party',
            'election_date', 'gazette_date', 'oath_date',
            'nomination_date', 'go_number', 'go_date',
            'times_elected',
        ]
        widgets = {
            'election_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gazette_date':    forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'oath_date':       forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nomination_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'go_date':         forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class SpouseForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = Spouse
        fields = [
            'name_bn', 'name_en',
            'dob', 'nid', 'mobile', 'passport_number',
            'marriage_date', 'tin',
            'profession', 'home_district', 'gender',
            'employer_details_bn', 'employer_details_en',
        ]
        widgets = {
            'dob':           forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'marriage_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class ChildForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = Child
        fields = ['serial', 'name_bn', 'name_en', 'dob', 'gender', 'profession',
                  'nid_or_birth_reg', 'mobile']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


# SSC / HSC / Diploma share ONE group pool ('school'); Graduation / Masters / PhD
# share the 'university' pool. Each level still stores its own value independently.
_LEVEL_GROUP_MAP = {
    'primary':    [],
    'secondary':  ['school', 'all'],
    'higher_sec': ['school', 'all'],
    'diploma':    ['school', 'all'],
    'bachelor':   ['university', 'all'],
    'masters':    ['university', 'all'],
    'phd':        ['university', 'all'],
    'other':      ['all'],
}


# Levels whose awarding body is an education board rather than a university.
_SCHOOL_LEVEL_TYPES = {'primary', 'secondary', 'higher_sec', 'diploma'}


def _keep_current(queryset, pk):
    """queryset, widened to still contain ``pk`` if it is stored but filtered out."""
    if pk and not queryset.filter(pk=pk).exists():
        model = queryset.model
        return model.objects.filter(
            models.Q(pk__in=queryset.values('pk')) | models.Q(pk=pk)
        ).order_by('name_bn')
    return queryset


class EducationSectionForm(_BootstrapMixin, forms.ModelForm):
    """One section of the fixed-section education page (Phase 17.11). Bound to a
    fixed `EducationLevel` (passed as `level`); the Examination (degree) dropdown
    is scoped to that level. Everything is optional — an untouched section saves
    nothing, and clearing a filled section deletes its record."""

    # Fields that count as "real" data when deciding whether to save/delete.
    DATA_FIELDS = (
        'degree_title', 'group', 'major_subject', 'board_affiliation',
        'institution', 'institution_other_bn', 'institution_other_en',
        'passing_year', 'course_duration',
        'result_type', 'division_result', 'gpa_value', 'gpa_out_of',
        'percentage', 'class_result', 'result_text',
    )

    class Meta:
        model  = Education
        fields = [
            'degree_title', 'group', 'major_subject', 'board_affiliation',
            'institution', 'institution_other_bn', 'institution_other_en',
            'passing_year', 'course_duration',
            'result_type', 'division_result', 'gpa_value', 'gpa_out_of',
            'percentage', 'class_result', 'result_text',
        ]

    def __init__(self, *args, level=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.level = level

        for f in self.fields.values():
            f.required = False

        applicable = _LEVEL_GROUP_MAP.get(level.level_type, ['all']) if level else ['all']
        if level is not None:
            self.fields['degree_title'].queryset = DegreeName.objects.filter(
                education_level=level, is_active=True).order_by('ordering', 'name_bn')
        self.fields['group'].queryset = (
            EducationGroup.objects.filter(applicable_to__in=applicable, is_active=True)
            .order_by('ordering', 'name_bn') if applicable else EducationGroup.objects.none())
        self.fields['major_subject'].queryset = EducationSubject.objects.filter(
            is_active=True).order_by('name_bn')

        # Institution pools are split by level (types come from Master Data):
        #   SSC / HSC / Diploma — the awarding body is an education *board*, and
        #     the institute is the school/college, so neither list may offer a
        #     university.
        #   Graduation and above — the awarding body is a university, so the
        #     list must not offer an education board.
        insts   = EducationInstitution.objects.filter(is_active=True).order_by('name_bn')
        if (level.level_type if level else 'other') in _SCHOOL_LEVEL_TYPES:
            board_qs = insts.filter(inst_type='board')
            inst_qs  = insts.exclude(inst_type__in=('board', 'university', 'foreign'))
        else:
            board_qs = insts.filter(inst_type__in=('university', 'foreign'))
            inst_qs  = board_qs
        # Never drop a value that is already stored — a mistyped master row would
        # otherwise be silently wiped the next time the section is saved.
        self.fields['institution'].queryset = _keep_current(
            inst_qs, self.instance.institution_id if self.instance else None)
        self.fields['board_affiliation'].queryset = _keep_current(
            board_qs, self.instance.board_affiliation_id if self.instance else None)
        self.fields['result_type'].queryset = ResultType.objects.filter(
            is_active=True).order_by('ordering')
        self.fields['division_result'].queryset = DivisionResult.objects.filter(
            is_active=True).order_by('ordering')

        # Result-type drives a JS cascade; keep it a plain <select> so the native
        # change event fires reliably (Select2 would swallow it). division_result
        # also stays native so it renders correctly inside a hidden result block.
        self.fields['result_type'].widget.attrs.update({
            'data-no-select2': '', 'class': 'form-select edu-result-type',
        })
        self.fields['division_result'].widget.attrs.update({'data-no-select2': ''})

    def has_data(self):
        """True if the user entered anything meaningful in this section."""
        cd = self.cleaned_data
        return any(cd.get(f) not in (None, '', []) for f in self.DATA_FIELDS)


class AddressForm(_BootstrapMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance if self.instance and self.instance.pk else None

        # Pre-filter district and upazila for existing instance
        if instance and instance.division_id:
            self.fields['district'].queryset = District.objects.filter(
                division_id=instance.division_id, is_active=True
            ).order_by('name_bn')
        else:
            self.fields['district'].queryset = District.objects.filter(
                is_active=True).order_by('name_bn')

        if instance and instance.district_id:
            self.fields['upazila'].queryset = Upazila.objects.filter(
                district_id=instance.district_id, is_active=True
            ).order_by('name_bn')
        else:
            self.fields['upazila'].queryset = Upazila.objects.filter(
                is_active=True).order_by('name_bn')

        # For POST — update querysets based on submitted values so validation passes
        if args and args[0]:
            prefix  = self.prefix or ''
            div_key  = f'{prefix}-division'  if prefix else 'division'
            dist_key = f'{prefix}-district' if prefix else 'district'
            div_id  = args[0].get(div_key)
            dist_id = args[0].get(dist_key)
            if div_id:
                self.fields['district'].queryset = District.objects.filter(
                    division_id=div_id, is_active=True).order_by('name_bn')
            if dist_id:
                self.fields['upazila'].queryset = Upazila.objects.filter(
                    district_id=dist_id, is_active=True).order_by('name_bn')

        # Add cascade onchange handlers using the resolved prefix
        prefix = self.prefix or ''
        if prefix:
            self.fields['division'].widget.attrs['onchange'] = (
                f"cascadeDistricts(this.value,'{prefix}')")
            self.fields['district'].widget.attrs['onchange'] = (
                f"cascadeUpazilas(this.value,'{prefix}')")

    class Meta:
        model  = Address
        fields = [
            'division', 'district', 'upazila',
            'pouroshova_union_bn', 'pouroshova_union_en',
            'address_detail_bn', 'address_detail_en',
            'postal_code',
            'telephone', 'mobile', 'alt_mobile', 'whatsapp',
            'email', 'personal_email',
        ]
        # address_detail_* are TextFields — keep them compact (2 rows, not 3).
        widgets = {
            'address_detail_bn': forms.Textarea(attrs={'rows': 2}),
            'address_detail_en': forms.Textarea(attrs={'rows': 2}),
        }


class ForeignLanguageSkillForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = ForeignLanguageSkill
        fields = ['language', 'proficiency', 'ordering']


class BankAccountForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = BankAccount
        fields = ['account_number', 'bank_name_bn', 'bank_name_en',
                  'branch_name_bn', 'branch_name_en', 'routing_number', 'account_type']


class CovidVaccinationForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model   = CovidVaccination
        fields  = ['dose_number', 'date', 'vaccine_name', 'center_name', 'certificate_number']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class PreviousParliamentaryHistoryForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model   = PreviousParliamentaryHistory
        fields  = ['assembly_name_bn', 'assembly_name_en', 'constituency_bn', 'constituency_en',
                   'from_date', 'to_date', 'remarks_bn', 'remarks_en', 'ordering']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class OrganizationForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model   = Organization
        fields  = ['name_bn', 'name_en', 'role_bn', 'role_en', 'from_date', 'to_date', 'ordering']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class AwardForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = Award
        fields = ['name_bn', 'name_en', 'year', 'awarded_by_bn', 'awarded_by_en', 'ordering']


class SocialServiceForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = SocialService
        fields = ['description_bn', 'description_en']


class SpecialPositionHistoryForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model   = SpecialPositionHistory
        fields  = ['parliament', 'role', 'from_date', 'to_date']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class PublicationForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model  = Publication
        fields = ['title_bn', 'title_en', 'pub_year', 'publisher_bn', 'publisher_en',
                  'pub_type', 'ordering']


class PersonalForeignTravelForm(_BootstrapMixin, forms.ModelForm):
    """Profile-entered travel. Only the country is required — see the model."""

    class Meta:
        model  = PersonalForeignTravel
        fields = ['country', 'purpose', 'from_date', 'to_date',
                  'note_bn', 'note_en', 'ordering']
        widgets = {
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date':   forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note_bn':   forms.Textarea(attrs={'rows': 2}),
            'note_en':   forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'] = BilingualChoiceField(
            queryset=Country.objects.filter(is_active=True).order_by('name_bn'),
            empty_label='-- দেশ নির্বাচন করুন / Select Country --',
            label='দেশ / Country',
        )
        self.fields['purpose'] = BilingualChoiceField(
            queryset=TravelPurpose.objects.filter(is_active=True).order_by('name_bn'),
            empty_label='-- উদ্দেশ্য (ঐচ্ছিক) / Purpose (optional) --',
            required=False,
            label='উদ্দেশ্য / Purpose',
        )
        for name in ('purpose', 'from_date', 'to_date', 'note_bn', 'note_en', 'ordering'):
            self.fields[name].required = False
        normalize_date_fields(self)
