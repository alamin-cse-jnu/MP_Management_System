import os
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.mixins import perm_required
from apps.parliament.models import Parliament
from apps.ministry.models import MinistryAssignment
from apps.committee.models import CommitteeAssignment
from apps.travel.models import ForeignTourParticipant
from apps.office.models import ParliamentOfficeAddress
from .forms import (
    MPCreateForm, MPGeneralForm, ElectionInfoForm,
    SpouseForm, ChildForm, EducationSectionForm, AddressForm,
    ForeignLanguageSkillForm, BankAccountForm, CovidVaccinationForm,
    PreviousParliamentaryHistoryForm, OrganizationForm, AwardForm,
    SocialServiceForm, SpecialPositionHistoryForm, PublicationForm,
)
from apps.master.models import EducationLevel, ResultType
from .models import (
    MP, ElectionInfo, Spouse, Child, Education, Address,
    ForeignLanguageSkill, BankAccount, CovidVaccination,
    PreviousParliamentaryHistory, Organization, Award,
    SocialService, SpecialPositionHistory, Publication,
    MPSyncConflict,
)
from . import api_sync


# ── SHARED CONTEXT ────────────────────────────────────────────────────────────

_TAB_LIST = [
    ('tab-general',      '১. সাধারণ তথ্য'),
    ('tab-election',     '২. নির্বাচন'),
    ('tab-spouse',       '৩. স্বামী/স্ত্রী'),
    ('tab-children',     '৪. সন্তান'),
    ('tab-education',    '৫. শিক্ষা'),
    ('tab-address',      '৬. ঠিকানা'),
    ('tab-language',     '৭. বিদেশি ভাষা'),
    ('tab-bank',         '৮. ব্যাংক'),
    ('tab-covid',        '৯. কোভিড'),
    ('tab-ministry',     '১০. মন্ত্রণালয়'),
    ('tab-committee',    '১১. কমিটি'),
    ('tab-history',      '১২. পূর্ববর্তী ইতিহাস'),
    ('tab-organization', '১৩. সংগঠন'),
    ('tab-award',        '১৪. পুরস্কার'),
    ('tab-social',       '১৫. সমাজ সেবা'),
    ('tab-special',      '১৬. বিশেষ পদ'),
    ('tab-publication',  '১৭. প্রকাশনা'),
    ('tab-travel',       '১৮. বিদেশ ভ্রমণ'),
]
_COMING_SOON = []


def _detail_ctx(mp, **override):
    """Build context for mp_detail; pass keyword overrides to replace defaults."""
    election_info = ElectionInfo.objects.filter(mp=mp, parliament=mp.parliament).first()
    addresses     = {a.address_type: a for a in mp.addresses.all()}
    ei_initial    = {} if election_info else {'parliament': mp.parliament}

    try:
        social_service = mp.social_service
    except SocialService.DoesNotExist:
        social_service = None

    ctx = {
        'mp':            mp,
        'election_info': election_info,
        'spouses':       mp.spouses.all(),
        'children':      mp.children.all(),
        'educations':    mp.educations.select_related(
            'education_level', 'degree_title', 'institution', 'result_type').all(),
        'addresses':     addresses,

        # Sections 7–17
        'language_skills':   mp.language_skills.select_related('language', 'proficiency').all(),
        'bank_accounts':     mp.bank_accounts.all(),
        'covid_vaccinations': mp.covid_vaccinations.select_related('vaccine_name').all(),
        'parl_histories':    mp.parliamentary_histories.all(),
        'organizations':     mp.organizations.all(),
        'awards':            mp.awards.all(),
        'social_service':    social_service,
        'special_positions': mp.special_positions.select_related('parliament', 'role').all(),
        'publications':      mp.publications.all(),

        # Sections 10–11 (ministry/committee modules)
        'ministry_assignments': MinistryAssignment.objects.filter(mp=mp).select_related(
            'parliament', 'ministry', 'minister_type'),
        'committee_assignments': CommitteeAssignment.objects.filter(mp=mp).select_related(
            'parliament', 'committee', 'position'),

        # Section 18 (travel module) + office
        'travel_participations': ForeignTourParticipant.objects.filter(mp=mp).select_related(
            'tour', 'tour__tour_type', 'tour__purpose').prefetch_related('tour__countries__country'),
        'office_address': getattr(mp, 'office_address', None),

        'active_tab':       'tab-general',
        'tab_list':         _TAB_LIST,
        'coming_soon_tabs': _COMING_SOON,

        'general_form':   MPGeneralForm(instance=mp),
        'election_form':  ElectionInfoForm(instance=election_info, initial=ei_initial),
        'present_form':   AddressForm(
            instance=addresses.get('present'), prefix='present',
            initial={'address_type': 'present'}),
        'permanent_form': AddressForm(
            instance=addresses.get('permanent'), prefix='permanent',
            initial={'address_type': 'permanent'}),
        'dhaka_form':     AddressForm(
            instance=addresses.get('dhaka'), prefix='dhaka',
            initial={'address_type': 'dhaka'}),
    }
    ctx.update(override)
    return ctx


