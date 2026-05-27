from django import forms

from apps.master.models import (
    DegreeName, District, EducationGroup, EducationLevel, EducationSubject, Upazila,
)
from .models import (
    MP, ElectionInfo, Spouse, Child, Education, Address,
    ForeignLanguageSkill, BankAccount, CovidVaccination,
    PreviousParliamentaryHistory, Organization, Award,
    SocialService, SpecialPositionHistory, Publication,
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
            'nationality', 'religion',
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
            'dob', 'nid',
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
                  'nid_or_birth_reg']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


_LEVEL_GROUP_MAP = {
    'primary':    [],
    'secondary':  ['secondary', 'all'],
    'higher_sec': ['higher_sec', 'all'],
    'diploma':    ['all'],
    'bachelor':   ['university', 'all'],
    'masters':    ['university', 'all'],
    'phd':        ['university', 'all'],
    'other':      ['all'],
}


class EducationForm(_BootstrapMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance if self.instance and self.instance.pk else None

        # Pre-filter for edit mode
        if instance:
            if instance.education_level_id:
                applicable = _LEVEL_GROUP_MAP.get(
                    instance.education_level.level_type, ['all'])
                if applicable:
                    self.fields['group'].queryset = EducationGroup.objects.filter(
                        applicable_to__in=applicable, is_active=True
                    ).order_by('ordering', 'name_bn')
                else:
                    self.fields['group'].queryset = EducationGroup.objects.none()
                self.fields['degree_title'].queryset = DegreeName.objects.filter(
                    education_level_id=instance.education_level_id, is_active=True
                ).order_by('ordering', 'name_bn')
            if instance.group_id:
                self.fields['major_subject'].queryset = EducationSubject.objects.filter(
                    group_id=instance.group_id, is_active=True
                ).order_by('ordering', 'name_bn')

        # Re-filter from POST data so validation passes
        if args and args[0]:
            level_id = args[0].get('education_level')
            group_id = args[0].get('group')
            if level_id:
                self.fields['degree_title'].queryset = DegreeName.objects.filter(
                    education_level_id=level_id, is_active=True
                ).order_by('ordering', 'name_bn')
                try:
                    lvl = EducationLevel.objects.get(pk=level_id)
                    applicable = _LEVEL_GROUP_MAP.get(lvl.level_type, ['all'])
                    if applicable:
                        self.fields['group'].queryset = EducationGroup.objects.filter(
                            applicable_to__in=applicable, is_active=True
                        ).order_by('ordering', 'name_bn')
                    else:
                        self.fields['group'].queryset = EducationGroup.objects.none()
                except EducationLevel.DoesNotExist:
                    pass
            if group_id:
                self.fields['major_subject'].queryset = EducationSubject.objects.filter(
                    group_id=group_id, is_active=True
                ).order_by('ordering', 'name_bn')

        # HTMX cascade attributes
        self.fields['education_level'].widget.attrs.update({
            'hx-get': '/master/htmx/education-level-cascade/',
            'hx-trigger': 'change',
            'hx-target': '#edu-cascade-block',
        })
        self.fields['group'].widget.attrs.update({
            'hx-get': '/master/htmx/subject-options/',
            'hx-trigger': 'change',
            'hx-target': '#id_major_subject',
            'hx-swap': 'innerHTML',
        })
        self.fields['result_type'].widget.attrs.update({
            'hx-get': '/master/htmx/result-fields/',
            'hx-trigger': 'change',
            'hx-target': '#result-fields-block',
        })

    class Meta:
        model  = Education
        fields = [
            'education_level', 'group', 'degree_title', 'major_subject',
            'institution', 'institution_other_bn', 'institution_other_en',
            'board_affiliation', 'passing_year',
            'result_type', 'division_result',
            'gpa_value', 'gpa_out_of', 'percentage',
            'class_result', 'result_text',
            'ordering',
        ]


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
            'telephone', 'mobile', 'alt_mobile', 'whatsapp', 'email',
        ]


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
