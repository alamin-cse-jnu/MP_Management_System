from django.contrib import messages
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
    SpouseForm, ChildForm, EducationForm, AddressForm,
    ForeignLanguageSkillForm, BankAccountForm, CovidVaccinationForm,
    PreviousParliamentaryHistoryForm, OrganizationForm, AwardForm,
    SocialServiceForm, SpecialPositionHistoryForm, PublicationForm,
)
from .models import (
    MP, ElectionInfo, Spouse, Child, Education, Address,
    ForeignLanguageSkill, BankAccount, CovidVaccination,
    PreviousParliamentaryHistory, Organization, Award,
    SocialService, SpecialPositionHistory, Publication,
)


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


# ── EDUCATION CRUD ────────────────────────────────────────────────────────────

@perm_required
def education_create(request, pk):
    mp   = get_object_or_404(MP, pk=pk)
    form = EducationForm(request.POST or None)
    if form.is_valid():
        edu = form.save(commit=False)
        edu.mp = mp
        edu.save()
        messages.success(request, 'শিক্ষাগত তথ্য সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-education')
    return render(request, 'mp/education_form.html', {
        'form': form, 'mp': mp, 'is_create': True, 'title_bn': 'নতুন শিক্ষাগত তথ্য',
        'title_en':  'New Education',
    })


@perm_required
def education_update(request, pk, ek):
    mp  = get_object_or_404(MP, pk=pk)
    edu = get_object_or_404(Education, pk=ek, mp=mp)
    form = EducationForm(request.POST or None, instance=edu)
    if form.is_valid():
        form.save()
        messages.success(request, 'শিক্ষাগত তথ্য আপডেট হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-education')
    return render(request, 'mp/education_form.html', {
        'form': form, 'mp': mp, 'edu': edu,
        'is_create': False, 'title_bn': 'শিক্ষাগত তথ্য সম্পাদনা',
        'title_en':  'Edit Education',
    })


@perm_required
@require_POST
def education_delete(request, pk, ek):
    mp = get_object_or_404(MP, pk=pk)
    get_object_or_404(Education, pk=ek, mp=mp).delete()
    messages.success(request, 'শিক্ষাগত তথ্য মুছে ফেলা হয়েছে।')
    return redirect(reverse('mp:mp_detail', args=[pk]) + '?active=tab-education')


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
