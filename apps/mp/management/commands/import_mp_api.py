"""
Import MP data from the PRP API (prp.parliament.gov.bd) JSON payload.

Sibling of import_mp_excel.py — same helpers / alias conventions, extended to
cover passport, blood group, marital status, parents, bank accounts, spouses,
children, and photo/signature downloads.

Source: a saved JSON file (default API_Data.txt) OR a live URL via --url.
The payload shape is:  {"responseCode": 200, "payload": [ {mp record}, ... ]}

Design decisions (see memory/project_api_import.md):
  * Unmatched dropdown values are FLAGGED (WARN) and left null — never guessed.
    Run --dry-run first; the summary lists every unresolved value so you can add
    an alias line below (or the missing master row) and re-run.
  * presentOccupation is skipped entirely (dirty free-text; also empty for family).
  * Contact goes on the MP's 'present' Address row (matches import_mp_excel.py).
  * Reserved MPs (seat >= 301) DO get a constituency FK — the 301–350
    "Women Seat-N" rows exist and are matched by ordering, same as direct seats.
"""

import json
import os
import urllib.request

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.mp.models import MP, Address, BankAccount, Child, ElectionInfo, Spouse
from apps.parliament.models import Parliament
from apps.mp import api_sync
from utils import prp_api
from apps.mp.api_sync import (
    DISTRICT_ALIASES, MARITAL_ALIASES, PARTY_ALIASES, RELIGION_ALIASES,
    build_maps,
    clean as _clean,
    norm_mobile as _norm_mobile,
    parse_date as _parse_date,
    resolve as _resolve,
    resolve_bloodgroup as _resolve_bloodgroup,
)

User = get_user_model()

BASE_URL = prp_api.BASE_URL
DATA_PATH = '/api/secure/external?action=mpdata_list&parliamentNo={pno}'


