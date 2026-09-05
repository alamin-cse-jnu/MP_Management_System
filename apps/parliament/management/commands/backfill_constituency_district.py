"""Fill ``Constituency.district`` from the seat name.

The dashboard's constituency-basis division chart (and the district-wise report
with ``basis=constituency``) reach the division through
``constituency → district → division``. That FK is admin-entered and nullable,
so on a fresh database it is empty and every constituency-basis view looks
broken when it is only unpopulated.

Seat names are regular — ``৬ দিনাজপুর-১`` / ``6 Dinajpur-1`` — so the district
name is the middle piece: drop the leading serial and the trailing ``-<n>``.
The remainder is matched against District rows on English name first (ASCII,
so byte-stable) and Bangla name second, both normalised: Bangla on production
is NOT byte-normalised, so an unnormalised ``name_bn`` compare silently misses
(see CLAUDE.md gotcha 21).

Nothing is guessed. A seat whose name does not resolve to exactly one district
is reported and left alone for manual entry through the constituency UI.

    python manage.py backfill_constituency_district --dry-run
    python manage.py backfill_constituency_district
    python manage.py backfill_constituency_district --overwrite   # re-check rows
                                                                  # that already
                                                                  # have a district
"""
import re
import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.master.models import District
from apps.parliament.models import Constituency


# Seat names and the District master disagree on a handful of spellings, and
# which side carries the "old" one varies by row — so these are equivalence
# groups, not a one-way rewrite: whichever spelling exists in the master wins
# and the rest resolve to it. An early one-way map turned Netrokona (spelled
# that way in BOTH tables) from a hit into a miss.
ALIAS_GROUPS = [
    ('chittagong', 'chattogram', 'chattagram'),
    ('comilla', 'cumilla'),
    ('barisal', 'barishal'),
    ('jessore', 'jashore'),
    ('bogra', 'bogura'),
    ('jhalokati', 'jhalakathi', 'jhalokathi'),
    ('netrokona', 'netrakona'),
    ('moulvibazar', 'maulvibazar', 'moulavibazar'),
    ('brahminbaria', 'brahmanbaria'),
    ('chapainawabganj', 'chapainababganj', 'nawabganj'),
    ('coxsbazar', 'coxbazar', 'coxsbazaar'),
    ('rangamati', 'rangamatiparbatya'),
]


def _norm_en(text):
    """Lowercase, strip everything but a-z0-9 — spelling noise, not identity."""
    return re.sub(r'[^a-z0-9]', '', (text or '').lower())


def _norm_bn(text):
    """NFC-normalise and drop whitespace/punctuation before comparing Bangla."""
    text = unicodedata.normalize('NFC', text or '')
    return re.sub(r'[\s​-‏\-–—.]', '', text)


def _is_reserved(c):
    """Seats 301-350 are women's reserved seats — no constituency district by
    rule (business rule 2), so they are skipped, not reported as failures."""
    if c.ordering and c.ordering > 300:
        return True
    return 'women seat' in (c.display_en or '').lower() or 'মহিলা আসন' in (c.display_bn or '')


def _core(display):
    """'৬ দিনাজপুর-১' → 'দিনাজপুর'   |   '6 Dinajpur-1' → 'Dinajpur'."""
    text = (display or '').strip()
    # leading serial, ASCII or Bangla digits, plus its separator
    text = re.sub(r'^[\d০-৯]+[\s.\-–—]+', '', text)
    # trailing seat number after the last dash
    text = re.sub(r'[\-–—]\s*[\d০-৯]+\s*$', '', text)
    return text.strip()


class Command(BaseCommand):
    help = "Set Constituency.district from the seat name (district-wise reports need it)."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report matches and misses, save nothing.')
        parser.add_argument('--overwrite', action='store_true',
                            help='Also re-check constituencies that already have a district.')

    def handle(self, *args, **opts):
        dry       = opts['dry_run']
        overwrite = opts['overwrite']

        districts = list(District.objects.filter(is_active=True).select_related('division'))
        by_en, by_bn = {}, {}
        for d in districts:
            by_en.setdefault(_norm_en(d.name_en), d)
            by_bn.setdefault(_norm_bn(d.name_bn), d)
        # Alternate spellings resolve to whichever member of the group the
        # master table actually uses; an exact master name is never overwritten.
        for group in ALIAS_GROUPS:
            known = next((by_en[g] for g in group if g in by_en), None)
            if known is None:
                continue
            for g in group:
                by_en.setdefault(g, known)

        qs = Constituency.objects.select_related('district')
        if not overwrite:
            qs = qs.filter(district__isnull=True)

        matched, unmatched, unchanged, reserved = [], [], 0, 0
        for c in qs.order_by('ordering', 'id'):
            if _is_reserved(c):
                reserved += 1          # rule 2: reserved seats have no district
                continue
            en_key = _norm_en(_core(c.display_en))
            # Alias only as a fallback — the master table already uses some of
            # the "old" spellings, and rewriting first turned a hit into a miss.
            dist = by_en.get(en_key) or by_bn.get(_norm_bn(_core(c.display_bn)))
            if dist is None:
                unmatched.append(c)
                continue
            if c.district_id == dist.id:
                unchanged += 1
                continue
            matched.append((c, dist))

        for c, d in matched:
            self.stdout.write(f"  {c.display_bn}  →  {d.name_bn} / {d.name_en}"
                              f"  ({d.division.name_bn if d.division else '—'})")
        for c in unmatched:
            self.stdout.write(self.style.WARNING(
                f"  UNRESOLVED  {c.display_bn} ({c.display_en}) — set the district by hand"))

        self.stdout.write('')
        self.stdout.write(f"to set: {len(matched)}   already correct: {unchanged}   "
                          f"reserved (skipped): {reserved}   unresolved: {len(unmatched)}")

        if dry:
            self.stdout.write(self.style.NOTICE('dry run — nothing saved'))
            return

        with transaction.atomic():
            for c, d in matched:
                c.district = d
                c.save(update_fields=['district'])
        self.stdout.write(self.style.SUCCESS(f"saved {len(matched)} constituencies"))
