from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from apps.committee.models import CommitteeAssignment
from apps.institution.models import InstitutionAssignment
from apps.master.models import (
    CommitteePosition, Country, District, Division, Gender,
    GovernmentInstitution, MinisterType, Ministry, PoliticalParty,
    ProfessionalQualification, StandingCommittee, TravelType,
)
from apps.ministry.models import MinistryAssignment
from apps.mp.models import MP, Address, ElectionInfo
from apps.office.models import ParliamentOfficeAddress
from apps.parliament.models import Parliament
from apps.travel.models import ForeignTour, ForeignTourParticipant

from .utils import export_csv, export_excel

PAGE_SIZE = 25


# ── helpers ────────────────────────────────────────────────────────────────────

def _active_parliament_id(request):
    pid = request.GET.get('parliament', '')
    if not pid:
        p = Parliament.objects.filter(is_active=True).first()
        if p:
            pid = str(p.pk)
    return pid


def _parliament_qs():
    return Parliament.objects.order_by('-ordinal')


def _mp_qs_base(parliament_id=None):
    qs = MP.objects.select_related(
        'parliament', 'gender', 'religion', 'blood_group',
        'home_district', 'home_district__division', 'birth_district',
    ).prefetch_related(
        Prefetch('election_infos',
                 queryset=ElectionInfo.objects.select_related('constituency', 'party', 'parliament')),
        'professions_current',
        'professional_qualifications',
    ).filter(is_active=True)
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    return qs


# ── index ──────────────────────────────────────────────────────────────────────

@login_required
def index(request):
    active_parliament = Parliament.objects.filter(is_active=True).first()
    stats = {}
    if active_parliament:
        stats['total_mp'] = MP.objects.filter(is_active=True, parliament=active_parliament).count()
        stats['women_mp'] = MP.objects.filter(
            is_active=True, parliament=active_parliament, member_type='reserved'
        ).count()
        stats['cabinet'] = MinistryAssignment.objects.filter(
            is_active=True, parliament=active_parliament
        ).count()
        stats['tours'] = ForeignTour.objects.filter(parliament=active_parliament).count()
    else:
        stats['total_mp'] = MP.objects.filter(is_active=True).count()
        stats['women_mp'] = MP.objects.filter(is_active=True, member_type='reserved').count()
        stats['cabinet'] = MinistryAssignment.objects.filter(is_active=True).count()
        stats['tours'] = ForeignTour.objects.count()
    return render(request, 'reports/index.html', {
        'active_parliament': active_parliament,
        'stats': stats,
    })


# ── Report 1: সকল সংসদ সদস্য তালিকা ─────────────────────────────────────────

ALL_MP_COLS = [
    ('photo',         'ছবি'),
    ('mp_id',         'এমপি আইডি'),
    ('name_bn',       'নাম (বাংলায়)'),
    ('name_en',       'Name (English)'),
    ('constituency',  'নির্বাচনী এলাকা'),
    ('party',         'রাজনৈতিক দল'),
    ('gender',        'লিঙ্গ'),
    ('dob',           'জন্ম তারিখ'),
    ('religion',      'ধর্ম'),
    ('blood_group',   'রক্তের গ্রুপ'),
    ('district',      'জেলা'),
    ('professions',   'পেশা'),
]
ALL_MP_DEFAULT = ['mp_id', 'name_bn', 'name_en', 'constituency', 'party', 'district']


@login_required
def all_mp(request):
    fmt = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)

    selected_cols = request.GET.getlist('col') or ALL_MP_DEFAULT
    party_id      = request.GET.get('party', '')
    gender_id     = request.GET.get('gender', '')
    district_id   = request.GET.get('district', '')
    division_id   = request.GET.get('division', '')
    member_type   = request.GET.get('member_type', '')
    q             = request.GET.get('q', '').strip()

    qs = _mp_qs_base(parliament_id)
    if party_id:
        qs = qs.filter(election_infos__party_id=party_id)
    if gender_id:
        qs = qs.filter(gender_id=gender_id)
    if district_id:
        qs = qs.filter(home_district_id=district_id)
    if division_id:
        qs = qs.filter(home_district__division_id=division_id)
    if member_type:
        qs = qs.filter(member_type=member_type)
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q) | Q(mp_id__icontains=q))
    qs = qs.distinct()

    ctx = {
        'ALL_COLS':       ALL_MP_COLS,
        'selected_cols':  selected_cols,
        'parliament_id':  parliament_id,
        'party_id':       party_id,
        'gender_id':      gender_id,
        'district_id':    district_id,
        'division_id':    division_id,
        'member_type':    member_type,
        'q':              q,
        'parliaments':    _parliament_qs(),
        'parties':        PoliticalParty.objects.filter(is_active=True),
        'genders':        Gender.objects.filter(is_active=True),
        'districts':      District.objects.filter(is_active=True).select_related('division'),
        'divisions':      Division.objects.filter(is_active=True),
        'total_count':    qs.count(),
    }

    if fmt == 'excel':
        return _all_mp_excel(qs, selected_cols)
    if fmt == 'csv':
        return _all_mp_csv(qs, selected_cols)
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/all_mp.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/all_mp.html', ctx)


def _all_mp_get_cell(mp, col):
    ei = next(iter(mp.election_infos.all()), None)
    if col == 'mp_id':        return mp.mp_id
    if col == 'name_bn':      return mp.name_bn
    if col == 'name_en':      return mp.name_en
    if col == 'constituency': return (ei.constituency.display_bn if ei and ei.constituency else '—')
    if col == 'party':        return (ei.party.name_bn if ei and ei.party else '—')
    if col == 'gender':       return (mp.gender.name_bn if mp.gender else '—')
    if col == 'dob':          return (mp.dob.strftime('%d/%m/%Y') if mp.dob else '—')
    if col == 'religion':     return (mp.religion.name_bn if mp.religion else '—')
    if col == 'blood_group':  return (mp.blood_group.name_bn if mp.blood_group else '—')
    if col == 'district':     return (mp.home_district.name_bn if mp.home_district else '—')
    if col == 'professions':  return ', '.join(p.name_bn for p in mp.professions_current.all()) or '—'
    return '—'