class Command(BaseCommand):
    help = 'Import MP data from the PRP API JSON payload (default: API_Data.txt)'

    def add_arguments(self, parser):
        parser.add_argument('json_file', nargs='?', default='API_Data.txt',
                            help='Path to the JSON payload (default: API_Data.txt)')
        parser.add_argument('--fetch', action='store_true',
                            help='Fetch live from the PRP API (token auth) instead of a file')
        parser.add_argument('--username', default=os.environ.get('PRP_API_USER'),
                            help='PRP API username (or env PRP_API_USER)')
        parser.add_argument('--password', default=os.environ.get('PRP_API_PASS'),
                            help='PRP API password (or env PRP_API_PASS)')
        parser.add_argument('--parliament-no', type=int, default=13,
                            help='parliamentNo query param for the data endpoint (default: 13)')
        parser.add_argument('--url', default=None,
                            help='Fetch the raw payload from this exact URL (no auth)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Validate and report unresolved values without saving')
        parser.add_argument('--update', action='store_true',
                            help='Force-overwrite MPs that already exist (default: skip them). '
                                 'Prefer --sync for conflict-safe updates.')
        parser.add_argument('--sync', action='store_true',
                            help='For existing MPs, detect differences into the conflict '
                                 'queue instead of overwriting (auto-fills empty fields).')
        parser.add_argument('--no-images', action='store_true',
                            help='Do not download photo/signature images')
        parser.add_argument('--images-only', action='store_true',
                            help='Only (re)download photo/signature for existing MPs; '
                                 'touches nothing else. Use with --fetch for fresh URLs+token.')
        parser.add_argument('--limit', type=int, default=None,
                            help='Only process the first N records (for testing)')

    # ── auth + load payload ────────────────────────────────────────────────────
    # The HTTP plumbing lives in utils/prp_api.py, shared with sync_officers.
    def _fetch_json(self, req, what, timeout=180):
        return prp_api.fetch_json(req, what, timeout=timeout)

    def _get_token(self, username, password):
        username, password = prp_api.credentials(username, password)
        if not (username and password):
            raise CommandError('--fetch needs --username/--password (or env '
                               'PRP_API_USER / PRP_API_PASS).')
        return prp_api.get_token(username, password)

    def _load(self, options):
        if options['fetch']:
            self.stdout.write('Authenticating with PRP API…')
            token = self._get_token(options['username'], options['password'])
            self.token = token  # reused to authorize image downloads
            url = BASE_URL + DATA_PATH.format(pno=options['parliament_no'])
            self.stdout.write(f'Fetching: {url}')
            req = urllib.request.Request(url, headers={
                'Authorization': token,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            })
            data = self._fetch_json(req, 'MP data request')
        elif options['url']:
            self.stdout.write(f"Fetching: {options['url']}")
            data = self._fetch_json(urllib.request.Request(options['url']), 'MP data request')
        else:
            path = options['json_file']
            if not os.path.exists(path):
                raise CommandError(f'File not found: {path}')
            self.stdout.write(f'Reading: {path}')
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)
        payload = data.get('payload', data if isinstance(data, list) else [])
        if not payload:
            raise CommandError('No records found in payload.')
        return payload

    def _download(self, url, field, filename, warns, label):
        """Download an image URL into an ImageField (unsaved). Warn on failure."""
        url = _clean(url)
        if not url:
            return
        headers = {}
        if getattr(self, 'token', None):
            headers['Authorization'] = self.token
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60,
                                        context=prp_api.ssl_context()) as resp:
                data = resp.read()
                ctype = resp.headers.get('Content-Type', '').lower()
        except Exception as exc:  # noqa: BLE001
            warns.append(f'{label} download failed: {exc}')
            return
        if not data:
            warns.append(f'{label}: empty response')
            return
        if 'image' not in ctype and not (b'\xff\xd8' == data[:2] or data[:8] == b'\x89PNG\r\n\x1a\n'):
            # Not an image (e.g. an HTML/JSON error page) — don't save garbage.
            warns.append(f'{label}: non-image response (Content-Type: {ctype or "?"})')
            return
        ext = 'png' if 'png' in ctype or data[:8] == b'\x89PNG\r\n\x1a\n' else 'jpg'
        field.save(f'{filename}.{ext}', ContentFile(data), save=False)

    def handle(self, *args, **options):
        dry_run     = options['dry_run']
        do_update   = options['update']
        do_sync     = options['sync']
        skip_images = options['no_images']
        self.token  = None

        payload = self._load(options)
        if options['limit']:
            payload = payload[:options['limit']]

        # ── images-only backfill: (re)download photo/signature, nothing else ──
        if options['images_only']:
            # PRP publishes elected members only. Technocrat ministers are
            # locally entered and have no prpId, so they are never matched,
            # created or overwritten by the API.
            existing = {mp.mp_id: mp for mp in MP.objects.parliament_members()}
            done = missing = 0
            for rec in payload:
                mp_id = _clean(rec.get('prpId'))
                mp = existing.get(mp_id)
                if not mp:
                    missing += 1
                    continue
                warns = []
                self._download(rec.get('image'), mp.photo, f'{mp_id}_photo', warns, 'photo')
                self._download(rec.get('signature'), mp.signature, f'{mp_id}_sign', warns, 'signature')
                mp.save(update_fields=['photo', 'signature'])
                done += 1
                self.stdout.write(
                    f'  IMG   {mp_id} | photo={bool(mp.photo)} signature={bool(mp.signature)}'
                    + (self.style.WARNING(f'  ⚠ {"; ".join(warns)}') if warns else ''))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'Images processed for {done} MP(s); {missing} record(s) had no matching MP.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be saved'))

        # ── Pre-load lookup maps ──────────────────────────────────────────────
        parliament = (Parliament.objects.filter(ordinal=13).first()
                      or Parliament.objects.filter(name_en__icontains='13').first())
        if not parliament:
            raise CommandError('13th Parliament not found in database.')

        maps             = build_maps()
        religion_map     = maps['religion']
        district_map     = maps['district']
        gender_map       = maps['gender']
        marital_map      = maps['marital']
        bloodgroup_map   = maps['bloodgroup']
        party_map        = maps['party']
        constituency_map = maps['constituency']
        # Technocrats excluded — the PRP roster covers elected members only.
        existing         = {mp.mp_id: mp
                            for mp in MP.objects.parliament_members().filter(parliament=parliament)}

        total = skipped = created = updated = errors = 0
        synced = conflicts = autofilled = 0
        error_log = []
        unresolved = {}  # field -> Counter-like dict of raw values

        def flag(field, value):
            unresolved.setdefault(field, {})
            unresolved[field][value] = unresolved[field].get(value, 0) + 1

        for rec in payload:
            total += 1
            gi   = rec.get('generalInformation', {}) or {}
            ei   = rec.get('mpElectionInformation', {}) or {}
            ca   = rec.get('contactAddress', {}) or {}
            pp   = gi.get('passportInformation', {}) or {}
            mp_id = _clean(rec.get('prpId'))
            name_en = _clean(gi.get('nameEn'))

            existing_mp = existing.get(mp_id)

            # ── existing MP + --sync: detect conflicts instead of overwriting ──
            if existing_mp and do_sync:
                try:
                    st = api_sync.sync_existing_mp(
                        rec, existing_mp, maps, dry_run=dry_run, unresolved=unresolved,
                    )
                    # Backfill missing photo/signature only (system-canonical:
                    # never overwrite an image the system already has).
                    img_warns = []
                    if not skip_images and not dry_run:
                        img_changed = []
                        if not existing_mp.photo:
                            self._download(rec.get('image'), existing_mp.photo,
                                           f'{mp_id}_photo', img_warns, 'photo')
                            if existing_mp.photo:
                                img_changed.append('photo')
                        if not existing_mp.signature:
                            self._download(rec.get('signature'), existing_mp.signature,
                                           f'{mp_id}_sign', img_warns, 'signature')
                            if existing_mp.signature:
                                img_changed.append('signature')
                        if img_changed:
                            existing_mp.save(update_fields=img_changed)
                    synced += 1
                    conflicts  += st['conflicts']
                    autofilled += st['autofilled']
                    note = (f"conflicts={st['conflicts']} filled={st['autofilled']} "
                            f"added={st['added']} removals={st['removals']}")
                    self.stdout.write(f'  SYNC  {mp_id} | {name_en} | {note}'
                                      + (self.style.WARNING(f'  ⚠ {"; ".join(img_warns)}')
                                         if img_warns else ''))
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    msg = f'{mp_id} | {name_en} | {exc}'
                    error_log.append(msg)
                    self.stdout.write(self.style.ERROR(f'  ERROR {msg}'))
                continue

            if existing_mp and not do_update:
                skipped += 1
                self.stdout.write(f'  SKIP  {mp_id} | {name_en} (exists)')
                continue

            # ── constituency + member type (seat number = ordering) ───────────
            constituency_obj = None
            member_type = 'direct'
            con_str = _clean(ei.get('constituencyNoAndName'))
            if con_str:
                try:
                    seat = int(con_str.split()[0])
                    member_type = 'reserved' if seat >= 301 else 'direct'
                    constituency_obj = constituency_map.get(seat)
                    if not constituency_obj:
                        flag('constituency', con_str)
                except (ValueError, IndexError):
                    flag('constituency', con_str)

            # ── resolve FK fields (flag misses) ───────────────────────────────
            def R(m, raw, alias=None, fname=None):
                obj = _resolve(m, raw, alias)
                if raw and not obj and fname:
                    flag(fname, _clean(raw))
                return obj

            gender        = R(gender_map,   gi.get('gender'),        None, 'gender')
            religion      = R(religion_map, gi.get('religion'),      RELIGION_ALIASES, 'religion')
            marital       = R(marital_map,  gi.get('maritalStatus'), MARITAL_ALIASES, 'maritalStatus')
            home_district = R(district_map, gi.get('homeDistrict'),  DISTRICT_ALIASES, 'homeDistrict')
            birth_district= R(district_map, gi.get('birthDistrict'), DISTRICT_ALIASES, 'birthDistrict')
            blood_group   = _resolve_bloodgroup(bloodgroup_map, gi.get('bloodGroup'))
            if _clean(gi.get('bloodGroup')) and not blood_group:
                flag('bloodGroup', _clean(gi.get('bloodGroup')))
            party         = R(party_map,    ei.get('politicalParty'), PARTY_ALIASES, 'politicalParty')

            dob = _parse_date(gi.get('dob'))
            try:
                times_elected = int(ei.get('electedCount') or 1)
            except (ValueError, TypeError):
                times_elected = 1

            if dry_run:
                self.stdout.write(
                    f'  OK    {mp_id} | {name_en} | {member_type} | '
                    f'con={constituency_obj} | party={party} | '
                    f'spouses={len(rec.get("spouses") or [])} '
                    f'children={len(rec.get("children") or [])} '
                    f'banks={len(rec.get("bankInfos") or [])}'
                )
                created += 1
                continue

            # ── Save ──────────────────────────────────────────────────────────
            warns = []
            try:
                with transaction.atomic():
                    defaults = dict(
                        parliament     = parliament,
                        member_type    = member_type,
                        name_bn        = _clean(gi.get('nameBn')) or name_en,
                        name_en        = name_en,
                        father_name_bn = _clean(gi.get('fatherNameBn')),
                        father_name_en = _clean(gi.get('fatherNameEn')),
                        mother_name_bn = _clean(gi.get('motherNameBn')),
                        mother_name_en = _clean(gi.get('motherNameEn')),
                        dob            = dob,
                        nid            = _clean(gi.get('nid')) or None,
                        gender         = gender,
                        religion       = religion,
                        marital_status = marital,
                        blood_group    = blood_group,
                        home_district  = home_district,
                        birth_district = birth_district,
                        tin            = _clean(gi.get('tin')),
                        passport_number      = _clean(pp.get('passportNo')),
                        passport_issue_date  = _parse_date(pp.get('dateOfIssue')),
                        passport_expiry_date = _parse_date(pp.get('dateOfExpiry')),
                        passport_issue_place = _clean(pp.get('placeOfIssue')),
                    )
                    if _clean(gi.get('nationality')).lower() == 'bangladeshi':
                        defaults['nationality_bn'] = 'বাংলাদেশী'
                        defaults['nationality_en'] = 'Bangladeshi'

                    # Safety net: never let the API convert a locally entered
                    # technocrat minister into an elected member, even if their
                    # manually assigned mp_id happens to match a prpId.
                    if MP.objects.technocrats().filter(mp_id=mp_id).exists():
                        skipped += 1
                        self.stdout.write(self.style.WARNING(
                            f'  SKIP  {mp_id} | {name_en} (technocrat — not synced from PRP)'))
                        continue

                    mp, was_created = MP.objects.update_or_create(
                        mp_id=mp_id, defaults=defaults,
                    )

                    if not skip_images:
                        self._download(rec.get('image'), mp.photo,
                                       f'{mp_id}_photo', warns, 'photo')
                        self._download(rec.get('signature'), mp.signature,
                                       f'{mp_id}_sign', warns, 'signature')
                        if mp.photo or mp.signature:
                            mp.save(update_fields=['photo', 'signature'])

                    ElectionInfo.objects.update_or_create(
                        mp=mp, parliament=parliament,
                        defaults=dict(
                            constituency  = constituency_obj,
                            party         = party,
                            election_date = _parse_date(ei.get('dateOfElection')),
                            gazette_date  = _parse_date(ei.get('dateOfGazette')),
                            oath_date     = _parse_date(ei.get('dateOfOath')),
                            times_elected = times_elected,
                        ),
                    )

                    Address.objects.update_or_create(
                        mp=mp, address_type='present',
                        defaults=dict(
                            mobile         = _norm_mobile(ca.get('mobile')),
                            alt_mobile     = _norm_mobile(ca.get('alternativeMobile')),
                            whatsapp       = _norm_mobile(ca.get('whatsappNo')),
                            email          = _clean(ca.get('officialEmail')),
                            personal_email = _clean(ca.get('personalEmail')),
                        ),
                    )

                    # Re-sync children collections (idempotent under --update)
                    mp.bank_accounts.all().delete()
                    for b in (rec.get('bankInfos') or []):
                        acc = _clean(b.get('accountNo'))
                        if not acc:
                            continue
                        at = {1: 'savings', 2: 'current'}.get(b.get('accountType'), 'other')
                        bank = _clean(b.get('bankName'))
                        BankAccount.objects.create(
                            mp=mp, account_number=acc,
                            bank_name_bn=bank, bank_name_en=bank,
                            branch_name_en=_clean(b.get('branchName')),
                            account_type=at,
                        )

                    mp.spouses.all().delete()
                    for s in (rec.get('spouses') or []):
                        nm_bn = _clean(s.get('nameBn'))
                        nm_en = _clean(s.get('nameEn'))
                        if not (nm_bn or nm_en):
                            continue
                        Spouse.objects.create(
                            mp=mp, name_bn=nm_bn or nm_en, name_en=nm_en,
                            dob=_parse_date(s.get('dob')),
                            nid=_clean(s.get('nid')), tin=_clean(s.get('tin')),
                            gender=_resolve(gender_map, s.get('gender')),
                        )

                    mp.children.all().delete()
                    for i, c in enumerate(rec.get('children') or [], start=1):
                        nm_bn = _clean(c.get('nameBn'))
                        nm_en = _clean(c.get('nameEn'))
                        if not (nm_bn or nm_en):
                            continue
                        Child.objects.create(
                            mp=mp, serial=i, name_bn=nm_bn or nm_en, name_en=nm_en,
                            dob=_parse_date(c.get('dob')),
                            nid_or_birth_reg=(_clean(c.get('nid'))
                                              or _clean(c.get('birthRegistrationNo'))),
                            gender=_resolve(gender_map, c.get('gender')),
                        )

                existing[mp_id] = mp
                if was_created:
                    created += 1
                    tag = self.style.SUCCESS('SAVED')
                else:
                    updated += 1
                    tag = self.style.SUCCESS('UPDT ')
                self.stdout.write(f'  {tag} {mp_id} | {name_en}'
                                  + (f'  ⚠ {"; ".join(warns)}' if warns else ''))

            except Exception as exc:  # noqa: BLE001
                errors += 1
                msg = f'{mp_id} | {name_en} | {exc}'
                error_log.append(msg)
                self.stdout.write(self.style.ERROR(f'  ERROR {msg}'))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write('─' * 60)
        self.stdout.write(f'Total records : {total}')
        self.stdout.write(f'Skipped       : {skipped} (already in DB)')
        self.stdout.write(f'{"Would create" if dry_run else "Created"}      : {created}')
        if do_sync:
            self.stdout.write(f'Synced        : {synced} existing MP(s)')
            self.stdout.write(f'  auto-filled : {autofilled} empty field(s)')
            self.stdout.write(f'  conflicts   : {conflicts} flagged for review')
        if not dry_run:
            self.stdout.write(f'Updated       : {updated}')
            self.stdout.write(f'Errors        : {errors}')
        self.stdout.write('─' * 60)

        if do_sync and conflicts and not dry_run:
            self.stdout.write(self.style.WARNING(
                '\nReview conflicts in the UI:  MP → Sync Conflicts'))

        if unresolved:
            self.stdout.write(self.style.WARNING('\nUNRESOLVED VALUES (add an alias or master row, then re-run):'))
            for field, values in sorted(unresolved.items()):
                self.stdout.write(self.style.WARNING(f'  {field}:'))
                for val, n in sorted(values.items(), key=lambda kv: -kv[1]):
                    self.stdout.write(f'      {n:4} × "{val}"')

        if error_log:
            self.stdout.write(self.style.ERROR('\nFailed records:'))
            for msg in error_log:
                self.stdout.write(self.style.ERROR(f'  {msg}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run complete. Re-run without --dry-run to import.'))
        elif errors == 0:
            self.stdout.write(self.style.SUCCESS('\nImport complete — no errors.'))
        else:
            self.stdout.write(self.style.WARNING(f'\nImport complete with {errors} error(s).'))
