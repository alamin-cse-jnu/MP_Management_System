from django.contrib import messages
from apps.accounts.mixins import perm_required
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.accounts.mixins import PermissionMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from .forms import (
    BloodGroupForm, CommitteePositionForm, CountryForm,
    DegreeNameForm, DistrictForm, DivisionForm, DivisionResultForm,
    EducationGroupForm, EducationInstitutionForm, EducationLevelForm,
    EducationSubjectForm, ForeignLanguageForm, GenderForm,
    InstitutionRoleForm, MaritalStatusForm,
    MinisterTypeForm, MinistryForm, PoliticalPartyForm,
    ProfessionForm, ProfessionalQualificationForm, ProficiencyLevelForm,
    ReligionForm, ResultTypeForm, StandingCommitteeForm,
    TravelPurposeForm, TravelTypeForm, UpazilaForm,
    VaccineNameForm, SpecialRoleTypeForm, PADesignationForm,
)
from .models import (
    BloodGroup, CommitteePosition, Country,
    DegreeName, District, Division, DivisionResult,
    EducationGroup, EducationInstitution, EducationLevel,
    EducationSubject, ForeignLanguage, Gender,
    InstitutionRole, MaritalStatus,
    MinisterType, Ministry, PoliticalParty,
    Profession, ProfessionalQualification, ProficiencyLevel,
    Religion, ResultType, StandingCommittee,
    TravelPurpose, TravelType, Upazila,
    VaccineName, SpecialRoleType, PADesignation,
)

# ── MASTER_SPECS ─────────────────────────────────────────────────────────────
# Each entry drives URL generation and generic CRUD views.
# extra_cols: additional columns shown before name_bn in the list table.
#   Each entry: {'label': 'বিভাগ', 'attr': 'division'}

