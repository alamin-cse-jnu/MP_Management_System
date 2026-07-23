"""
PRP API sync engine — shared helpers, alias maps, a field registry, and the
conflict-detection / resolution logic used by both the import_mp_api command
(``--sync`` mode) and the conflict-review views.

Sync policy (see memory/project_api_import.md):
  * This system is canonical. Sync never blindly overwrites.
  * Empty API value  → never touches the system value.
  * System empty, API has value → auto-fill (not a conflict).
  * Both filled and differ → record an MPSyncConflict (pending) for UI review.
  * Collections (bank/spouse/child) are ADD-ONLY: API rows missing here are
    added; rows here but missing from the API are flagged (never auto-deleted).
"""

import html
from datetime import date, datetime

from django.utils import timezone

# ── Alias maps (API value → DB name_en, lower-case keys) ──────────────────────
# Kept in sync with import_mp_excel.py. Extend as --dry-run / --sync reveals
# unresolved values against the real database.

DISTRICT_ALIASES = {
    'bogra':             'bogura',
    'chapai nababganj':  'chapainawabganj',
    'jessore':           'jashore',
    'barisal':           'barishal',
    'jhalokati':         'jhalakathi',
    'netrakona':         'netrokona',
    'kishoregonj':       'kishoreganj',
    'comilla':           'cumilla',
    'chittagong':        'chattogram',
    "cox's bazar":       'coxsbazar',
    'khagrachhari':      'khagrachari',
}
RELIGION_ALIASES = {
    'hinduism':  'shonaton (hinduism)',
    'buddhisn':  'buddhism',
}
PARTY_ALIASES = {}
MARITAL_ALIASES = {}
BLOODGROUP_ALIASES = {}


# ── Value cleaners ────────────────────────────────────────────────────────────

def clean(raw):
    if raw is None:
        return ''
    return html.unescape(str(raw)).replace('\xa0', ' ').strip()


def norm_mobile(raw):
    s = clean(raw)
    if s.startswith('880') and len(s) == 13:
        return '0' + s[3:]
    return s


def parse_date(raw):
    s = clean(raw)
    if not s:
        return None
    try:
        return datetime.strptime(s, '%d/%m/%Y').date()
    except ValueError:
        return None


def resolve(lookup_map, raw_value, alias_map=None):
    key = clean(raw_value).lower()
    if not key:
        return None
    if alias_map:
        key = alias_map.get(key, key)
    return lookup_map.get(key)


def resolve_bloodgroup(bg_map, raw):
    key = clean(raw).lower()
    if not key:
        return None
    key = BLOODGROUP_ALIASES.get(key, key)
    if key in bg_map:
        return bg_map[key]
    alt = key.replace('positive', '+').replace('negative', '-').replace(' ', '')
    return bg_map.get(alt)


def dig(rec, path):
    """Traverse a nested dict via a tuple path, returning '' if any hop misses."""
    cur = rec
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return ''
    return cur


# ── Lookup maps ───────────────────────────────────────────────────────────────

def build_maps():
    from apps.master.models import (
        BloodGroup, District, Gender, MaritalStatus, PoliticalParty, Religion,
    )
    from apps.parliament.models import Constituency
    return {
        'religion':     {r.name_en.lower(): r for r in Religion.objects.all()},
        'district':     {d.name_en.lower(): d for d in District.objects.all()},
        'gender':       {g.name_en.lower(): g for g in Gender.objects.all()},
        'marital':      {m.name_en.lower(): m for m in MaritalStatus.objects.all()},
        'bloodgroup':   {b.name_en.lower(): b for b in BloodGroup.objects.all()},
        'party':        {p.name_en.lower(): p for p in PoliticalParty.objects.all()},
        'constituency': {c.ordering: c for c in Constituency.objects.all()},
    }


# ── Field registry ────────────────────────────────────────────────────────────
# (key, label, target, attr, vtype, path, mapname, alias)
# vtype ∈ scalar | mobile | date | int | fk | bloodgroup | constituency