# ── MP LIST ───────────────────────────────────────────────────────────────────

@perm_required
def mp_list(request):
    qs = MP.objects.select_related('parliament').prefetch_related(
        Prefetch(
            'election_infos',
            queryset=ElectionInfo.objects.select_related('constituency', 'party'),
        )
    )

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name_bn__icontains=q) | Q(name_en__icontains=q) | Q(mp_id__icontains=q)
        )

    parliament_id = request.GET.get('parliament', '')
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    else:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            qs = qs.filter(parliament=active_p)
            parliament_id = str(active_p.pk)

    member_type = request.GET.get('member_type', '')
    if member_type:
        qs = qs.filter(member_type=member_type)

    status = request.GET.get('status', 'active')
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status != 'all':
        qs = qs.filter(is_active=True)

    paginator = Paginator(qs.order_by('mp_id'), 25)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'mp/mp_list.html', {
        'page_obj':     page,
        'q':            q,
        'parliament_id': parliament_id,
        'parliaments':  Parliament.objects.order_by('-ordinal'),
        'member_type':  member_type,
        'status':       status,
    })


# ── MP CREATE ─────────────────────────────────────────────────────────────────

@perm_required
def mp_create(request):
    active_p = Parliament.objects.filter(is_active=True).first()
    form = MPCreateForm(request.POST or None, initial={'parliament': active_p} if active_p else {})
    if form.is_valid():
        mp = form.save(commit=False)
        mp.created_by = request.user
        mp.updated_by = request.user
        mp.save()
        messages.success(request, f'"{mp.name_bn}" তৈরি হয়েছে। বাকি তথ্য পূরণ করুন।')
        return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-election')
    return render(request, 'mp/mp_create.html', {'form': form})


# ── MP DETAIL ─────────────────────────────────────────────────────────────────

@perm_required
def mp_detail(request, pk):
    mp  = get_object_or_404(MP, pk=pk)
    ctx = _detail_ctx(mp, active_tab=request.GET.get('active', 'tab-general'))
    return render(request, 'mp/mp_detail.html', ctx)


# ── SECTION SAVES ─────────────────────────────────────────────────────────────