MASTER_SPECS = [
    # Geography
    {
        'key': 'division',
        'model': Division,
        'form': DivisionForm,
        'title_bn': 'বিভাগ',
        'title_en': 'Divisions',
        'extra_cols': [],
    },
    {
        'key': 'district',
        'model': District,
        'form': DistrictForm,
        'title_bn': 'জেলা',
        'title_en': 'Districts',
        'extra_cols': [{'label': 'বিভাগ', 'attr': 'division'}],
    },
    {
        'key': 'upazila',
        'model': Upazila,
        'form': UpazilaForm,
        'title_bn': 'উপজেলা / থানা',
        'title_en': 'Upazilas',
        'extra_cols': [{'label': 'জেলা', 'attr': 'district'}],
    },
    # Personal
    {
        'key': 'religion',
        'model': Religion,
        'form': ReligionForm,
        'title_bn': 'ধর্ম',
        'title_en': 'Religions',
        'extra_cols': [],
    },
    {
        'key': 'blood-group',
        'model': BloodGroup,
        'form': BloodGroupForm,
        'title_bn': 'রক্তের গ্রুপ',
        'title_en': 'Blood Groups',
        'extra_cols': [],
    },
    {
        'key': 'marital-status',
        'model': MaritalStatus,
        'form': MaritalStatusForm,
        'title_bn': 'বৈবাহিক অবস্থা',
        'title_en': 'Marital Statuses',
        'extra_cols': [],
    },
    {
        'key': 'gender',
        'model': Gender,
        'form': GenderForm,
        'title_bn': 'লিঙ্গ',
        'title_en': 'Genders',
        'extra_cols': [],
    },
    # Professional
    {
        'key': 'profession',
        'model': Profession,
        'form': ProfessionForm,
        'title_bn': 'পেশা',
        'title_en': 'Professions',
        'extra_cols': [],
    },
    {
        'key': 'professional-qualification',
        'model': ProfessionalQualification,
        'form': ProfessionalQualificationForm,
        'title_bn': 'পেশাদার যোগ্যতা',
        'title_en': 'Professional Qualifications',
        'extra_cols': [],
    },
    # Education — the 7 education reference tables are NOT registered here.
    # They are managed together on the single-page Education manager
    # (`education_master` view + EDU_ENTITIES below), reached at /master/education/.
    # Political
    {
        'key': 'political-party',
        'model': PoliticalParty,
        'form': PoliticalPartyForm,
        'title_bn': 'রাজনৈতিক দল',
        'title_en': 'Political Parties',
        'extra_cols': [],
    },
    # Ministry
    {
        'key': 'ministry',
        'model': Ministry,
        'form': MinistryForm,
        'title_bn': 'মন্ত্রণালয়',
        'title_en': 'Ministries',
        'extra_cols': [],
    },
    {
        'key': 'minister-type',
        'model': MinisterType,
        'form': MinisterTypeForm,
        'title_bn': 'মন্ত্রীর ধরন',
        'title_en': 'Minister Types',
        'extra_cols': [],
    },
    # Committee
    {
        'key': 'standing-committee',
        'model': StandingCommittee,
        'form': StandingCommitteeForm,
        'title_bn': 'স্থায়ী কমিটি',
        'title_en': 'Standing Committees',
        'extra_cols': [],
    },
    {
        'key': 'committee-position',
        'model': CommitteePosition,
        'form': CommitteePositionForm,
        'title_bn': 'কমিটির পদ',
        'title_en': 'Committee Positions',
        'extra_cols': [],
    },
    # Institution
    {
        'key': 'institution-role',
        'model': InstitutionRole,
        'form': InstitutionRoleForm,
        'title_bn': 'প্রতিষ্ঠানের ভূমিকা',
        'title_en': 'Institution Roles',
        'extra_cols': [],
    },
    # Travel
    {
        'key': 'country',
        'model': Country,
        'form': CountryForm,
        'title_bn': 'দেশ',
        'title_en': 'Countries',
        'extra_cols': [],
    },
    {
        'key': 'travel-type',
        'model': TravelType,
        'form': TravelTypeForm,
        'title_bn': 'ভ্রমণের ধরন',
        'title_en': 'Travel Types',
        'extra_cols': [],
    },
    {
        'key': 'travel-purpose',
        'model': TravelPurpose,
        'form': TravelPurposeForm,
        'title_bn': 'ভ্রমণের উদ্দেশ্য',
        'title_en': 'Travel Purposes',
        'extra_cols': [],
    },
    # Language
    {
        'key': 'foreign-language',
        'model': ForeignLanguage,
        'form': ForeignLanguageForm,
        'title_bn': 'বিদেশি ভাষা',
        'title_en': 'Foreign Languages',
        'extra_cols': [],
    },
    {
        'key': 'proficiency-level',
        'model': ProficiencyLevel,
        'form': ProficiencyLevelForm,
        'title_bn': 'দক্ষতার মাত্রা',
        'title_en': 'Proficiency Levels',
        'extra_cols': [],
    },
    # COVID
    {
        'key': 'vaccine-name',
        'model': VaccineName,
        'form': VaccineNameForm,
        'title_bn': 'টিকার নাম',
        'title_en': 'Vaccine Names',
        'extra_cols': [],
    },
    # Special Positions
    {
        'key': 'special-role-type',
        'model': SpecialRoleType,
        'form': SpecialRoleTypeForm,
        'title_bn': 'বিশেষ পদের ধরন',
        'title_en': 'Special Role Types',
        'extra_cols': [],
    },
    # Office / PA-PS
    {
        'key': 'pa-designation',
        'model': PADesignation,
        'form': PADesignationForm,
        'title_bn': 'পিএ/পিএস পদবী',
        'title_en': 'PA/PS Designations',
        'extra_cols': [],
    },
]

# Quick lookup by key
SPEC_MAP = {s['key']: s for s in MASTER_SPECS}

# URL-safe key → Python identifier (replace hyphens)
def _url_name(key, suffix):
    return key.replace('-', '_') + '_' + suffix


# ── GENERIC BASE VIEWS ───────────────────────────────────────────────────────

