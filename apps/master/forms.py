from django import forms

from utils.form_dates import normalize_date_fields
from utils.master_merge import NAME_SCOPE, clean_name, find_similar

from .models import (
    Division, District, Upazila,
    Religion, BloodGroup, MaritalStatus, Gender,
    Profession, ProfessionalQualification,
    EducationLevel, EducationGroup, EducationSubject, DegreeName,
    EducationInstitution, ResultType, DivisionResult, ClassResult,
    PoliticalParty, Ministry, MinisterType,
    StandingCommittee, CommitteePosition,
    InstitutionRole,
    Country, TravelType, TravelPurpose,
    ForeignLanguage, ProficiencyLevel,
    VaccineName, SpecialRoleType, PADesignation,
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
                w.attrs.setdefault('data-select2', '')
            elif isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('class', 'form-check-input')
        normalize_date_fields(self)


# Text fields that name the thing and therefore have to be canonical before
# they are stored or compared. `ঢাকা  বোর্ড` reached prod with two spaces and
# never matched `ঢাকা বোর্ড` again.
_NAME_FIELDS = ('name_bn', 'name_en', 'short_name', 'short_bn', 'short_en',
                'abbreviation', 'category_bn', 'category_en')


class _DedupeMixin:
    """Normalise the name fields and refuse a row that already exists.

    Every master table is written through exactly one ModelForm, so this is the
    one place that can stop a duplicate being created at all — cleaning up
    afterwards means repointing MP records, which is far more expensive than
    refusing the save. Near-misses are not blocked here (no string metric can
    tell `মেডিসিন` from `চিকিৎসাবিজ্ঞান`); they are surfaced as a live warning
    while the operator types — see `master:name_check`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Captured before binding: `construct_instance()` overwrites the
        # instance with the posted values, so after `is_valid()` a
        # new-vs-old comparison would compare a value with itself.
        self._original_names = (
            (self.instance.name_bn, getattr(self.instance, 'name_en', ''))
            if self.instance.pk else None)

    def _prior_collisions(self):
        """Rows this instance ALREADY collided with before the edit."""
        if not self._original_names:
            return set()
        model = self._meta.model
        scope_field = NAME_SCOPE.get(model._meta.label)
        scope = getattr(self.instance, scope_field) if scope_field else None
        exact, _ = find_similar(model, name_bn=self._original_names[0],
                                name_en=self._original_names[1],
                                exclude_pk=self.instance.pk, scope=scope)
        return {r.pk for r in exact}

    def clean(self):
        cleaned = super().clean()
        for name in _NAME_FIELDS:
            if name in cleaned and isinstance(cleaned.get(name), str):
                cleaned[name] = clean_name(cleaned[name])

        model = self._meta.model
        scope_field = NAME_SCOPE.get(model._meta.label)
        scope = cleaned.get(scope_field[:-3]) if scope_field else None
        exact, _near = find_similar(
            model,
            name_bn=cleaned.get('name_bn', ''),
            name_en=cleaned.get('name_en', ''),
            exclude_pk=self.instance.pk,
            scope=scope,
        )
        # An edit that does not make things worse must still go through. Prod
        # already carries duplicates, and refusing to let anyone fix the
        # ordering or the English half of one until it is merged would be a
        # new way of being stuck.
        if exact and {r.pk for r in exact} <= self._prior_collisions():
            return cleaned

        if exact:
            hit = exact[0]
            # An inactive match is the trap worth naming: the row is invisible
            # in the list, so the operator adds it again and the table now has
            # two, one of which still holds MP data.
            state_bn = 'সক্রিয়' if hit.is_active else 'নিষ্ক্রিয় (তালিকায় দেখা যাচ্ছে না)'
            state_en = 'active' if hit.is_active else 'inactive — hidden from the list'
            advice_bn = ('' if hit.is_active
                         else ' নতুন না করে সেটিকেই আবার সক্রিয় করুন।')
            advice_en = ('' if hit.is_active
                         else ' Reactivate that row instead of adding a new one.')
            raise forms.ValidationError(
                f'এটি ইতিমধ্যে আছে — "{hit.name_bn}" (আইডি {hit.pk}, {state_bn})।'
                f'{advice_bn} / Already exists as "{hit.name_en or hit.name_bn}" '
                f'(id {hit.pk}, {state_en}).{advice_en}'
            )
        return cleaned


def _make_form(model_class, fields):
    """Factory: returns a ModelForm subclass with Bootstrap widgets."""
    Meta = type('Meta', (), {'model': model_class, 'fields': fields})
    return type(
        f'{model_class.__name__}Form',
        (_DedupeMixin, _BootstrapMixin, forms.ModelForm),
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
ClassResultForm = _make_form(ClassResult, ['name_bn', 'name_en', 'ordering'])
MinistryForm = _make_form(Ministry, ['name_bn', 'name_en', 'ordering'])
MinisterTypeForm = _make_form(MinisterType, ['name_bn', 'name_en', 'ordering'])
StandingCommitteeForm = _make_form(StandingCommittee, ['name_bn', 'name_en', 'ordering'])
CommitteePositionForm = _make_form(CommitteePosition, ['name_bn', 'name_en', 'ordering'])
InstitutionRoleForm = _make_form(InstitutionRole, ['name_bn', 'name_en', 'ordering'])
CountryForm = _make_form(Country, ['name_bn', 'name_en', 'ordering'])
TravelTypeForm = _make_form(TravelType, ['name_bn', 'name_en', 'ordering'])
TravelPurposeForm = _make_form(TravelPurpose, ['name_bn', 'name_en', 'ordering'])
ForeignLanguageForm = _make_form(ForeignLanguage, ['name_bn', 'name_en', 'ordering'])
ProficiencyLevelForm = _make_form(ProficiencyLevel, ['name_bn', 'name_en', 'ordering'])
VaccineNameForm = _make_form(VaccineName, ['name_bn', 'name_en', 'ordering'])
# The unique flag is what stops a second sitting Speaker, so it has to be
# editable — a hand-added office defaults to "many holders allowed".
SpecialRoleTypeForm = _make_form(
    SpecialRoleType, ['name_bn', 'name_en', 'is_unique_per_parliament', 'ordering'])
PADesignationForm = _make_form(PADesignation, ['name_bn', 'name_en', 'ordering'])

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