@perm_required
@require_POST
def mp_section_general(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = MPGeneralForm(request.POST, request.FILES, instance=mp)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        form.save_m2m()
        messages.success(request, 'সাধারণ তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-general')
    ctx = _detail_ctx(mp, general_form=form, active_tab='tab-general')
    return render(request, 'mp/mp_detail.html', ctx)


@perm_required
@require_POST
def mp_section_election(request, pk):
    mp       = get_object_or_404(MP, pk=pk)
    existing = ElectionInfo.objects.filter(mp=mp, parliament=mp.parliament).first()
    form     = ElectionInfoForm(request.POST, instance=existing)
    if form.is_valid():
        ei = form.save(commit=False)
        ei.mp = mp
        if not ei.parliament_id:
            ei.parliament = mp.parliament
        ei.save()
        messages.success(request, 'নির্বাচন সংক্রান্ত তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-election')
    ctx = _detail_ctx(mp, election_form=form, active_tab='tab-election')
    return render(request, 'mp/mp_detail.html', ctx)


@perm_required
@require_POST
def mp_address_save(request, pk, atype):
    mp = get_object_or_404(MP, pk=pk)
    if atype not in ('present', 'permanent', 'dhaka'):
        raise Http404
    existing = Address.objects.filter(mp=mp, address_type=atype).first()
    form     = AddressForm(request.POST, instance=existing, prefix=atype)
    if form.is_valid():
        addr = form.save(commit=False)
        addr.mp           = mp
        addr.address_type = atype
        addr.save()
        messages.success(request, 'ঠিকানা সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-address')
    ctx = _detail_ctx(mp, **{f'{atype}_form': form}, active_tab='tab-address')
    return render(request, 'mp/mp_detail.html', ctx)


# ── SPOUSE CRUD ───────────────────────────────────────────────────────────────

@perm_required
def spouse_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = SpouseForm(request.POST or None)
    if form.is_valid():
        sp = form.save(commit=False)
        sp.mp = mp
        sp.save()
        messages.success(request, 'স্বামী/স্ত্রীর তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-spouse')
    return render(request, 'mp/spouse_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন স্বামী/স্ত্রী',
        'title_en':  'New Spouse',
    })


@perm_required
def spouse_update(request, pk, spk):
    mp     = get_object_or_404(MP, pk=pk)
    spouse = get_object_or_404(Spouse, pk=spk, mp=mp)
    form   = SpouseForm(request.POST or None, instance=spouse)
    if form.is_valid():
        form.save()
        messages.success(request, 'স্বামী/স্ত্রীর তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-spouse')
    return render(request, 'mp/spouse_form.html', {
        'form': form, 'mp': mp, 'spouse': spouse,
        'is_create': False, 'title_bn': 'স্বামী/স্ত্রীর তথ্য সম্পাদনা',
        'title_en':  'Edit Spouse',
    })


@perm_required
@require_POST
def spouse_delete(request, pk, spk):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(Spouse, pk=spk, mp=mp).delete()
    messages.success(request, 'স্বামী/স্ত্রীর তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-spouse')


# ── CHILDREN CRUD ─────────────────────────────────────────────────────────────

@perm_required
def child_create(request, pk):
    mp          = get_object_or_404(MP, pk=pk)
    next_serial = mp.children.count() + 1
    form        = ChildForm(request.POST or None, initial={'serial': next_serial})
    if form.is_valid():
        ch = form.save(commit=False)
        ch.mp = mp
        ch.save()
        messages.success(request, 'সন্তানের তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-children')
    return render(request, 'mp/child_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন সন্তান',
        'title_en':  'New Child',
    })


@perm_required
def child_update(request, pk, ck):
    mp    = get_object_or_404(MP, pk=pk)
    child = get_object_or_404(Child, pk=ck, mp=mp)
    form  = ChildForm(request.POST or None, instance=child)
    if form.is_valid():
        form.save()
        messages.success(request, 'সন্তানের তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-children')
    return render(request, 'mp/child_form.html', {
        'form': form, 'mp': mp, 'child': child,
        'is_create': False, 'title_bn': 'সন্তানের তথ্য সম্পাদনা',
        'title_en':  'Edit Child',
    })


@perm_required
@require_POST
def child_delete(request, pk, ck):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(Child, pk=ck, mp=mp).delete()
    messages.success(request, 'সন্তানের তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-children')


# ── EDUCATION — fixed-section single page (Phase 17.11) ───────────────────────

# (level_type, section kind, title_bn, title_en). Order = display order.
_EDU_SECTIONS = [
    ('secondary',  'school', 'এসএসসি বা সমমান',       'SSC or Equivalent'),
    ('higher_sec', 'school', 'এইচএসসি বা সমমান',      'HSC or Equivalent'),
    ('diploma',    'school', 'ডিপ্লোমা / ভোকেশনাল',   'Diploma / Vocational'),
    ('bachelor',   'degree', 'স্নাতক (সম্মান)',        'Graduation'),
    ('masters',    'degree', 'স্নাতকোত্তর',            'Masters'),
    ('phd',        'degree', 'পিএইচডি / ডক্টরেট',     'PhD / Doctorate'),
]