class _MasterListView(PermissionMixin, LoginRequiredMixin, ListView):
    template_name = 'master/generic_list.html'
    paginate_by = 25
    _spec = None

    def get_queryset(self):
        spec = self._spec
        qs = spec['model'].objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q))
        status = self.request.GET.get('status', 'active')
        if status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'all':
            pass
        else:
            qs = qs.filter(is_active=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spec = self._spec
        uid = _url_name(spec['key'], '')   # e.g. 'division_'
        ctx.update({
            'title_bn': spec['title_bn'],
            'title_en': spec['title_en'],
            'extra_cols': spec['extra_cols'],
            'url_key': spec['key'],
            'create_url_name': f'master:{uid}create',
            'update_url_name': f'master:{uid}update',
            'toggle_url_name': f'master:{uid}toggle',
            'q': self.request.GET.get('q', ''),
            'status': self.request.GET.get('status', 'active'),
        })
        return ctx


class _MasterCreateView(PermissionMixin, LoginRequiredMixin, CreateView):
    template_name = 'master/generic_form.html'
    _spec = None

    def get_form_class(self):
        return self._spec['form']

    def get_success_url(self):
        return reverse('master:' + _url_name(self._spec['key'], 'list'))

    def form_valid(self, form):
        messages.success(self.request, f"'{form.instance}' সফলভাবে যোগ করা হয়েছে।")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spec = self._spec
        ctx.update({
            'title_bn': f'নতুন {spec["title_bn"]} যোগ করুন',
            'title_en': f'Add {spec["title_en"]}',
            'list_url': reverse('master:' + _url_name(spec['key'], 'list')),
            'is_create': True,
        })
        return ctx


class _MasterUpdateView(PermissionMixin, LoginRequiredMixin, UpdateView):
    template_name = 'master/generic_form.html'
    _spec = None

    def get_queryset(self):
        return self._spec['model'].objects.all()

    def get_form_class(self):
        return self._spec['form']

    def get_success_url(self):
        return reverse('master:' + _url_name(self._spec['key'], 'list'))

    def form_valid(self, form):
        messages.success(self.request, f"'{form.instance}' সফলভাবে আপডেট করা হয়েছে।")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spec = self._spec
        ctx.update({
            'title_bn': f'{spec["title_bn"]} সম্পাদনা',
            'title_en': f'Edit {spec["title_en"]}',
            'list_url': reverse('master:' + _url_name(spec['key'], 'list')),
            'is_create': False,
        })
        return ctx


class _MasterToggleView(PermissionMixin, LoginRequiredMixin, View):
    _spec = None

    def post(self, request, pk):
        spec = self._spec
        obj = get_object_or_404(spec['model'], pk=pk)
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        label = 'সক্রিয়' if obj.is_active else 'নিষ্ক্রিয়'
        messages.success(request, f'"{obj}" {label} করা হয়েছে।')
        list_url = reverse('master:' + _url_name(spec['key'], 'list'))
        query = request.GET.urlencode()
        return redirect(list_url + (f'?{query}' if query else ''))


# ── VIEW FACTORY ─────────────────────────────────────────────────────────────

def _build_views(spec):
    """Create concrete view classes for a given MASTER_SPEC entry."""
    key = spec['key']

    list_view = type(
        f'{key}_list',
        (_MasterListView,),
        {'_spec': spec},
    ).as_view()

    create_view = type(
        f'{key}_create',
        (_MasterCreateView,),
        {'_spec': spec},
    ).as_view()

    update_view = type(
        f'{key}_update',
        (_MasterUpdateView,),
        {'_spec': spec},
    ).as_view()

    toggle_view = type(
        f'{key}_toggle',
        (_MasterToggleView,),
        {'_spec': spec},
    ).as_view()

    return list_view, create_view, update_view, toggle_view


# Build all views at module load
_VIEWS = {spec['key']: _build_views(spec) for spec in MASTER_SPECS}


def get_views(key):
    return _VIEWS[key]


# ── EDUCATION MASTER — single-page manager ───────────────────────────────────
# All 7 education reference tables managed on ONE page (/master/education/) with a
# left tab-rail + inline HTMX add/edit/toggle. Reuses the existing master forms;
# no dedicated forms/models. `cols` = extra columns shown after name_bn/name_en.

EDU_ENTITIES = [
    {'key': 'degree-name', 'model': DegreeName, 'form': DegreeNameForm,
     'title_bn': 'পরীক্ষা / ডিগ্রি', 'title_en': 'Examinations', 'icon': 'bi-mortarboard-fill',
     'hint_bn': 'স্তর-ভিত্তিক পরীক্ষা/ডিগ্রির নাম (এসএসসি, এইচএসসি, বিএসসি…)।',
     'hint_en': 'Level-scoped examination / degree names (SSC, HSC, BSc…).',
     'cols': [{'label_bn': 'স্তর', 'label_en': 'Level', 'attr': 'education_level'},
              {'label_bn': 'সংক্ষিপ্ত', 'label_en': 'Short', 'attr': 'short_name'}]},
    {'key': 'education-group', 'model': EducationGroup, 'form': EducationGroupForm,
     'title_bn': 'গ্রুপ', 'title_en': 'Groups', 'icon': 'bi-diagram-3-fill',
     'hint_bn': 'বিজ্ঞান/বাণিজ্য/মানবিক — স্কুল বা বিশ্ববিদ্যালয় পুলে প্রযোজ্য।',
     'hint_en': 'Science/Business/Arts — tagged to the school or university pool.',
     'cols': [{'label_bn': 'প্রযোজ্য', 'label_en': 'Applies to', 'attr': 'get_applicable_to_display'}]},
    {'key': 'education-subject', 'model': EducationSubject, 'form': EducationSubjectForm,
     'title_bn': 'বিষয়', 'title_en': 'Subjects', 'icon': 'bi-book-fill',
     'hint_bn': 'বিষয়সমূহ — ঐচ্ছিকভাবে গ্রুপের সাথে সংযুক্ত।',
     'hint_en': 'Subjects — optionally linked to a group.',
     'cols': [{'label_bn': 'গ্রুপ', 'label_en': 'Group', 'attr': 'group'}]},
    {'key': 'education-institution', 'model': EducationInstitution, 'form': EducationInstitutionForm,
     'title_bn': 'প্রতিষ্ঠান', 'title_en': 'Institutions', 'icon': 'bi-bank2',
     'hint_bn': 'বোর্ড ও বিশ্ববিদ্যালয় — ধরন অনুযায়ী।',
     'hint_en': 'Boards & universities — grouped by type.',
     'cols': [{'label_bn': 'ধরন', 'label_en': 'Type', 'attr': 'get_inst_type_display'},
              {'label_bn': 'জেলা', 'label_en': 'District', 'attr': 'district'}]},
    {'key': 'result-type', 'model': ResultType, 'form': ResultTypeForm,
     'title_bn': 'ফলাফলের ধরন', 'title_en': 'Result Types', 'icon': 'bi-percent',
     'hint_bn': 'জিপিএ/সিজিপিএ/বিভাগ/শতকরা ইত্যাদি।',
     'hint_en': 'GPA/CGPA/Division/Percentage etc.',
     'cols': [{'label_bn': 'ফরম্যাট', 'label_en': 'Format', 'attr': 'get_result_format_display'}]},
    {'key': 'division-result', 'model': DivisionResult, 'form': DivisionResultForm,
     'title_bn': 'বিভাগ ভিত্তিক ফলাফল', 'title_en': 'Division Results', 'icon': 'bi-list-ol',
     'hint_bn': 'প্রথম/দ্বিতীয়/তৃতীয় বিভাগ ইত্যাদি।',
     'hint_en': '1st/2nd/3rd Division etc.',
     'cols': []},
    {'key': 'education-level', 'model': EducationLevel, 'form': EducationLevelForm,
     'title_bn': 'শিক্ষাগত স্তর', 'title_en': 'Levels', 'icon': 'bi-layers-fill', 'advanced': True,
     'hint_bn': 'পূর্বনির্ধারিত ৬টি স্তর — সাধারণত পরিবর্তনের প্রয়োজন নেই।',
     'hint_en': 'The 6 seeded levels — rarely need changing.',
     'cols': [{'label_bn': 'ধরন', 'label_en': 'Type', 'attr': 'get_level_type_display'},
              {'label_bn': 'ক্রম', 'label_en': 'Order', 'attr': 'degree_order'}]},
]
EDU_MAP = {e['key']: e for e in EDU_ENTITIES}


def _edu_param(request, name, default=''):
    """Filter params arrive in GET (filter/tab requests) or POST (save/toggle,
    carried via hx-include) — check both so the filter survives every action."""
    return request.POST.get(name, request.GET.get(name, default))


def _edu_queryset(spec, request):
    qs = spec['model'].objects.all()
    q = _edu_param(request, 'q').strip()
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q))
    status = _edu_param(request, 'status', 'active')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    return qs


