from django import forms

from .models import (
    Division, District, Upazila,
    Religion, BloodGroup, MaritalStatus, Gender,
    Profession, ProfessionalQualification,
    EducationLevel, EducationGroup, EducationSubject, DegreeName,
    EducationInstitution, ResultType, DivisionResult,
    PoliticalParty, Ministry, MinisterType,
    StandingCommittee, CommitteePosition,
    GovernmentInstitution, InstitutionRole,
    Country, TravelType, TravelPurpose,
    ForeignLanguage, ProficiencyLevel,
)


class _BootstrapMixin:
    """Apply Bootstrap 5 widget classes to all form fields automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.TextInput, forms.NumberInput,
                               forms.EmailInput, forms.URLInput)):
                w.attrs.setdefault('class', 'form-control')
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault('class', 'form-control')
                w.attrs.setdefault('rows', '3')
            elif isinstance(w, forms.Select):
                w.attrs.setdefault('class', 'form-select')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')


def _make_form(model_class, fields):
    """Factory: returns a ModelForm subclass with Bootstrap widgets."""
    Meta = type('Meta', (), {'model': model_class, 'fields': fields})
    return type(
        f'{model_class.__name__}Form',
        (_BootstrapMixin, forms.ModelForm),
        {'Meta': Meta},
    )


# ── Simple standard forms ────────────────────────────────────────────────────

DivisionForm = _make_form(Division, ['name_bn', 'name_en', 'ordering'])
ReligionForm = _make_form(Religion, ['name_bn', 'name_en', 'ordering'])
BloodGroupForm = _make_form(BloodGroup, ['name_bn', 'name_en', 'ordering'])
MaritalStatusForm = _make_form(MaritalStatus, ['name_bn', 'name_en', 'ordering'])
GenderForm = _make_form(Gender, ['name_bn', 'name_en', 'ordering'])
EducationGroupForm = _make_form(EducationGroup, ['name_bn', 'name_en', 'applicable_to', 'ordering'])
ResultTypeForm = _make_form(ResultType, ['name_bn', 'name_en', 'result_format', 'ordering'])
DivisionResultForm = _make_form(DivisionResult, ['name_bn', 'name_en', 'ordering'])
MinistryForm = _make_form(Ministry, ['name_bn', 'name_en', 'ordering'])
MinisterTypeForm = _make_form(MinisterType, ['name_bn', 'name_en', 'ordering'])
StandingCommitteeForm = _make_form(StandingCommittee, ['name_bn', 'name_en', 'ordering'])
CommitteePositionForm = _make_form(CommitteePosition, ['name_bn', 'name_en', 'ordering'])
GovernmentInstitutionForm = _make_form(GovernmentInstitution, ['name_bn', 'name_en', 'ordering'])
InstitutionRoleForm = _make_form(InstitutionRole, ['name_bn', 'name_en', 'ordering'])
CountryForm = _make_form(Country, ['name_bn', 'name_en', 'ordering'])
TravelTypeForm = _make_form(TravelType, ['name_bn', 'name_en', 'ordering'])
TravelPurposeForm = _make_form(TravelPurpose, ['name_bn', 'name_en', 'ordering'])
ForeignLanguageForm = _make_form(ForeignLanguage, ['name_bn', 'name_en', 'ordering'])
ProficiencyLevelForm = _make_form(ProficiencyLevel, ['name_bn', 'name_en', 'ordering'])

# ── Forms with FK parents ────────────────────────────────────────────────────

DistrictForm = _make_form(District, ['division', 'name_bn', 'name_en', 'ordering'])
UpazilaForm = _make_form(Upazila, ['district', 'name_bn', 'name_en', 'ordering'])
EducationSubjectForm = _make_form(EducationSubject, ['name_bn', 'name_en', 'group', 'ordering'])
DegreeNameForm = _make_form(DegreeName, ['name_bn', 'name_en', 'short_name', 'education_level', 'ordering'])
EducationInstitutionForm = _make_form(
    EducationInstitution,
    ['name_bn', 'name_en', 'short_name', 'inst_type', 'district', 'ordering'],
)

# ── Forms with extra non-FK fields ──────────────────────────────────────────

ProfessionForm = _make_form(Profession, ['name_bn', 'name_en', 'category_bn', 'category_en', 'ordering'])
ProfessionalQualificationForm = _make_form(
    ProfessionalQualification,
    ['name_bn', 'name_en', 'short_bn', 'short_en', 'ordering'],
)
EducationLevelForm = _make_form(
    EducationLevel,
    ['name_bn', 'name_en', 'level_type', 'degree_order', 'ordering'],
)
PoliticalPartyForm = _make_form(PoliticalParty, ['name_bn', 'name_en', 'abbreviation', 'ordering'])