@perm_required
def education_sections(request, pk):
    """Single page with a fixed section per education level + a self-educated
    free-text block. Saves/updates/deletes all sections in one submit."""
    mp = get_object_or_404(MP, pk=pk)

    # Resolve the canonical EducationLevel row for each section (seeded in master/0008).
    levels = {
        lt: EducationLevel.objects.filter(level_type=lt, is_active=True)
        .order_by('ordering').first()
        for lt, _kind, _bn, _en in _EDU_SECTIONS
    }
    # Existing record per level_type (first one; sections assume one row per level).
    existing = {}
    for edu in mp.educations.select_related('education_level').all():
        lt = edu.education_level.level_type if edu.education_level else None
        if lt and lt not in existing:
            existing[lt] = edu

    sections = []
    for lt, kind, tbn, ten in _EDU_SECTIONS:
        sections.append({
            'key': lt, 'kind': kind, 'title_bn': tbn, 'title_en': ten,
            'level': levels.get(lt),
            'form': EducationSectionForm(
                request.POST or None, prefix=lt,
                instance=existing.get(lt), level=levels.get(lt)),
        })

    if request.method == 'POST':
        if all(s['form'].is_valid() for s in sections):
            for s in sections:
                form, level = s['form'], s['level']
                inst = form.instance
                if form.has_data():
                    edu = form.save(commit=False)
                    edu.mp = mp
                    if level is not None:
                        edu.education_level = level
                        edu.ordering = level.degree_order
                    edu.save()
                elif inst and inst.pk:
                    inst.delete()

            mp.is_self_educated  = bool(request.POST.get('is_self_educated'))
            mp.self_education_bn = request.POST.get('self_education_bn', '').strip()
            mp.self_education_en = request.POST.get('self_education_en', '').strip()
            mp.save(update_fields=['is_self_educated', 'self_education_bn', 'self_education_en'])

            messages.success(request, 'শিক্ষাগত তথ্য সংরক্ষিত হয়েছে।')
            return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-education')
        messages.error(request, 'কিছু তথ্য সঠিক নয় — নিচের ত্রুটিগুলো ঠিক করুন।')

    return render(request, 'mp/education_sections.html', {
        'mp':            mp,
        'sections':      sections,
        'result_types':  ResultType.objects.filter(is_active=True).order_by('ordering'),
        'is_self_educated':  mp.is_self_educated,
        'self_education_bn': mp.self_education_bn,
        'self_education_en': mp.self_education_en,
    })


# ── FOREIGN LANGUAGE SKILLS CRUD ─────────────────────────────────────────────

@perm_required
def language_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = ForeignLanguageSkillForm(request.POST or None,
                                    initial={'ordering': mp.language_skills.count() + 1})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'ভাষার তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-language')
    return render(request, 'mp/language_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন বিদেশি ভাষা',
        'title_en':  'New Language',
    })


@perm_required
def language_update(request, pk, lk):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(ForeignLanguageSkill, pk=lk, mp=mp)
    form = ForeignLanguageSkillForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'ভাষার তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-language')
    return render(request, 'mp/language_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'ভাষার তথ্য সম্পাদনা',
        'title_en':  'Edit Language',
    })


@perm_required
@require_POST
def language_delete(request, pk, lk):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(ForeignLanguageSkill, pk=lk, mp=mp).delete()
    messages.success(request, 'ভাষার তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-language')


# ── BANK ACCOUNTS CRUD ────────────────────────────────────────────────────────

@perm_required
def bank_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = BankAccountForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'ব্যাংক হিসাবের তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-bank')
    return render(request, 'mp/bank_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন ব্যাংক হিসাব',
        'title_en':  'New Bank Account',
    })