def _edu_panel_ctx(request, spec, **extra):
    ctx = {
        'spec': spec,
        'objects': _edu_queryset(spec, request),
        'q': _edu_param(request, 'q'),
        'status': _edu_param(request, 'status', 'active'),
        'form': None, 'open_form': False, 'saved': None, 'editing_pk': None,
    }
    ctx.update(extra)
    return ctx


def _render_edu_panel(request, spec, **extra):
    return render(request, 'master/partials/edu_panel.html',
                  _edu_panel_ctx(request, spec, **extra))


@perm_required
def education_master(request):
    """Single page: left tab-rail of the 7 education tables + inline HTMX CRUD."""
    entities = [{**e, 'count': e['model'].objects.filter(is_active=True).count()}
                for e in EDU_ENTITIES]
    spec = EDU_MAP.get(request.GET.get('tab'), EDU_ENTITIES[0])
    ctx = _edu_panel_ctx(request, spec)
    ctx.update({'entities': entities, 'active_key': spec['key']})
    return render(request, 'master/education_master.html', ctx)


@perm_required
def education_panel(request, key):
    spec = EDU_MAP.get(key)
    if not spec:
        raise Http404
    return _render_edu_panel(request, spec)


@perm_required
def education_form(request, key, pk=None):
    """GET → open the inline add/edit form; POST → validate + save."""
    spec = EDU_MAP.get(key)
    if not spec:
        raise Http404
    instance = get_object_or_404(spec['model'], pk=pk) if pk else None
    if request.method == 'POST':
        form = spec['form'](request.POST, instance=instance)
        if form.is_valid():
            obj = form.save()
            return _render_edu_panel(request, spec, saved=obj)
        return _render_edu_panel(request, spec, form=form, open_form=True, editing_pk=pk)
    return _render_edu_panel(request, spec, form=spec['form'](instance=instance),
                             open_form=True, editing_pk=pk)


