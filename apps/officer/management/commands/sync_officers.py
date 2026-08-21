"""
Sync the Parliament Secretariat officer roster from the PRP employee API.

KEEP-RULE (locked with the user, 2026-08-22):
    class == 1  AND  status == 'Active'  AND  designation present  AND  office present

Everything else is skipped and reported. Officers already in our DB that fall
out of the keep-set are RETIRED (is_active=False + a reason) — never deleted —
so tours they are already on keep working, while they can no longer be searched
or added to a new tour.

Usage:
    python manage.py sync_officers --dry-run
    python manage.py sync_officers
    python manage.py sync_officers --file employees.json     # offline payload
"""

import html
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.officer.models import Officer
from apps.travel.models import ForeignTourOfficer
from utils import prp_api

# A bad API response must not empty the picker: refuse to retire the roster if
# the keep-set collapses to under this fraction of the currently active count.
WIPE_GUARD_RATIO = 0.5


def _clean(raw):
    if raw is None:
        return ''
    return html.unescape(str(raw)).replace('\xa0', ' ').strip()


def _int_or_none(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = 'Sync active Class-1 officers from the PRP employee API'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change without saving')
        parser.add_argument('--file', default=None,
                            help='Read the payload from a saved JSON file instead of the API')
        parser.add_argument('--username', default=None,
                            help='PRP API username (or env PRP_API_USER)')
        parser.add_argument('--password', default=None,
                            help='PRP API password (or env PRP_API_PASS)')
        parser.add_argument('--limit', type=int, default=None,
                            help='Only process the first N records (for testing)')
        parser.add_argument('--force', action='store_true',
                            help='Retire officers even if the wipe-guard trips')

    # ── payload ──────────────────────────────────────────────────────────────
    def _load(self, options):
        if options['file']:
            path = options['file']
            if not os.path.exists(path):
                raise CommandError(f'File not found: {path}')
            self.stdout.write(f'Reading: {path}')
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)
        else:
            self.stdout.write('Authenticating with PRP API…')
            username, password = prp_api.credentials(options['username'], options['password'])
            token = prp_api.get_token(username, password)
            self.stdout.write(f'Fetching: {prp_api.EMPLOYEE_PATH}')
            data = prp_api.secure_get(prp_api.EMPLOYEE_PATH, token, 'Employee data request')
        payload = data.get('payload', data if isinstance(data, list) else [])
        if not isinstance(payload, list):
            raise CommandError('Unexpected payload shape — expected a list of employees.')
        return payload

    # ── keep-rule ────────────────────────────────────────────────────────────
    def _classify(self, rec):
        """Return (keep: bool, skip_reason: str)."""
        if _int_or_none(rec.get('class')) != 1:
            return False, 'not_class_1'
        if _clean(rec.get('status')).lower() != 'active':
            return False, 'inactive'
        has_designation = bool(_clean(rec.get('designationBn')) or _clean(rec.get('designationEn')))
        has_office = bool(rec.get('officeDetails'))
        if not (has_designation and has_office):
            return False, 'incomplete'
        if not (_clean(rec.get('nameBn')) or _clean(rec.get('nameEn'))):
            return False, 'blank_name'
        if not _clean(rec.get('prpId')):
            return False, 'blank_prp_id'
        return True, ''

    def _fields(self, rec):
        od = rec.get('officeDetails') or {}
        return {
            'name_bn':        _clean(rec.get('nameBn')) or _clean(rec.get('nameEn')),
            'name_en':        _clean(rec.get('nameEn')) or _clean(rec.get('nameBn')),
            'designation_bn': _clean(rec.get('designationBn')) or _clean(rec.get('designationEn')),
            'designation_en': _clean(rec.get('designationEn')) or _clean(rec.get('designationBn')),
            'officer_class':  _int_or_none(rec.get('class')) or 1,
            'prp_status':     _clean(rec.get('status')),
            'mobile':         _clean(rec.get('mobile')),
            'telephone':      _clean(rec.get('telephone')),
            'gender':         _clean(rec.get('gender')),
            'wing_id':        _int_or_none(od.get('wingId')),
            'wing_bn':        _clean(od.get('wingNameBn')),
            'wing_en':        _clean(od.get('wingNameEn')),
            'branch_id':      _int_or_none(od.get('branchId')),
            'branch_bn':      _clean(od.get('branchNameBn')),
            'branch_en':      _clean(od.get('branchNameEn')),
            'section_id':     _int_or_none(od.get('sectionId')),
            'section_bn':     _clean(od.get('sectionNameBn')),
            'section_en':     _clean(od.get('sectionNameEn')),
            'office_id':      _int_or_none(od.get('officeId')),
            'office_bn':      _clean(od.get('officeNameBn')),
            'office_en':      _clean(od.get('officeNameEn')),
        }

    def _retire_reason(self, rec):
        """Why a known officer is no longer selectable, given his latest record."""
        if rec is None:
            return Officer.REASON_ABSENT
        if _int_or_none(rec.get('class')) != 1:
            return Officer.REASON_CLASS
        if _clean(rec.get('status')).lower() != 'active':
            return Officer.REASON_INACTIVE
        return Officer.REASON_INCOMPLETE

    # ── main ─────────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        payload = self._load(options)
        if options['limit']:
            payload = payload[:options['limit']]
        self.stdout.write(f'Records received: {len(payload)}')

        keep, skipped, seen_ids, dupes = {}, {}, {}, []
        for rec in payload:
            prp_id = _clean(rec.get('prpId'))
            if prp_id:
                seen_ids.setdefault(prp_id, rec)
            ok, reason = self._classify(rec)
            if not ok:
                skipped[reason] = skipped.get(reason, 0) + 1
                continue
            if prp_id in keep:
                dupes.append(prp_id)
                continue
            keep[prp_id] = rec

        self.stdout.write(f'Keep-set (class 1 · Active · designation · office): {len(keep)}')
        for reason, n in sorted(skipped.items()):
            self.stdout.write(f'  skipped [{reason}]: {n}')
        if dupes:
            self.stdout.write(self.style.WARNING(
                f'  duplicate prpId in keep-set (first wins): {", ".join(sorted(set(dupes)))}'))

        active_now = Officer.objects.selectable().count()
        if active_now and len(keep) < active_now * WIPE_GUARD_RATIO and not options['force']:
            raise CommandError(
                f'Wipe-guard: the API returned only {len(keep)} selectable officers but '
                f'{active_now} are active here. Refusing to retire the roster — the API '
                f'response looks wrong. Re-run with --force if this is genuinely correct.')
        if not keep:
            raise CommandError('Keep-set is empty — nothing to sync.')

        created = updated = unchanged = reactivated = 0
        retired = {}
        now = timezone.now()

        with transaction.atomic():
            existing = {o.prp_id: o for o in Officer.objects.all()}

            for prp_id, rec in keep.items():
                fields = self._fields(rec)
                officer = existing.get(prp_id)
                if officer is None:
                    created += 1
                    if not dry_run:
                        Officer.objects.create(prp_id=prp_id, is_active=True,
                                               last_synced_at=now, **fields)
                    continue
                changed = [f for f, v in fields.items() if getattr(officer, f) != v]
                came_back = not officer.is_active
                if came_back:
                    reactivated += 1
                elif changed:
                    updated += 1
                else:
                    unchanged += 1
                if not dry_run:
                    for f, v in fields.items():
                        setattr(officer, f, v)
                    officer.is_active = True
                    officer.deactivated_at = None
                    officer.deactivated_reason = ''
                    officer.last_synced_at = now
                    officer.save()

            # Retire everyone we know about who is not in the keep-set.
            for prp_id, officer in existing.items():
                if prp_id in keep or not officer.is_active:
                    continue
                reason = self._retire_reason(seen_ids.get(prp_id))
                retired[reason] = retired.get(reason, 0) + 1
                if not dry_run:
                    officer.is_active = False
                    officer.deactivated_at = now
                    officer.deactivated_reason = reason
                    officer.save(update_fields=['is_active', 'deactivated_at',
                                                'deactivated_reason'])

            # Link legacy free-text tour rows whose officer_id matches a PRP ID.
            linked = 0
            if not dry_run:
                by_id = {o.prp_id: o for o in Officer.objects.all()}
                for row in ForeignTourOfficer.objects.filter(
                        officer__isnull=True, is_external=False).exclude(prp_id=''):
                    match = by_id.get(row.prp_id.strip())
                    if match:
                        row.officer = match
                        row.save(update_fields=['officer'])
                        linked += 1
            else:
                ids = set(keep) | set(existing)
                linked = ForeignTourOfficer.objects.filter(
                    officer__isnull=True, is_external=False, prp_id__in=ids).count()

            if dry_run:
                transaction.set_rollback(True)

        style = self.style.WARNING if dry_run else self.style.SUCCESS
        self.stdout.write(style(
            f"{'[DRY RUN] ' if dry_run else ''}"
            f'created {created} · updated {updated} · unchanged {unchanged} · '
            f'reactivated {reactivated} · retired {sum(retired.values())} · '
            f'tour rows linked {linked}'))
        for reason, n in sorted(retired.items()):
            self.stdout.write(f'  retired [{reason}]: {n}')
        self.stdout.write(f"Selectable officers {'would be' if dry_run else 'now'}: {len(keep)}")