@perm_required
def bank_update(request, pk, bk):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(BankAccount, pk=bk, mp=mp)
    form = BankAccountForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'ব্যাংক হিসাবের তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-bank')
    return render(request, 'mp/bank_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'ব্যাংক হিসাব সম্পাদনা',
        'title_en':  'Edit Bank Account',
    })


@perm_required
@require_POST
def bank_delete(request, pk, bk):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(BankAccount, pk=bk, mp=mp).delete()
    messages.success(request, 'ব্যাংক হিসাবের তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-bank')


# ── COVID VACCINATION CRUD ────────────────────────────────────────────────────

@perm_required
def covid_create(request, pk):
    mp          = get_object_or_404(MP, pk=pk)
    next_dose   = mp.covid_vaccinations.count() + 1
    form = CovidVaccinationForm(request.POST or None, initial={'dose_number': next_dose})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'টিকার তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-covid')
    return render(request, 'mp/covid_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন কোভিড টিকার তথ্য',
        'title_en':  'New Covid Vaccination',
    })


@perm_required
def covid_update(request, pk, ck):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(CovidVaccination, pk=ck, mp=mp)
    form = CovidVaccinationForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'টিকার তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-covid')
    return render(request, 'mp/covid_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'টিকার তথ্য সম্পাদনা',
        'title_en':  'Edit Vaccination',
    })


@perm_required
@require_POST
def covid_delete(request, pk, ck):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(CovidVaccination, pk=ck, mp=mp).delete()
    messages.success(request, 'টিকার তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-covid')


# ── PARLIAMENTARY HISTORY CRUD ────────────────────────────────────────────────

@perm_required
def history_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    next_ord = mp.parliamentary_histories.count() + 1
    form = PreviousParliamentaryHistoryForm(request.POST or None, initial={'ordering': next_ord})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'সংসদ ইতিহাস সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-history')
    return render(request, 'mp/history_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন সংসদ ইতিহাস',
        'title_en':  'New Parliamentary History',
    })


@perm_required
def history_update(request, pk, hk):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(PreviousParliamentaryHistory, pk=hk, mp=mp)
    form = PreviousParliamentaryHistoryForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'সংসদ ইতিহাস আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-history')
    return render(request, 'mp/history_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'সংসদ ইতিহাস সম্পাদনা',
        'title_en':  'Edit Parliamentary History',
    })


@perm_required
@require_POST
def history_delete(request, pk, hk):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(PreviousParliamentaryHistory, pk=hk, mp=mp).delete()
    messages.success(request, 'সংসদ ইতিহাস মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-history')


# ── ORGANIZATIONS CRUD ────────────────────────────────────────────────────────

@perm_required
def organization_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = OrganizationForm(request.POST or None,
                            initial={'ordering': mp.organizations.count() + 1})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'সংগঠনের তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-organization')
    return render(request, 'mp/organization_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন সংগঠন',
        'title_en':  'New Organization',
    })


@perm_required
def organization_update(request, pk, ok):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(Organization, pk=ok, mp=mp)
    form = OrganizationForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'সংগঠনের তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-organization')
    return render(request, 'mp/organization_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'সংগঠন সম্পাদনা',
        'title_en':  'Edit Organization',
    })


@perm_required
@require_POST
def organization_delete(request, pk, ok):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(Organization, pk=ok, mp=mp).delete()
    messages.success(request, 'সংগঠনের তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-organization')


# ── AWARDS CRUD ───────────────────────────────────────────────────────────────

@perm_required
def award_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = AwardForm(request.POST or None, initial={'ordering': mp.awards.count() + 1})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'পুরস্কারের তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-award')
    return render(request, 'mp/award_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন পুরস্কার',
        'title_en':  'New Award',
    })


@perm_required
def award_update(request, pk, ak):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(Award, pk=ak, mp=mp)
    form = AwardForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'পুরস্কারের তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-award')
    return render(request, 'mp/award_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'পুরস্কার সম্পাদনা',
        'title_en':  'Edit Award',
    })