GEN = 'generalInformation'
PAS = ('generalInformation', 'passportInformation')
ELE = 'mpElectionInformation'
CON = 'contactAddress'

FIELD_SPECS = [
    # ── MP ────────────────────────────────────────────────────────────────────
    ('name_bn',        'নাম (বাংলা)',        'mp', 'name_bn',        'scalar', (GEN, 'nameBn'),        None, None),
    ('name_en',        'Name (English)',      'mp', 'name_en',        'scalar', (GEN, 'nameEn'),        None, None),
    ('father_name_bn', 'পিতা (বাংলা)',       'mp', 'father_name_bn', 'scalar', (GEN, 'fatherNameBn'),  None, None),
    ('father_name_en', "Father's Name",       'mp', 'father_name_en', 'scalar', (GEN, 'fatherNameEn'),  None, None),
    ('mother_name_bn', 'মাতা (বাংলা)',       'mp', 'mother_name_bn', 'scalar', (GEN, 'motherNameBn'),  None, None),
    ('mother_name_en', "Mother's Name",       'mp', 'mother_name_en', 'scalar', (GEN, 'motherNameEn'),  None, None),
    ('nid',            'জাতীয় পরিচয়পত্র',  'mp', 'nid',            'scalar', (GEN, 'nid'),           None, None),
    ('tin',            'টিআইএন',             'mp', 'tin',            'scalar', (GEN, 'tin'),           None, None),
    ('dob',            'জন্ম তারিখ',         'mp', 'dob',            'date',   (GEN, 'dob'),           None, None),
    ('gender',         'লিঙ্গ',              'mp', 'gender',         'fk',     (GEN, 'gender'),        'gender', None),
    ('religion',       'ধর্ম',               'mp', 'religion',       'fk',     (GEN, 'religion'),      'religion', RELIGION_ALIASES),
    ('marital_status', 'বৈবাহিক অবস্থা',     'mp', 'marital_status', 'fk',     (GEN, 'maritalStatus'), 'marital', MARITAL_ALIASES),
    ('home_district',  'নিজ জেলা',           'mp', 'home_district',  'fk',     (GEN, 'homeDistrict'),  'district', DISTRICT_ALIASES),
    ('birth_district', 'জন্মস্থান (জেলা)',   'mp', 'birth_district', 'fk',     (GEN, 'birthDistrict'), 'district', DISTRICT_ALIASES),
    ('blood_group',    'রক্তের গ্রুপ',       'mp', 'blood_group',    'bloodgroup', (GEN, 'bloodGroup'), None, None),
    ('passport_number',     'পাসপোর্ট নং',       'mp', 'passport_number',     'scalar', PAS + ('passportNo',),   None, None),
    ('passport_issue_date', 'পাসপোর্ট ইস্যু',    'mp', 'passport_issue_date', 'date',   PAS + ('dateOfIssue',),  None, None),
    ('passport_expiry_date','পাসপোর্ট মেয়াদ',   'mp', 'passport_expiry_date','date',   PAS + ('dateOfExpiry',), None, None),
    ('passport_issue_place','পাসপোর্ট স্থান',    'mp', 'passport_issue_place','scalar', PAS + ('placeOfIssue',), None, None),
    # ── Election ────────────────────────────────────────────────────────────────
    ('party',         'রাজনৈতিক দল',    'election', 'party',         'fk',           (ELE, 'politicalParty'),       'party', PARTY_ALIASES),
    ('constituency',  'নির্বাচনী এলাকা', 'election', 'constituency',  'constituency', (ELE, 'constituencyNoAndName'), None, None),
    ('times_elected', 'কতবার নির্বাচিত', 'election', 'times_elected', 'int',          (ELE, 'electedCount'),         None, None),
    ('election_date', 'নির্বাচনের তারিখ','election', 'election_date', 'date',         (ELE, 'dateOfElection'),       None, None),
    ('gazette_date',  'গেজেটের তারিখ',   'election', 'gazette_date',  'date',         (ELE, 'dateOfGazette'),        None, None),
    ('oath_date',     'শপথের তারিখ',     'election', 'oath_date',     'date',         (ELE, 'dateOfOath'),           None, None),
    # ── Contact (present address) ───────────────────────────────────────────────
    ('mobile',         'মোবাইল',          'address', 'mobile',         'mobile', (CON, 'mobile'),            None, None),
    ('alt_mobile',     'বিকল্প মোবাইল',   'address', 'alt_mobile',     'mobile', (CON, 'alternativeMobile'), None, None),
    ('whatsapp',       'হোয়াটসঅ্যাপ',    'address', 'whatsapp',       'mobile', (CON, 'whatsappNo'),        None, None),
    ('email',          'দাপ্তরিক ই-মেইল', 'address', 'email',          'scalar', (CON, 'officialEmail'),     None, None),
    ('personal_email', 'ব্যক্তিগত ই-মেইল','address', 'personal_email', 'scalar', (CON, 'personalEmail'),     None, None),
]