def _all_mp_excel(qs, selected_cols):
    col_labels = {k: v for k, v in ALL_MP_COLS}
    headers = ['ক্রম'] + [col_labels.get(c, c) for c in selected_cols if c != 'photo']
    data_cols = [c for c in selected_cols if c != 'photo']
    rows = [[i + 1] + [_all_mp_get_cell(mp, c) for c in data_cols] for i, mp in enumerate(qs)]
    return export_excel('all_mp_list', headers, rows, 'সকল সংসদ সদস্য')


def _all_mp_csv(qs, selected_cols):
    col_labels = {k: v for k, v in ALL_MP_COLS}
    headers = ['ক্রম'] + [col_labels.get(c, c) for c in selected_cols if c != 'photo']
    data_cols = [c for c in selected_cols if c != 'photo']
    rows = [[i + 1] + [_all_mp_get_cell(mp, c) for c in data_cols] for i, mp in enumerate(qs)]
    return export_csv('all_mp_list', headers, rows)


# ── Report 2: মহিলা সদস্য তালিকা ─────────────────────────────────────────────

@login_required
def women_mp(request):
    fmt = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    q = request.GET.get('q', '').strip()

    qs = _mp_qs_base(parliament_id).filter(member_type='reserved')
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q) | Q(mp_id__icontains=q))
    qs = qs.distinct()

    headers = ['ক্রম', 'এমপি আইডি', 'নাম (বাংলায়)', 'Name (English)', 'রাজনৈতিক দল', 'জেলা', 'জন্ম তারিখ']

    def rows_fn(queryset):
        out = []
        for i, mp in enumerate(queryset):
            ei = next(iter(mp.election_infos.all()), None)
            out.append([
                i + 1,
                mp.mp_id,
                mp.name_bn,
                mp.name_en,
                ei.party.name_bn if ei and ei.party else '—',
                mp.home_district.name_bn if mp.home_district else '—',
                mp.dob.strftime('%d/%m/%Y') if mp.dob else '—',
            ])
        return out

    if fmt == 'excel':
        return export_excel('women_mp', headers, rows_fn(qs), 'মহিলা সদস্য')
    if fmt == 'csv':
        return export_csv('women_mp', headers, rows_fn(qs))

    ctx = {
        'parliament_id': parliament_id,
        'parliaments':   _parliament_qs(),
        'q':             q,
        'total_count':   qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/women_mp.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/women_mp.html', ctx)


# ── Report 3: দল ভিত্তিক তালিকা ──────────────────────────────────────────────

@login_required
def party_wise(request):
    fmt = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    party_id = request.GET.get('party', '')
    q        = request.GET.get('q', '').strip()

    qs = _mp_qs_base(parliament_id)
    if party_id:
        qs = qs.filter(election_infos__party_id=party_id)
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q))
    qs = qs.distinct()

    headers = ['ক্রম', 'এমপি আইডি', 'নাম (বাংলায়)', 'Name', 'নির্বাচনী এলাকা', 'রাজনৈতিক দল', 'কতবার']

    def rows_fn(queryset):
        out = []
        for i, mp in enumerate(queryset):
            ei = next(iter(mp.election_infos.all()), None)
            out.append([
                i + 1, mp.mp_id, mp.name_bn, mp.name_en,
                ei.constituency.display_bn if ei and ei.constituency else '—',
                ei.party.name_bn if ei and ei.party else '—',
                ei.times_elected if ei else '—',
            ])
        return out

    if fmt == 'excel':
        return export_excel('party_wise', headers, rows_fn(qs), 'দল ভিত্তিক')
    if fmt == 'csv':
        return export_csv('party_wise', headers, rows_fn(qs))

    ctx = {
        'parliament_id': parliament_id,
        'party_id':      party_id,
        'q':             q,
        'parliaments':   _parliament_qs(),
        'parties':       PoliticalParty.objects.filter(is_active=True),
        'total_count':   qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/party_wise.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/party_wise.html', ctx)


# ── Report 4: জেলা/বিভাগ ভিত্তিক ─────────────────────────────────────────────

@login_required
def district_wise(request):
    fmt = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    district_id   = request.GET.get('district', '')
    division_id   = request.GET.get('division', '')
    q             = request.GET.get('q', '').strip()

    qs = _mp_qs_base(parliament_id)
    if district_id:
        qs = qs.filter(home_district_id=district_id)
    if division_id:
        qs = qs.filter(home_district__division_id=division_id)
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q))
    qs = qs.distinct()

    headers = ['ক্রম', 'এমপি আইডি', 'নাম (বাংলায়)', 'Name', 'বিভাগ', 'জেলা', 'নির্বাচনী এলাকা', 'দল']

    def rows_fn(queryset):
        out = []
        for i, mp in enumerate(queryset):
            ei = next(iter(mp.election_infos.all()), None)
            dist = mp.home_district
            out.append([
                i + 1, mp.mp_id, mp.name_bn, mp.name_en,
                dist.division.name_bn if dist and dist.division else '—',
                dist.name_bn if dist else '—',
                ei.constituency.display_bn if ei and ei.constituency else '—',
                ei.party.name_bn if ei and ei.party else '—',
            ])
        return out

    if fmt == 'excel':
        return export_excel('district_wise', headers, rows_fn(qs), 'জেলা ভিত্তিক')
    if fmt == 'csv':
        return export_csv('district_wise', headers, rows_fn(qs))

    ctx = {
        'parliament_id': parliament_id,
        'district_id':   district_id,
        'division_id':   division_id,
        'q':             q,
        'parliaments':   _parliament_qs(),
        'districts':     District.objects.filter(is_active=True).select_related('division'),
        'divisions':     Division.objects.filter(is_active=True),
        'total_count':   qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/district_wise.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/district_wise.html', ctx)


# ── Report 5: পেশাদার যোগ্যতা ভিত্তিক ────────────────────────────────────────

@login_required
def qualification_wise(request):
    fmt           = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    qual_id       = request.GET.get('qualification', '')
    q             = request.GET.get('q', '').strip()

    qs = _mp_qs_base(parliament_id)
    if qual_id:
        qs = qs.filter(professional_qualifications__id=qual_id)
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q))
    qs = qs.distinct()

    headers = ['ক্রম', 'এমপি আইডি', 'নাম (বাংলায়)', 'Name', 'পেশাদার যোগ্যতা', 'নির্বাচনী এলাকা', 'দল']

    def rows_fn(queryset):
        out = []
        for i, mp in enumerate(queryset):
            ei = next(iter(mp.election_infos.all()), None)
            quals = ', '.join(q.name_bn for q in mp.professional_qualifications.all()) or '—'
            out.append([
                i + 1, mp.mp_id, mp.name_bn, mp.name_en, quals,
                ei.constituency.display_bn if ei and ei.constituency else '—',
                ei.party.name_bn if ei and ei.party else '—',
            ])
        return out

    if fmt == 'excel':
        return export_excel('qualification_wise', headers, rows_fn(qs), 'যোগ্যতা ভিত্তিক')
    if fmt == 'csv':
        return export_csv('qualification_wise', headers, rows_fn(qs))

    ctx = {
        'parliament_id':  parliament_id,
        'qual_id':        qual_id,
        'q':              q,
        'parliaments':    _parliament_qs(),
        'qualifications': ProfessionalQualification.objects.filter(is_active=True),
        'total_count':    qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/qualification_wise.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/qualification_wise.html', ctx)


# ── Report 6: মন্ত্রিসভা তালিকা ───────────────────────────────────────────────

@login_required
def cabinet(request):
    fmt             = request.GET.get('format', '')
    parliament_id   = _active_parliament_id(request)
    minister_type_id = request.GET.get('minister_type', '')
    status          = request.GET.get('status', 'active')
    q               = request.GET.get('q', '').strip()

    qs = MinistryAssignment.objects.select_related(
        'mp', 'parliament', 'ministry', 'minister_type'
    )
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if minister_type_id:
        qs = qs.filter(minister_type_id=minister_type_id)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(ministry__name_bn__icontains=q)
        )

    headers = ['ক্রম', 'এমপি আইডি', 'নাম', 'মন্ত্রণালয়', 'মন্ত্রীর ধরন', 'শুরু', 'শেষ', 'GO নং', 'অবস্থা']

    def rows_fn(queryset):
        out = []
        for i, obj in enumerate(queryset):
            out.append([
                i + 1,
                obj.mp.mp_id,
                obj.mp.name_bn,
                obj.ministry.name_bn,
                obj.minister_type.name_bn,
                obj.start_date.strftime('%d/%m/%Y') if obj.start_date else '—',
                obj.end_date.strftime('%d/%m/%Y') if obj.end_date else '—',
                obj.go_number or '—',
                'সক্রিয়' if obj.is_active else 'নিষ্ক্রিয়',
            ])
        return out

    if fmt == 'excel':
        return export_excel('cabinet', headers, rows_fn(qs), 'মন্ত্রিসভা')
    if fmt == 'csv':
        return export_csv('cabinet', headers, rows_fn(qs))

    ctx = {
        'parliament_id':    parliament_id,
        'minister_type_id': minister_type_id,
        'status':           status,
        'q':                q,
        'parliaments':      _parliament_qs(),
        'minister_types':   MinisterType.objects.filter(is_active=True),
        'total_count':      qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/cabinet.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/cabinet.html', ctx)


# ── Report 7: কমিটি সদস্য তালিকা ─────────────────────────────────────────────

@login_required
def committee_members(request):
    fmt          = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    committee_id = request.GET.get('committee', '')
    position_id  = request.GET.get('position', '')
    status       = request.GET.get('status', 'active')
    q            = request.GET.get('q', '').strip()

    qs = CommitteeAssignment.objects.select_related(
        'mp', 'parliament', 'committee', 'position'
    )
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if committee_id:
        qs = qs.filter(committee_id=committee_id)
    if position_id:
        qs = qs.filter(position_id=position_id)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(committee__name_bn__icontains=q)
        )

    headers = ['ক্রম', 'এমপি আইডি', 'নাম', 'কমিটি', 'পদ', 'শুরু', 'শেষ', 'অবস্থা']

    def rows_fn(queryset):
        out = []
        for i, obj in enumerate(queryset):
            out.append([
                i + 1,
                obj.mp.mp_id,
                obj.mp.name_bn,
                obj.committee.name_bn,
                obj.position.name_bn,
                obj.start_date.strftime('%d/%m/%Y') if obj.start_date else '—',
                obj.end_date.strftime('%d/%m/%Y') if obj.end_date else '—',
                'সক্রিয়' if obj.is_active else 'নিষ্ক্রিয়',
            ])
        return out

    if fmt == 'excel':
        return export_excel('committee_members', headers, rows_fn(qs), 'কমিটি সদস্য')
    if fmt == 'csv':
        return export_csv('committee_members', headers, rows_fn(qs))

    ctx = {
        'parliament_id': parliament_id,
        'committee_id':  committee_id,
        'position_id':   position_id,
        'status':        status,
        'q':             q,
        'parliaments':   _parliament_qs(),
        'committees':    StandingCommittee.objects.filter(is_active=True),
        'positions':     CommitteePosition.objects.filter(is_active=True),
        'total_count':   qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/committee_members.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/committee_members.html', ctx)


# ── Report 8: এমপি কমিটি সারসংক্ষেপ ──────────────────────────────────────────

@login_required
def mp_committee_summary(request):
    fmt   = request.GET.get('format', '')
    mp_id = request.GET.get('mp_id', '').strip()
    mp    = None
    qs    = CommitteeAssignment.objects.none()

    if mp_id:
        mp = MP.objects.filter(mp_id=mp_id).first()
        if mp:
            qs = CommitteeAssignment.objects.filter(mp=mp).select_related(
                'committee', 'position', 'parliament'
            ).order_by('-start_date')

    headers = ['ক্রম', 'কমিটি', 'পদ', 'সংসদ', 'শুরু', 'শেষ', 'অবস্থা']

    def rows_fn(queryset):
        out = []
        for i, obj in enumerate(queryset):
            out.append([
                i + 1,
                obj.committee.name_bn,
                obj.position.name_bn,
                obj.parliament.name_bn,
                obj.start_date.strftime('%d/%m/%Y') if obj.start_date else '—',
                obj.end_date.strftime('%d/%m/%Y') if obj.end_date else '—',
                'সক্রিয়' if obj.is_active else 'নিষ্ক্রিয়',
            ])
        return out

    if fmt == 'excel' and mp:
        return export_excel(f'committee_summary_{mp.mp_id}', headers, rows_fn(qs), 'কমিটি সারসংক্ষেপ')
    if fmt == 'csv' and mp:
        return export_csv(f'committee_summary_{mp.mp_id}', headers, rows_fn(qs))

    ctx = {
        'mp_id':       mp_id,
        'mp':          mp,
        'object_list': qs,
    }
    if fmt == 'print' and mp:
        return render(request, 'reports/print/mp_committee_summary.html', ctx)
    return render(request, 'reports/mp_committee_summary.html', ctx)


# ── Report 9: প্রতিষ্ঠান নিয়োগ তালিকা ────────────────────────────────────────

@login_required
def institution_assignments(request):
    fmt            = request.GET.get('format', '')
    parliament_id  = _active_parliament_id(request)
    institution_id = request.GET.get('institution', '')
    status         = request.GET.get('status', 'active')
    q              = request.GET.get('q', '').strip()

    qs = InstitutionAssignment.objects.select_related(
        'mp', 'parliament', 'institution', 'role'
    )
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if institution_id:
        qs = qs.filter(institution_id=institution_id)
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(institution__name_bn__icontains=q)
        )

    headers = ['ক্রম', 'এমপি আইডি', 'নাম', 'প্রতিষ্ঠান', 'ভূমিকা', 'শুরু', 'শেষ', 'অবস্থা']

    def rows_fn(queryset):
        out = []
        for i, obj in enumerate(queryset):
            out.append([
                i + 1,
                obj.mp.mp_id,
                obj.mp.name_bn,
                obj.institution.name_bn,
                obj.role.name_bn,
                obj.start_date.strftime('%d/%m/%Y') if obj.start_date else '—',
                obj.end_date.strftime('%d/%m/%Y') if obj.end_date else '—',
                'সক্রিয়' if obj.is_active else 'নিষ্ক্রিয়',
            ])
        return out

    if fmt == 'excel':
        return export_excel('institution_assignments', headers, rows_fn(qs), 'প্রতিষ্ঠান নিয়োগ')
    if fmt == 'csv':
        return export_csv('institution_assignments', headers, rows_fn(qs))

    ctx = {
        'parliament_id':  parliament_id,
        'institution_id': institution_id,
        'status':         status,
        'q':              q,
        'parliaments':    _parliament_qs(),
        'institutions':   GovernmentInstitution.objects.filter(is_active=True),
        'total_count':    qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/institution_assignments.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/institution_assignments.html', ctx)


# ── Report 10: বিদেশ সফর তালিকা ───────────────────────────────────────────────

@login_required
def foreign_tours(request):
    fmt           = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    tour_type_id  = request.GET.get('tour_type', '')
    country_id    = request.GET.get('country', '')
    year          = request.GET.get('year', '')
    q             = request.GET.get('q', '').strip()

    qs = ForeignTour.objects.select_related('parliament', 'tour_type', 'purpose').prefetch_related(
        Prefetch('participants', queryset=ForeignTourParticipant.objects.select_related('mp')),
        'countries__country',
    )
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if tour_type_id:
        qs = qs.filter(tour_type_id=tour_type_id)
    if country_id:
        qs = qs.filter(countries__country_id=country_id)
    if year:
        qs = qs.filter(go_date__year=year)
    if q:
        qs = qs.filter(Q(go_number__icontains=q) | Q(participants__mp__name_bn__icontains=q))
    qs = qs.distinct()

    import datetime
    current_year = datetime.date.today().year
    years = list(range(current_year, current_year - 15, -1))

    headers = ['ক্রম', 'GO নং', 'GO তারিখ', 'ধরন', 'উদ্দেশ্য', 'দেশসমূহ', 'সদস্যবৃন্দ', 'যাত্রা', 'প্রত্যাবর্তন']

    def rows_fn(queryset):
        out = []
        for i, tour in enumerate(queryset):
            countries = ', '.join(tc.country.name_bn for tc in tour.countries.all()) or '—'
            mps       = ', '.join(p.mp.name_bn for p in tour.participants.all()) or '—'
            first_p   = tour.participants.first()
            out.append([
                i + 1,
                tour.go_number,
                tour.go_date.strftime('%d/%m/%Y') if tour.go_date else '—',
                tour.tour_type.name_bn,
                tour.purpose.name_bn,
                countries,
                mps,
                first_p.departure_date.strftime('%d/%m/%Y') if first_p and first_p.departure_date else '—',
                first_p.return_date.strftime('%d/%m/%Y') if first_p and first_p.return_date else '—',
            ])
        return out

    if fmt == 'excel':
        return export_excel('foreign_tours', headers, rows_fn(qs), 'বিদেশ সফর')
    if fmt == 'csv':
        return export_csv('foreign_tours', headers, rows_fn(qs))

    ctx = {
        'parliament_id': parliament_id,
        'tour_type_id':  tour_type_id,
        'country_id':    country_id,
        'year':          year,
        'q':             q,
        'parliaments':   _parliament_qs(),
        'tour_types':    TravelType.objects.filter(is_active=True),
        'countries':     Country.objects.filter(is_active=True),
        'years':         years,
        'total_count':   qs.count(),
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/foreign_tours.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/foreign_tours.html', ctx)


# ── Report 11: এমপি বায়োডাটা (একক) ───────────────────────────────────────────

@login_required
def mp_biodata(request):
    mp_id = request.GET.get('mp_id', '').strip()
    mp    = None
    fmt   = request.GET.get('format', '')

    if mp_id:
        mp = MP.objects.filter(mp_id=mp_id).select_related(
            'parliament', 'gender', 'religion', 'blood_group', 'marital_status',
            'home_district__division', 'birth_district',
        ).prefetch_related(
            Prefetch('election_infos',
                     queryset=ElectionInfo.objects.select_related(
                         'constituency', 'party', 'parliament')),
            'spouses__profession', 'spouses__home_district', 'spouses__gender',
            'children__profession', 'children__gender',
            'educations__education_level', 'educations__degree_title',
            'educations__major_subject', 'educations__institution',
            'educations__result_type', 'educations__division_result',
            Prefetch('addresses',
                     queryset=Address.objects.select_related('division', 'district', 'upazila')),
            'language_skills__language', 'language_skills__proficiency',
            'bank_accounts',
            'covid_vaccinations__vaccine_name',
            'ministry_assignments__ministry', 'ministry_assignments__minister_type',
            'ministry_assignments__parliament',
            'committee_assignments__committee', 'committee_assignments__position',
            'committee_assignments__parliament',
            'institution_assignments__institution', 'institution_assignments__role',
            Prefetch('travel_participations',
                     queryset=ForeignTourParticipant.objects.select_related(
                         'tour__tour_type', 'tour__purpose'
                     ).prefetch_related('tour__countries__country')),
            'professions_current', 'professions_previous', 'professional_qualifications',
            'parliamentary_histories',
            'organizations',
            'awards',
            'special_positions__parliament', 'special_positions__role',
            'publications',
        ).first()

    ctx = {'mp_id': mp_id, 'mp': mp}

    if mp:
        try:
            ctx['office'] = mp.office_address
        except Exception:
            ctx['office'] = None
        try:
            ctx['social_service'] = mp.social_service
        except Exception:
            ctx['social_service'] = None

    if mp and fmt == 'print':
        return render(request, 'reports/print/mp_biodata.html', ctx)

    if mp and fmt == 'pdf':
        import base64
        import os
        import subprocess
        import tempfile
        from io import BytesIO
        from pathlib import Path
        from django.conf import settings

        # ── 1. Find best available Bangla font ──────────────────────────────
        font_candidates = [
            settings.BASE_DIR / 'static' / 'fonts' / 'SolaimanLipi.ttf',
            Path(r'C:\Windows\Fonts\kalpurush.ttf'),
            Path(r'C:\Windows\Fonts\Vrinda.ttf'),
            Path('/usr/share/fonts/truetype/kalpurush/kalpurush.ttf'),
        ]
        font_file_path = None
        for fp in font_candidates:
            if fp.exists():
                font_file_path = fp
                break
        # file:// URL for WeasyPrint (server-side filesystem); base64 for Edge (self-contained file)
        font_file_uri = font_file_path.as_uri() if font_file_path else ''
        font_data_uri = ''
        if font_file_path:
            with open(font_file_path, 'rb') as fh:
                font_data_uri = 'data:font/truetype;base64,' + base64.b64encode(fh.read()).decode()
        ctx['font_data_uri'] = font_file_uri   # file:// URL — works for WeasyPrint
        ctx['font_base64_uri'] = font_data_uri  # base64 — used when we write standalone HTML for Edge

        # ── 2. Embed parliament logo as base64 ───────────────────────────────
        logo_path = settings.BASE_DIR / 'static' / 'img' / 'parliament-logo.png'
        ctx['logo_data'] = None
        if logo_path.exists():
            with open(logo_path, 'rb') as fh:
                ctx['logo_data'] = (
                    'data:image/png;base64,' + base64.b64encode(fh.read()).decode()
                )

        # ── 3. Embed MP photo as base64 ──────────────────────────────────────
        photo_data = None
        if mp.photo:
            try:
                ext  = mp.photo.name.rsplit('.', 1)[-1].lower()
                mime = 'image/png' if ext == 'png' else 'image/jpeg'
                with open(mp.photo.path, 'rb') as fh:
                    photo_data = (
                        'data:{};base64,'.format(mime)
                        + base64.b64encode(fh.read()).decode()
                    )
            except Exception:
                photo_data = None
        ctx['photo_data'] = photo_data

        # ── 4. Render Bangla template (self-contained HTML) ──────────────────
        html_bn = render_to_string('reports/pdf/mp_biodata_bn.html', ctx, request=request)

        # ── 5. PDF engine cascade: Edge → WeasyPrint → xhtml2pdf ────────────
        pdf_bytes = None
        pdf_engine = 'none'

        # Tier 1: Edge / Chromium headless (best Bangla rendering on Windows)
        edge_exe = next(
            (e for e in [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
            ] if os.path.exists(e)),
            None,
        )
        if edge_exe:
            tmp_dir  = None
            tmp_html = None
            tmp_pdf  = None
            try:
                tmp_dir  = tempfile.mkdtemp()
                tmp_html = os.path.join(tmp_dir, 'biodata.html')
                tmp_pdf  = os.path.join(tmp_dir, 'biodata.pdf')
                # Replace file:// font URL with self-contained base64 so Edge can load the font
                html_for_edge = html_bn.replace(font_file_uri, font_data_uri) if font_file_uri else html_bn
                with open(tmp_html, 'w', encoding='utf-8') as fh:
                    fh.write(html_for_edge)
                file_url = 'file:///' + tmp_html.replace('\\', '/')
                subprocess.run(
                    [
                        edge_exe,
                        '--headless=new', '--disable-gpu', '--no-sandbox',
                        '--run-all-compositor-stages-before-draw',
                        '--virtual-time-budget=10000',
                        f'--print-to-pdf={tmp_pdf}',
                        '--print-to-pdf-no-header',
                        file_url,
                    ],
                    capture_output=True, timeout=60,
                )
                if os.path.exists(tmp_pdf) and os.path.getsize(tmp_pdf) > 1000:
                    with open(tmp_pdf, 'rb') as fh:
                        pdf_bytes = fh.read()
                    pdf_engine = 'edge'
            except Exception as _e:
                import traceback; traceback.print_exc()
            finally:
                for _f in [tmp_html, tmp_pdf]:
                    if _f:
                        try: os.unlink(_f)
                        except Exception: pass
                if tmp_dir:
                    try: os.rmdir(tmp_dir)
                    except Exception: pass

        # Tier 2: WeasyPrint (requires GTK runtime)
        if pdf_bytes is None:
            try:
                from weasyprint import HTML as WP_HTML
                pdf_bytes = WP_HTML(string=html_bn, base_url=str(settings.BASE_DIR)).write_pdf()
                pdf_engine = 'weasyprint'
            except Exception:
                pass

        # Tier 3: xhtml2pdf fallback (no Bangla shaping but produces a valid PDF)
        if pdf_bytes is None:
            from xhtml2pdf import pisa
            html_xhtml = render_to_string(
                'reports/pdf/mp_biodata_xhtml.html', ctx, request=request)
            buf = BytesIO()
            pisa.pisaDocument(BytesIO(html_xhtml.encode('utf-8')), buf)
            pdf_bytes = buf.getvalue()
            pdf_engine = 'xhtml2pdf'

        print(f'[PDF] engine={pdf_engine} size={len(pdf_bytes) if pdf_bytes else 0}')
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="biodata_{mp.mp_id}.pdf"'
        response['X-PDF-Engine'] = pdf_engine
        return response

    all_mps = MP.objects.filter(is_active=True).order_by('name_bn').values('mp_id', 'name_bn')
    ctx['all_mps'] = all_mps
    return render(request, 'reports/mp_biodata.html', ctx)


# ── Report 12: যোগাযোগ তালিকা ────────────────────────────────────────────────

CONTACT_COLS = [
    ('photo',        'ছবি'),
    ('mp_id',        'এমপি আইডি'),
    ('name_bn',      'নাম (বাংলায়)'),
    ('name_en',      'Name'),
    ('constituency', 'নির্বাচনী এলাকা'),
    ('party',        'দল'),
    ('mobile',       'মোবাইল'),
    ('telephone',    'টেলিফোন'),
    ('email',        'ই-মেইল'),
    ('whatsapp',     'হোয়াটসঅ্যাপ'),
    ('office_phone', 'অফিস টেলিফোন'),
    ('office_email', 'অফিস ই-মেইল'),
]
CONTACT_DEFAULT = ['mp_id', 'name_bn', 'constituency', 'party', 'mobile', 'email', 'office_phone']


@login_required
def contact_list(request):
    fmt           = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    party_id      = request.GET.get('party', '')
    district_id   = request.GET.get('district', '')
    selected_cols = request.GET.getlist('col') or CONTACT_DEFAULT
    q             = request.GET.get('q', '').strip()

    qs = MP.objects.select_related(
        'parliament', 'home_district',
    ).prefetch_related(
        Prefetch('election_infos',
                 queryset=ElectionInfo.objects.select_related('constituency', 'party')),
        Prefetch('addresses', queryset=Address.objects.filter(address_type='present')),
    ).filter(is_active=True)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if party_id:
        qs = qs.filter(election_infos__party_id=party_id)
    if district_id:
        qs = qs.filter(home_district_id=district_id)
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q) | Q(mp_id__icontains=q))
    qs = qs.distinct()

    # Attach office addresses in one query
    office_map = {
        oa.mp_id: oa
        for oa in ParliamentOfficeAddress.objects.filter(mp__in=qs)
    }

    def _get_present_addr(mp):
        return next((a for a in mp.addresses.all() if a.address_type == 'present'), None)

    def _contact_cell(mp, col):
        addr   = _get_present_addr(mp)
        office = office_map.get(mp.pk)
        ei     = next(iter(mp.election_infos.all()), None)
        if col == 'mp_id':        return mp.mp_id
        if col == 'name_bn':      return mp.name_bn
        if col == 'name_en':      return mp.name_en
        if col == 'constituency': return ei.constituency.display_bn if ei and ei.constituency else '—'
        if col == 'party':        return ei.party.name_bn if ei and ei.party else '—'
        if col == 'mobile':       return addr.mobile if addr else '—'
        if col == 'telephone':    return addr.telephone if addr else '—'
        if col == 'email':        return addr.email if addr else '—'
        if col == 'whatsapp':     return addr.whatsapp if addr else '—'
        if col == 'office_phone': return office.telephone if office else '—'
        if col == 'office_email': return office.official_email if office else '—'
        return '—'

    col_labels = {k: v for k, v in CONTACT_COLS}

    if fmt in ('excel', 'csv'):
        data_cols = [c for c in selected_cols if c != 'photo']
        headers   = ['ক্রম'] + [col_labels.get(c, c) for c in data_cols]
        rows      = [[i + 1] + [_contact_cell(mp, c) for c in data_cols] for i, mp in enumerate(qs)]
        if fmt == 'excel':
            return export_excel('contact_list', headers, rows, 'যোগাযোগ তালিকা')
        return export_csv('contact_list', headers, rows)

    ctx = {
        'CONTACT_COLS':  CONTACT_COLS,
        'selected_cols': selected_cols,
        'parliament_id': parliament_id,
        'party_id':      party_id,
        'district_id':   district_id,
        'q':             q,
        'parliaments':   _parliament_qs(),
        'parties':       PoliticalParty.objects.filter(is_active=True),
        'districts':     District.objects.filter(is_active=True),
        'total_count':   qs.count(),
        'office_map':    office_map,
    }
    if fmt == 'print':
        ctx['object_list'] = qs
        return render(request, 'reports/print/contact_list.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    return render(request, 'reports/contact_list.html', ctx)


# ── Audit Log ─────────────────────────────────────────────────────────────────

AUDIT_PAGE_SIZE = 50


@login_required
def audit_log_list(request):
    from apps.accounts.models import CustomUser
    from .models import AuditLog

    qs = AuditLog.objects.select_related('user')

    user_id    = request.GET.get('user', '')
    action     = request.GET.get('action', '')
    model_name = request.GET.get('model', '')
    date_from  = request.GET.get('date_from', '')
    date_to    = request.GET.get('date_to', '')

    if user_id:
        qs = qs.filter(user_id=user_id)
    if action:
        qs = qs.filter(action=action)
    if model_name:
        qs = qs.filter(model_name=model_name)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    total_count  = qs.count()
    paginator    = Paginator(qs, AUDIT_PAGE_SIZE)
    page_obj     = paginator.get_page(request.GET.get('page'))

    # Distinct model names for filter dropdown
    model_names = (
        AuditLog.objects.values_list('model_name', flat=True)
        .distinct().order_by('model_name')
    )
    users = CustomUser.objects.filter(is_active=True).order_by('username')

    return render(request, 'reports/audit_log_list.html', {
        'page_obj':    page_obj,
        'total_count': total_count,
        'users':       users,
        'model_names': model_names,
        'user_id':     user_id,
        'action':      action,
        'model_name':  model_name,
        'date_from':   date_from,
        'date_to':     date_to,
    })


# ── Custom Report ─────────────────────────────────────────────────────────────

CUSTOM_REPORT_COLS = [
    ('photo',         'ছবি'),
    ('mp_id',         'এমপি আইডি'),
    ('name_bn',       'নাম (বাংলায়)'),
    ('name_en',       'Name (English)'),
    ('constituency',  'নির্বাচনী এলাকা'),
    ('party',         'রাজনৈতিক দল'),
    ('age',           'বয়স'),
    ('blood_group',   'রক্তের গ্রুপ'),
    ('gender',        'লিঙ্গ'),
    ('religion',      'ধর্ম'),
    ('division',      'বিভাগ'),
    ('district',      'জেলা'),
    ('times_elected', 'নির্বাচনের সংখ্যা'),
    ('committee',     'স্থায়ী কমিটি'),
    ('ministry',      'মন্ত্রণালয়'),
    ('profession',    'পেশা'),
    ('member_type',   'সদস্যের ধরন'),
]
CUSTOM_REPORT_DEFAULT = ['mp_id', 'name_bn', 'constituency', 'party', 'gender', 'district']


def _custom_cell(mp, col, today=None):
    import datetime
    if today is None:
        today = datetime.date.today()
    ei = next(iter(mp.election_infos.all()), None)
    if col == 'mp_id':        return mp.mp_id
    if col == 'name_bn':      return mp.name_bn
    if col == 'name_en':      return mp.name_en
    if col == 'constituency': return ei.constituency.display_bn if ei and ei.constituency else '—'
    if col == 'party':        return ei.party.name_bn if ei and ei.party else '—'
    if col == 'age':
        if mp.dob:
            age = today.year - mp.dob.year - ((today.month, today.day) < (mp.dob.month, mp.dob.day))
            return str(age)
        return '—'
    if col == 'blood_group':   return mp.blood_group.name_bn if mp.blood_group else '—'
    if col == 'gender':        return mp.gender.name_bn if mp.gender else '—'
    if col == 'religion':      return mp.religion.name_bn if mp.religion else '—'
    if col == 'division':
        return mp.home_district.division.name_bn if mp.home_district and mp.home_district.division else '—'
    if col == 'district':      return mp.home_district.name_bn if mp.home_district else '—'
    if col == 'times_elected': return str(ei.times_elected) if ei else '—'
    if col == 'committee':
        return ', '.join(ca.committee.name_bn for ca in mp.committee_assignments.all()) or '—'
    if col == 'ministry':
        return ', '.join(ma.ministry.name_bn for ma in mp.ministry_assignments.all()) or '—'
    if col == 'profession':
        return ', '.join(p.name_bn for p in mp.professions_current.all()) or '—'
    if col == 'member_type':
        return 'সরাসরি নির্বাচিত' if mp.member_type == 'direct' else 'সংরক্ষিত (মহিলা)'
    return '—'


def _build_custom_qs(get, parliament_id):
    """Dynamically build queryset from enabled filters."""
    import datetime

    from django.db.models import Prefetch
    from apps.committee.models import CommitteeAssignment
    from apps.ministry.models import MinistryAssignment
    from apps.mp.models import MP, ElectionInfo

    ei_qs = ElectionInfo.objects.select_related('constituency', 'party')
    if parliament_id:
        ei_qs = ei_qs.filter(parliament_id=parliament_id)

    qs = MP.objects.select_related(
        'parliament', 'gender', 'religion', 'blood_group',
        'home_district__division',
    ).prefetch_related(
        Prefetch('election_infos', queryset=ei_qs),
        'professions_current',
        Prefetch('committee_assignments',
                 queryset=CommitteeAssignment.objects.select_related('committee').filter(is_active=True)),
        Prefetch('ministry_assignments',
                 queryset=MinistryAssignment.objects.select_related('ministry').filter(is_active=True)),
    ).filter(is_active=True)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)

    today = datetime.date.today()
    needs_distinct = False

    # ── MP ID ─────────────────────────────────────────────────────────────────
    if 'enable_mp_id' in get:
        val = get.get('mp_id', '').strip()
        if val:
            qs = qs.filter(mp_id__icontains=val)

    # ── Constituency ──────────────────────────────────────────────────────────
    if 'enable_constituency' in get:
        val = get.get('constituency', '').strip()
        if val:
            qs = qs.filter(
                Q(election_infos__constituency__display_bn__icontains=val) |
                Q(election_infos__constituency__display_en__icontains=val)
            )
            needs_distinct = True

    # ── Age Range ─────────────────────────────────────────────────────────────
    if 'enable_age' in get:
        age_min = get.get('age_min', '').strip()
        age_max = get.get('age_max', '').strip()
        if age_min and age_min.isdigit():
            max_dob = datetime.date(today.year - int(age_min), today.month, today.day)
            qs = qs.filter(dob__lte=max_dob)
        if age_max and age_max.isdigit():
            min_dob = datetime.date(today.year - int(age_max), today.month, today.day)
            qs = qs.filter(dob__gte=min_dob)

    # ── Blood Group ───────────────────────────────────────────────────────────
    if 'enable_blood_group' in get:
        ids = [v for v in get.getlist('blood_group') if v]
        if ids:
            qs = qs.filter(blood_group__in=ids)

    # ── Political Party ───────────────────────────────────────────────────────
    if 'enable_party' in get:
        ids = [v for v in get.getlist('party') if v]
        if ids:
            qs = qs.filter(election_infos__party__in=ids)
            needs_distinct = True

    # ── Division ──────────────────────────────────────────────────────────────
    if 'enable_division' in get:
        ids = [v for v in get.getlist('division') if v]
        if ids:
            qs = qs.filter(home_district__division__in=ids)

    # ── District ──────────────────────────────────────────────────────────────
    if 'enable_district' in get:
        ids = [v for v in get.getlist('district') if v]
        if ids:
            qs = qs.filter(home_district__in=ids)

    # ── Gender ────────────────────────────────────────────────────────────────
    if 'enable_gender' in get:
        ids = [v for v in get.getlist('gender') if v]
        if ids:
            qs = qs.filter(gender__in=ids)

    # ── Religion ──────────────────────────────────────────────────────────────
    if 'enable_religion' in get:
        ids = [v for v in get.getlist('religion') if v]
        if ids:
            qs = qs.filter(religion__in=ids)

    # ── Times Elected ─────────────────────────────────────────────────────────
    if 'enable_times_elected' in get:
        t_min = get.get('times_min', '').strip()
        t_max = get.get('times_max', '').strip()
        if t_min and t_min.isdigit():
            qs = qs.filter(election_infos__times_elected__gte=int(t_min))
            needs_distinct = True
        if t_max and t_max.isdigit():
            qs = qs.filter(election_infos__times_elected__lte=int(t_max))
            needs_distinct = True

    # ── Standing Committee ────────────────────────────────────────────────────
    if 'enable_committee' in get:
        ids = [v for v in get.getlist('committee') if v]
        if ids:
            qs = qs.filter(committee_assignments__committee__in=ids)
            needs_distinct = True

    # ── Ministry ──────────────────────────────────────────────────────────────
    if 'enable_ministry' in get:
        ids = [v for v in get.getlist('ministry') if v]
        if ids:
            qs = qs.filter(ministry_assignments__ministry__in=ids)
            needs_distinct = True

    if needs_distinct:
        qs = qs.distinct()

    return qs