@perm_required
@require_POST
def award_delete(request, pk, ak):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(Award, pk=ak, mp=mp).delete()
    messages.success(request, 'পুরস্কারের তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-award')


# ── SOCIAL SERVICE (single per MP) ────────────────────────────────────────────

@perm_required
def social_service_save(request, pk):
    mp       = get_object_or_404(MP, pk=pk)
    instance, _ = SocialService.objects.get_or_create(mp=mp)
    form     = SocialServiceForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, 'সমাজ সেবার তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-social')
    return render(request, 'mp/social_service_form.html', {
        'form': form, 'mp': mp, 'title_bn': 'সমাজ সেবা',
        'title_en':  'Social Service',
    })


# ── SPECIAL POSITIONS CRUD ────────────────────────────────────────────────────

@perm_required
def special_position_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = SpecialPositionHistoryForm(request.POST or None,
                                      initial={'parliament': mp.parliament})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'বিশেষ পদের তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-special')
    return render(request, 'mp/special_position_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন বিশেষ পদ',
        'title_en':  'New Special Position',
    })


@perm_required
def special_position_update(request, pk, spk):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(SpecialPositionHistory, pk=spk, mp=mp)
    form = SpecialPositionHistoryForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'বিশেষ পদের তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-special')
    return render(request, 'mp/special_position_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'বিশেষ পদ সম্পাদনা',
        'title_en':  'Edit Special Position',
    })


@perm_required
@require_POST
def special_position_delete(request, pk, spk):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(SpecialPositionHistory, pk=spk, mp=mp).delete()
    messages.success(request, 'বিশেষ পদের তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-special')


# ── PUBLICATIONS CRUD ─────────────────────────────────────────────────────────

@perm_required
def publication_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = PublicationForm(request.POST or None,
                           initial={'ordering': mp.publications.count() + 1})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.mp = mp
        obj.save()
        messages.success(request, 'প্রকাশনার তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-publication')
    return render(request, 'mp/publication_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন প্রকাশনা',
        'title_en':  'New Publication',
    })


@perm_required
def publication_update(request, pk, pubk):
    mp  = get_object_or_404(MP, pk=pk)
    obj = get_object_or_404(Publication, pk=pubk, mp=mp)
    form = PublicationForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, 'প্রকাশনার তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-publication')
    return render(request, 'mp/publication_form.html', {
        'form': form, 'mp': mp, 'obj': obj,
        'is_create': False, 'title_bn': 'প্রকাশনা সম্পাদনা',
        'title_en':  'Edit Publication',
    })


@perm_required
@require_POST
def publication_delete(request, pk, pubk):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(Publication, pk=pubk, mp=mp).delete()
    messages.success(request, 'প্রকাশনার তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-publication')


# ── TOGGLE ACTIVE ─────────────────────────────────────────────────────────────

@perm_required
@require_POST
def mp_toggle(request, pk):
    mp = get_object_or_404(MP, pk=pk)
    mp.is_active = not mp.is_active
    mp.save(update_fields=['is_active'])
    label = 'সক্রিয়' if mp.is_active else 'নিষ্ক্রিয়'
    messages.success(request, f'"{mp.name_bn}" {label} করা হয়েছে।')
    return redirect('mp:mp_list')


# ── SYNC CONFLICT REVIEW ──────────────────────────────────────────────────────

@perm_required
def sync_conflict_list(request):
    """Review page for PRP API sync conflicts, grouped by MP."""
    status = request.GET.get('status', 'pending')
    target = request.GET.get('target', '')
    q      = request.GET.get('q', '').strip()

    qs = MPSyncConflict.objects.select_related('mp', 'resolved_by')
    if status in ('pending', 'resolved'):
        qs = qs.filter(status=status)
    if target:
        qs = qs.filter(target=target)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q)
            | Q(mp__mp_id__icontains=q)
        )
    qs = qs.order_by('mp__mp_id', 'target', 'field_key')

    # group by MP (preserve order)
    groups = []
    current = None
    for c in qs:
        if current is None or current['mp'].pk != c.mp.pk:
            current = {'mp': c.mp, 'items': []}
            groups.append(current)
        current['items'].append(c)

    return render(request, 'mp/sync_conflicts.html', {
        'groups':        groups,
        'status':        status,
        'target':        target,
        'q':             q,
        'target_choices': MPSyncConflict.TARGET_CHOICES,
        'pending_count': MPSyncConflict.objects.filter(status='pending').count(),
    })