def _api_value(spec, rec, maps):
    """Return (compare_value, api_ref, raw_present, unresolved_raw).

    compare_value is what we compare against the system: an object for fk types,
    a date for dates, an int for int, else a cleaned string. api_ref is the
    string persisted so a resolution can re-apply the value later.
    """
    _, _, _, _, vtype, path, mapname, alias = spec
    raw = dig(rec, path)
    raw_present = bool(clean(raw))

    if vtype in ('scalar',):
        v = clean(raw)
        return v, v, raw_present, None
    if vtype == 'mobile':
        v = norm_mobile(raw)
        return v, v, raw_present, None
    if vtype == 'date':
        d = parse_date(raw)
        return d, (d.isoformat() if d else ''), raw_present, None
    if vtype == 'int':
        s = clean(raw)
        try:
            v = int(s) if s else None
        except ValueError:
            v = None
        return v, ('' if v is None else str(v)), raw_present, None
    if vtype in ('fk', 'bloodgroup', 'constituency'):
        if vtype == 'fk':
            obj = resolve(maps[mapname], raw, alias)
        elif vtype == 'bloodgroup':
            obj = resolve_bloodgroup(maps['bloodgroup'], raw)
        else:  # constituency by leading seat number
            obj = None
            s = clean(raw)
            try:
                obj = maps['constituency'].get(int(s.split()[0]))
            except (ValueError, IndexError):
                obj = None
        unresolved = clean(raw) if (raw_present and obj is None) else None
        return obj, ('' if obj is None else str(obj.pk)), raw_present, unresolved
    return None, '', raw_present, None


def _display(vtype, value):
    if value is None or value == '':
        return ''
    if vtype == 'date':
        return value.isoformat() if isinstance(value, date) else str(value)
    return str(value)


# ── Detection ─────────────────────────────────────────────────────────────────