@perm_required
@require_POST
def education_toggle(request, key, pk):
    spec = EDU_MAP.get(key)
    if not spec:
        raise Http404
    obj = get_object_or_404(spec['model'], pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    return _render_edu_panel(request, spec, saved=obj)


# ── HTMX PARTIAL VIEWS ───────────────────────────────────────────────────────

@perm_required
def master_home(request):
    from django.urls import reverse, NoReverseMatch

    def _item(name_bn, name_en, url_key):
        # Tolerant: a retired master model (its URL removed) must not 500 the
        # whole overview — skip any item whose URL no longer resolves.
        try:
            url = reverse(f'master:{url_key}')
        except NoReverseMatch:
            return None
        return {'name_bn': name_bn, 'name_en': name_en, 'url': url}

    sections = [
        {'title_bn': 'ভূগোল', 'title_en': 'Geography', 'icon': 'bi-geo-alt-fill', 'items': [
            _item('বিভাগ', 'Divisions', 'division_list'),
            _item('জেলা', 'Districts', 'district_list'),
            _item('উপজেলা', 'Upazilas', 'upazila_list'),
        ]},
        {'title_bn': 'ব্যক্তিগত', 'title_en': 'Personal', 'icon': 'bi-person-fill', 'items': [
            _item('ধর্ম', 'Religions', 'religion_list'),
            _item('রক্তের গ্রুপ', 'Blood Groups', 'blood_group_list'),
            _item('বৈবাহিক অবস্থা', 'Marital Status', 'marital_status_list'),
            _item('লিঙ্গ', 'Genders', 'gender_list'),
        ]},
        {'title_bn': 'পেশাদার', 'title_en': 'Professional', 'icon': 'bi-briefcase-fill', 'items': [
            _item('পেশা', 'Professions', 'profession_list'),
            _item('পেশাদার যোগ্যতা', 'Professional Qualifications', 'professional_qualification_list'),
        ]},
        {'title_bn': 'শিক্ষা', 'title_en': 'Education', 'icon': 'bi-mortarboard-fill', 'items': [
            _item('শিক্ষা মাস্টার ডেটা (সব একসাথে)', 'Education Master Data (all-in-one)', 'education_master'),
        ]},
        {'title_bn': 'রাজনৈতিক', 'title_en': 'Political', 'icon': 'bi-flag-fill', 'items': [
            _item('রাজনৈতিক দল', 'Political Parties', 'political_party_list'),
        ]},
        {'title_bn': 'মন্ত্রণালয়', 'title_en': 'Ministry', 'icon': 'bi-building-fill', 'items': [
            _item('মন্ত্রণালয়', 'Ministries', 'ministry_list'),
            _item('মন্ত্রীর ধরন', 'Minister Types', 'minister_type_list'),
        ]},
        {'title_bn': 'কমিটি', 'title_en': 'Committee', 'icon': 'bi-people-fill', 'items': [
            _item('স্থায়ী কমিটি', 'Standing Committees', 'standing_committee_list'),
            _item('কমিটির পদ', 'Committee Positions', 'committee_position_list'),
        ]},
        {'title_bn': 'প্রতিষ্ঠান', 'title_en': 'Institution', 'icon': 'bi-building', 'items': [
            _item('প্রতিষ্ঠানের ভূমিকা', 'Institution Roles', 'institution_role_list'),
        ]},
        {'title_bn': 'ভ্রমণ', 'title_en': 'Travel', 'icon': 'bi-globe', 'items': [
            _item('দেশ', 'Countries', 'country_list'),
            _item('ভ্রমণের ধরন', 'Travel Types', 'travel_type_list'),
            _item('ভ্রমণের উদ্দেশ্য', 'Travel Purposes', 'travel_purpose_list'),
        ]},
        {'title_bn': 'ভাষা', 'title_en': 'Language', 'icon': 'bi-translate', 'items': [
            _item('বিদেশি ভাষা', 'Foreign Languages', 'foreign_language_list'),
            _item('দক্ষতার মাত্রা', 'Proficiency Levels', 'proficiency_level_list'),
        ]},
        {'title_bn': 'অফিস / পিএ-পিএস', 'title_en': 'Office / PA-PS', 'icon': 'bi-person-badge-fill', 'items': [
            _item('পিএ/পিএস পদবী', 'PA/PS Designations', 'pa_designation_list'),
        ]},
    ]
    # Drop any skipped (None) items and now-empty sections.
    for sec in sections:
        sec['items'] = [it for it in sec['items'] if it]
    sections = [sec for sec in sections if sec['items']]
    return render(request, 'master/home.html', {'sections': sections})


def district_options(request):
    division_id = request.GET.get('division_id', '')
    qs = District.objects.none()
    if division_id:
        qs = District.objects.filter(
            division_id=division_id, is_active=True
        ).order_by('name_bn')
    return render(request, 'partials/options.html', {'items': qs})


def upazila_options(request):
    district_id = request.GET.get('district_id', '')
    qs = Upazila.objects.none()
    if district_id:
        qs = Upazila.objects.filter(
            district_id=district_id, is_active=True
        ).order_by('name_bn')
    return render(request, 'partials/options.html', {'items': qs})


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


def education_level_cascade(request):
    """HTMX: education level changes → return filtered group + degree_title selects."""
    level_id = request.GET.get('education_level', '')

    show_group = True
    groups = EducationGroup.objects.filter(is_active=True).order_by('ordering', 'name_bn')
    degrees = DegreeName.objects.none()

    if level_id:
        try:
            level = EducationLevel.objects.get(pk=level_id)
            applicable = _LEVEL_GROUP_MAP.get(level.level_type, ['all'])
            show_group = bool(applicable) and level.level_type != 'primary'
            if applicable:
                groups = EducationGroup.objects.filter(
                    applicable_to__in=applicable, is_active=True
                ).order_by('ordering', 'name_bn')
            else:
                groups = EducationGroup.objects.none()
            degrees = DegreeName.objects.filter(
                education_level_id=level_id, is_active=True
            ).order_by('ordering', 'name_bn')
        except EducationLevel.DoesNotExist:
            pass

    return render(request, 'partials/edu_level_cascade.html', {
        'groups': groups,
        'degrees': degrees,
        'show_group': show_group,
    })


def subject_options(request):
    """HTMX: group changes → return filtered subject options."""
    group_id = request.GET.get('group', '')
    qs = EducationSubject.objects.none()
    if group_id:
        qs = EducationSubject.objects.filter(
            group_id=group_id, is_active=True
        ).order_by('ordering', 'name_bn')
    return render(request, 'partials/subject_options.html', {'items': qs})


def result_fields(request):
    """HTMX: result_type changes → return relevant result input fields."""
    result_type_id = request.GET.get('result_type', '')
    result_format = None

    if result_type_id:
        try:
            rt = ResultType.objects.get(pk=result_type_id)
            result_format = rt.result_format
        except ResultType.DoesNotExist:
            pass

    division_results = DivisionResult.objects.all().order_by('ordering')

    return render(request, 'partials/education_result_fields.html', {
        'result_format': result_format,
        'division_results': division_results,
    })