@perm_required
@require_POST
def sync_conflict_update(request):
    """Apply a resolution to one or many conflicts (choice = system | api)."""
    choice = request.POST.get('choice')
    if choice not in ('system', 'api'):
        messages.error(request, 'অবৈধ সিদ্ধান্ত।')
        return redirect('mp:sync_conflict_list')

    ids = request.POST.getlist('ids')
    single = request.POST.get('conflict_id')
    if single:
        ids = [single]

    conflicts = MPSyncConflict.objects.filter(pk__in=ids, status='pending')
    n = 0
    for c in conflicts:
        api_sync.apply_conflict(c, request.user, choice)
        n += 1

    verb = 'API মান প্রয়োগ' if choice == 'api' else 'সিস্টেমের মান রাখা'
    messages.success(request, f'{n}টি দ্বন্দ্বে {verb} হয়েছে।')

    params = request.POST.get('return_params', '')
    return redirect(reverse('mp:sync_conflict_list') + (f'?{params}' if params else ''))


def _can_run_sync(user):
    """Trigger sync = superadmin, or can_edit on the Sync Conflicts submenu."""
    if getattr(user, 'is_superadmin', False):
        return True
    from apps.accounts.models import RolePermission, SubMenu
    if not getattr(user, 'role', None):
        return False
    sm = SubMenu.objects.filter(url_name='mp:sync_conflict_list').first()
    if not sm:
        return False
    perm = RolePermission.objects.filter(role=user.role, submenu=sm).first()
    return bool(perm and perm.can_edit)


@login_required
@require_POST
def sync_run(request):
    """Trigger a live PRP API pull in --sync mode (conflict-safe).

    Missing MP photos/signatures are backfilled from the API during the pull
    (existing images are never overwritten — system stays canonical).
    """
    if not _can_run_sync(request.user):
        raise PermissionDenied

    username = os.environ.get('PRP_API_USER')
    password = os.environ.get('PRP_API_PASS')
    if not (username and password):
        messages.error(
            request,
            'PRP API ক্রেডেনশিয়াল কনফিগার করা নেই (সার্ভারে PRP_API_USER / '
            'PRP_API_PASS পরিবেশ ভেরিয়েবল সেট করুন)।')
        return redirect('mp:sync_conflict_list')

    buf = StringIO()
    try:
        call_command('import_mp_api', fetch=True, sync=True, no_images=False,
                     username=username, password=password, stdout=buf, stderr=buf)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f'সিঙ্ক ব্যর্থ হয়েছে: {exc}')
        return redirect('mp:sync_conflict_list')

    pending = MPSyncConflict.objects.filter(status='pending').count()
    messages.success(
        request,
        f'PRP API সিঙ্ক সম্পন্ন হয়েছে। {pending}টি অমীমাংসিত দ্বন্দ্ব পর্যালোচনার জন্য প্রস্তুত।')

    # Photos are downloaded one-by-one; a single web request can time out before
    # every MP is covered. Report how many still lack a photo so the operator
    # knows to run Sync again (only the missing ones are fetched next time).
    no_photo = MP.objects.filter(Q(photo='') | Q(photo__isnull=True)).count()
    if no_photo:
        messages.warning(
            request,
            f'{no_photo} জন সংসদ সদস্যের ছবি এখনো আসেনি (বড় ব্যাচে সময় শেষ হয়ে '
            f'যেতে পারে)। সব ছবি একসাথে আনতে সার্ভারে চালান: '
            f'python manage.py import_mp_api --images-only — অথবা আবার "সিঙ্ক" চাপুন।')
    return redirect('mp:sync_conflict_list')