def sync_existing_mp(rec, mp, maps, *, dry_run=False, unresolved=None):
    """Detect field + collection differences for one existing MP.

    Returns a stats dict. Autofills empty fields directly (unless dry_run) and
    upserts MPSyncConflict rows for genuine divergences. `unresolved` (a dict) is
    populated with API values that couldn't be resolved to a master row.
    """
    from apps.mp.models import (
        Address, BankAccount, Child, ElectionInfo, MPSyncConflict, Spouse,
    )
    stats = {'autofilled': 0, 'conflicts': 0, 'added': 0, 'removals': 0}
    seen_keys = set()  # (target, field_key) detected this run

    election = ElectionInfo.objects.filter(mp=mp, parliament=mp.parliament).first()
    address = Address.objects.filter(mp=mp, address_type='present').first()
    if not dry_run:
        if election is None:
            election = ElectionInfo.objects.create(mp=mp, parliament=mp.parliament)
        if address is None:
            address = Address.objects.create(mp=mp, address_type='present')
    targets = {'mp': mp, 'election': election, 'address': address}
    dirty = set()

    def record_conflict(target, field_key, **defaults):
        seen_keys.add((target, field_key))
        if dry_run:
            stats['conflicts'] += 1
            return
        obj, created = MPSyncConflict.objects.get_or_create(
            mp=mp, target=target, field_key=field_key,
            defaults={**defaults, 'status': 'pending'},
        )
        if not created:
            # Respect an earlier human resolution unless the API changed again.
            if obj.api_ref != defaults.get('api_ref', ''):
                for k, v in defaults.items():
                    setattr(obj, k, v)
                obj.status = 'pending'
                obj.resolution = ''
                obj.resolved_at = None
                obj.resolved_by = None
                obj.save()
            elif obj.status == 'pending':
                obj.system_value = defaults.get('system_value', obj.system_value)
                obj.save(update_fields=['system_value', 'detected_at'])
        stats['conflicts'] += 1

    # ── scalar / fk / date / int fields ──────────────────────────────────────
    for spec in FIELD_SPECS:
        key, label, target, attr, vtype, path, mapname, alias = spec
        tgt = targets[target]
        api_val, api_ref, raw_present, unresolved_raw = _api_value(spec, rec, maps)

        if unresolved_raw and unresolved is not None:
            unresolved.setdefault(key, {})
            unresolved[key][unresolved_raw] = unresolved[key].get(unresolved_raw, 0) + 1

        # nothing coming from the API → never touch the system
        if api_val in (None, ''):
            continue
        if tgt is None:  # dry-run with no election/address row yet
            continue

        cur = getattr(tgt, attr)
        stored_vtype = 'fk' if vtype in ('fk', 'bloodgroup', 'constituency') else vtype

        if stored_vtype == 'fk':
            cur_empty = cur is None
            same = (cur is not None and cur.pk == api_val.pk)
            cur_disp = _display('fk', cur)
        elif vtype == 'date':
            cur_empty = cur is None
            same = (cur == api_val)
            cur_disp = _display('date', cur)
        elif vtype == 'int':
            cur_empty = cur is None
            same = (cur == api_val)
            cur_disp = _display('int', cur)
        else:  # scalar / mobile
            cur_s = (cur or '').strip()
            cur_empty = cur_s == ''
            same = (cur_s == api_val)
            cur_disp = cur_s

        if cur_empty:
            setattr(tgt, attr, api_val)
            dirty.add(target)
            stats['autofilled'] += 1
        elif not same:
            record_conflict(
                target, key, kind='field', attr=attr, label=label,
                value_type=stored_vtype,
                system_value=cur_disp,
                api_value=_display('date' if vtype == 'date' else stored_vtype, api_val),
                api_ref=api_ref,
            )

    if not dry_run:
        for t in dirty:
            targets[t].save()

    # ── collections (add-only; flag removals) ────────────────────────────────
    def sync_collection(target, api_rows, key_of, existing_qs, create_fn, describe):
        existing = {}
        for row in existing_qs:
            existing.setdefault(key_of(row), row)
        api_keys = set()
        for data in api_rows:
            k = key_of(data)
            if not k:
                continue
            api_keys.add(k)
            if k not in existing:
                if not dry_run:
                    create_fn(data)
                stats['added'] += 1
        for k, row in existing.items():
            if k and k not in api_keys:
                record_conflict(
                    target, f'{target}.{k}', kind='remove', attr='',
                    label=describe(row), value_type='',
                    system_value=describe(row), api_value='(not in API)',
                    api_ref=str(row.pk),
                )
                stats['removals'] += 1

    def bank_key(x):
        return clean(x.get('accountNo') if isinstance(x, dict) else x.account_number)

    def make_bank(b):
        acct = clean(b.get('accountNo'))
        bank = clean(b.get('bankName'))
        at = {1: 'savings', 2: 'current'}.get(b.get('accountType'), 'other')
        BankAccount.objects.create(
            mp=mp, account_number=acct, bank_name_bn=bank, bank_name_en=bank,
            branch_name_en=clean(b.get('branchName')), account_type=at,
        )

    sync_collection(
        'bank', rec.get('bankInfos') or [], bank_key,
        mp.bank_accounts.all(), make_bank,
        lambda r: f'{r.bank_name_en or r.bank_name_bn} — {r.account_number}',
    )

    def person_key(x, dob_attr='dob'):
        if isinstance(x, dict):
            return (clean(x.get('nid')) or clean(x.get('birthRegistrationNo'))
                    or clean(x.get('nameEn')) or clean(x.get('nameBn')))
        return (clean(x.nid) or clean(getattr(x, 'nid_or_birth_reg', ''))
                or clean(x.name_en) or clean(x.name_bn))

    def make_spouse(s):
        nm_bn, nm_en = clean(s.get('nameBn')), clean(s.get('nameEn'))
        Spouse.objects.create(
            mp=mp, name_bn=nm_bn or nm_en, name_en=nm_en,
            dob=parse_date(s.get('dob')), nid=clean(s.get('nid')),
            tin=clean(s.get('tin')), gender=resolve(maps['gender'], s.get('gender')),
        )

    sync_collection(
        'spouse', rec.get('spouses') or [], person_key,
        mp.spouses.all(), make_spouse,
        lambda r: r.name_en or r.name_bn,
    )

    child_rows = rec.get('children') or []
    child_counter = {'n': mp.children.count()}

    def make_child(c):
        nm_bn, nm_en = clean(c.get('nameBn')), clean(c.get('nameEn'))
        child_counter['n'] += 1
        Child.objects.create(
            mp=mp, serial=child_counter['n'], name_bn=nm_bn or nm_en, name_en=nm_en,
            dob=parse_date(c.get('dob')),
            nid_or_birth_reg=clean(c.get('nid')) or clean(c.get('birthRegistrationNo')),
            gender=resolve(maps['gender'], c.get('gender')),
        )

    sync_collection(
        'child', child_rows, person_key,
        mp.children.all(), make_child,
        lambda r: r.name_en or r.name_bn,
    )

    # ── clear stale pending conflicts that no longer apply ───────────────────
    if not dry_run:
        stale = MPSyncConflict.objects.filter(mp=mp, status='pending')
        for c in stale:
            if (c.target, c.field_key) not in seen_keys:
                c.delete()

    return stats