@login_required
def custom_report(request):
    from apps.master.models import (
        BloodGroup, Gender, Religion, Division, District,
        PoliticalParty, StandingCommittee, Ministry,
    )

    fmt           = request.GET.get('format', '')
    parliament_id = _active_parliament_id(request)
    searched      = 'search' in request.GET
    selected_cols = request.GET.getlist('col') or CUSTOM_REPORT_DEFAULT

    # Master data for filter dropdowns (always loaded)
    blood_groups    = BloodGroup.objects.filter(is_active=True)
    genders         = Gender.objects.filter(is_active=True)
    religions       = Religion.objects.filter(is_active=True)
    divisions       = Division.objects.filter(is_active=True)
    districts       = District.objects.filter(is_active=True).select_related('division')
    parties         = PoliticalParty.objects.filter(is_active=True)
    committees      = StandingCommittee.objects.filter(is_active=True)
    ministries      = Ministry.objects.filter(is_active=True)

    # Pre-selected values (restore filter state after search)
    sel = {
        'blood_group':  request.GET.getlist('blood_group'),
        'gender':       request.GET.getlist('gender'),
        'religion':     request.GET.getlist('religion'),
        'division':     request.GET.getlist('division'),
        'district':     request.GET.getlist('district'),
        'party':        request.GET.getlist('party'),
        'committee':    request.GET.getlist('committee'),
        'ministry':     request.GET.getlist('ministry'),
    }

    ctx = {
        'CUSTOM_REPORT_COLS': CUSTOM_REPORT_COLS,
        'selected_cols':      selected_cols,
        'parliament_id':      parliament_id,
        'parliaments':        _parliament_qs(),
        'blood_groups':       blood_groups,
        'genders':            genders,
        'religions':          religions,
        'divisions':          divisions,
        'districts':          districts,
        'parties':            parties,
        'committees':         committees,
        'ministries':         ministries,
        'sel':                sel,
        'searched':           searched,
        'GET':                request.GET,
    }

    if not searched:
        return render(request, 'reports/custom_report.html', ctx)

    qs = _build_custom_qs(request.GET, parliament_id)
    total_count = qs.count()
    ctx['total_count'] = total_count

    import datetime
    today = datetime.date.today()
    data_cols = [c for c in selected_cols if c != 'photo']

    if fmt == 'excel':
        col_labels = {k: v for k, v in CUSTOM_REPORT_COLS}
        headers    = ['ক্রম'] + [col_labels.get(c, c) for c in data_cols]
        rows       = [[i + 1] + [_custom_cell(mp, c, today) for c in data_cols]
                      for i, mp in enumerate(qs)]
        return export_excel('custom_report', headers, rows, 'কাস্টম রিপোর্ট')

    if fmt == 'csv':
        col_labels = {k: v for k, v in CUSTOM_REPORT_COLS}
        headers    = ['ক্রম'] + [col_labels.get(c, c) for c in data_cols]
        rows       = [[i + 1] + [_custom_cell(mp, c, today) for c in data_cols]
                      for i, mp in enumerate(qs)]
        return export_csv('custom_report', headers, rows)

    if fmt == 'print':
        ctx['object_list'] = qs
        ctx['today']       = today
        return render(request, 'reports/print/custom_report.html', ctx)

    paginator = Paginator(qs, PAGE_SIZE)
    ctx['page_obj'] = paginator.get_page(request.GET.get('page'))
    ctx['today']    = today
    return render(request, 'reports/custom_report.html', ctx)


@login_required
def audit_log_detail(request, pk):
    from .models import AuditLog
    log = get_object_or_404(AuditLog.objects.select_related('user'), pk=pk)
    return render(request, 'reports/audit_log_detail.html', {'log': log})
