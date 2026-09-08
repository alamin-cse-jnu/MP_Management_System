"""Swap education rows whose GPA pair was entered the wrong way round.

The entry form used to show ``gpa_value`` and ``gpa_out_of`` as two bare number
boxes either side of a ``/`` with a single "Result" label above them, so which
box was the earned point and which the scale was a coin flip. MP 013014301 has
a graduation row stored as ``5.00 / 4.75``; every biodata and report reads the
pair through ``Education.result_display``, so the whole system repeats it.

The form now labels both boxes and refuses ``earned > scale``. This repairs the
rows entered before that guard.

Only rows where BOTH halves are present and ``gpa_value > gpa_out_of`` are
touched — that combination is impossible on any real grading scale, so the swap
is a fact, not a guess. A row with only one half filled is left alone: there is
nothing to compare it against.

    python manage.py fix_reversed_gpa --dry-run   # list, change nothing
    python manage.py fix_reversed_gpa             # swap
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from apps.mp.models import Education


class Command(BaseCommand):
    help = 'Swap education GPA pairs stored as scale/earned instead of earned/scale.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change and save nothing.')

    def handle(self, *args, **opts):
        dry = opts['dry_run']

        rows = (Education.objects
                .filter(gpa_value__isnull=False, gpa_out_of__isnull=False)
                .filter(gpa_value__gt=F('gpa_out_of'))
                .select_related('mp', 'education_level', 'result_type')
                .order_by('mp__mp_id', 'ordering', 'id'))

        found = 0
        for edu in rows:
            found += 1
            level = edu.education_level.name_bn if edu.education_level else '—'
            self.stdout.write(
                f'  {edu.mp.mp_id}  {edu.mp.name_bn}  [{level}]  '
                f'{edu.gpa_value} / {edu.gpa_out_of}  →  {edu.gpa_out_of} / {edu.gpa_value}'
            )

        if not found:
            self.stdout.write(self.style.SUCCESS('No reversed GPA pairs found.'))
            return

        if dry:
            self.stdout.write(self.style.WARNING(
                f'\n{found} reversed pair(s). Dry run — nothing saved.'))
            return

        # One statement, so a half-applied swap is not possible. Re-filter inside
        # the transaction rather than reusing the list above: the update must not
        # act on rows that changed since they were read.
        with transaction.atomic():
            changed = 0
            for edu in (Education.objects
                        .filter(gpa_value__isnull=False, gpa_out_of__isnull=False)
                        .filter(gpa_value__gt=F('gpa_out_of'))
                        .select_for_update()):
                edu.gpa_value, edu.gpa_out_of = edu.gpa_out_of, edu.gpa_value
                edu.save(update_fields=['gpa_value', 'gpa_out_of'])
                changed += 1

        self.stdout.write(self.style.SUCCESS(f'\nSwapped {changed} education row(s).'))