# ── Resolution (called from the review view) ──────────────────────────────────

def apply_conflict(conflict, user, choice):
    """Apply a resolution ('system' or 'api') to one MPSyncConflict."""
    from apps.mp.models import Address, BankAccount, Child, ElectionInfo, Spouse

    if choice == 'api':
        if conflict.kind == 'field':
            tgt = {
                'mp': conflict.mp,
                'election': ElectionInfo.objects.filter(
                    mp=conflict.mp, parliament=conflict.mp.parliament).first(),
                'address': Address.objects.filter(
                    mp=conflict.mp, address_type='present').first(),
            }.get(conflict.target)
            if tgt is not None:
                vt = conflict.value_type
                if vt == 'fk':
                    model = tgt._meta.get_field(conflict.attr).related_model
                    val = model.objects.filter(pk=conflict.api_ref).first() if conflict.api_ref else None
                elif vt == 'date':
                    val = date.fromisoformat(conflict.api_ref) if conflict.api_ref else None
                elif vt == 'int':
                    val = int(conflict.api_ref) if conflict.api_ref else None
                else:
                    val = conflict.api_ref
                setattr(tgt, conflict.attr, val)
                tgt.save()
        elif conflict.kind == 'remove':
            model = {'bank': BankAccount, 'spouse': Spouse, 'child': Child}.get(conflict.target)
            if model and conflict.api_ref:
                model.objects.filter(pk=conflict.api_ref).delete()

    conflict.status = 'resolved'
    conflict.resolution = 'api' if choice == 'api' else 'system'
    conflict.resolved_by = user
    conflict.resolved_at = timezone.now()
    conflict.save()
