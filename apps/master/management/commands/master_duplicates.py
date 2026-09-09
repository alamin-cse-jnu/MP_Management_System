"""Report — and optionally merge — duplicate rows in the master reference tables.

    manage.py master_duplicates                      # report everything
    manage.py master_duplicates --model EducationSubject
    manage.py master_duplicates --merge 12:38        # merge 38 into 12
    manage.py master_duplicates --auto-merge         # only the unambiguous sets

`--auto-merge` restricts itself to sets whose rows are **identical in both
languages** once normalised. There is no judgement to make there: whichever row
survives, every screen and report shows exactly the same text as before, so the
merge only moves references. A set whose spellings differ — `জনপ্রশাসন` vs
`লোকপ্রশাসন`, `দ্বিতীয় বিভাগ/Second Division` vs `দ্বিতীয় বিভাগ/2nd Division` — is a
choice about which wording is correct, and is left to a person on
`/master/duplicates/`.
"""

from django.core.management.base import BaseCommand, CommandError

from utils.master_merge import (
    find_duplicate_sets, master_models, merge, norm, suggest_keeper, usage,
)


def _identical(rows):
    """True when every row in the set spells the name the same in both languages."""
    return (len({norm(r.name_bn) for r in rows}) == 1
            and len({norm(getattr(r, 'name_en', '')) for r in rows}) == 1)


class Command(BaseCommand):
    help = 'Report or merge duplicate master data rows.'

    def add_arguments(self, parser):
        parser.add_argument('--model', help='Restrict to one master model, e.g. EducationSubject')
        parser.add_argument('--merge', action='append', default=[], metavar='KEEP:DROP',
                            help='Merge DROP into KEEP (repeatable). Needs --model.')
        parser.add_argument('--auto-merge', action='store_true',
                            help='Merge every set whose rows are identical in both languages.')
        parser.add_argument('--keep-inactive', action='store_true',
                            help='Deactivate merged rows instead of deleting them.')
        parser.add_argument('--exact', action='store_true',
                            help='Match names exactly (ignore spacing/punctuation variants).')

    def handle(self, *args, **opts):
        models = master_models()
        if opts['model']:
            models = [m for m in models if m.__name__.lower() == opts['model'].lower()]
            if not models:
                raise CommandError(f"No master model named {opts['model']!r}.")

        if opts['merge']:
            return self._merge_pairs(models, opts)

        loose = not opts['exact']
        delete = not opts['keep_inactive']
        total_sets = merged = 0

        for model in models:
            sets = find_duplicate_sets(model, loose=loose)
            if not sets:
                continue
            self.stdout.write(self.style.MIGRATE_HEADING(
                f'\n{model.__name__} — {len(sets)} duplicate set(s)'))
            for rows in sets:
                total_sets += 1
                keeper = suggest_keeper(rows)
                used = {r.pk: usage(r)[0] for r in rows}
                for row in rows:
                    mark = 'KEEP' if row.pk == keeper.pk else 'drop'
                    state = 'active  ' if row.is_active else 'inactive'
                    self.stdout.write(
                        f'  [{mark}] id={row.pk:<5} {state} used={used[row.pk]:<4} '
                        f'{row.name_bn} / {getattr(row, "name_en", "")}')

                if not opts['auto_merge']:
                    continue
                if not _identical(rows):
                    self.stdout.write(self.style.WARNING(
                        '         skipped — the spellings differ, so which one wins is a '
                        'decision; merge it on /master/duplicates/'))
                    continue
                summary = merge([r for r in rows if r.pk != keeper.pk], keeper,
                                delete=delete)
                merged += 1
                self.stdout.write(self.style.SUCCESS(
                    f'         merged → id={keeper.pk}; moved {summary["moved"] or "nothing"}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{total_sets} duplicate set(s) found; {merged} merged.'))

    def _merge_pairs(self, models, opts):
        if len(models) != 1:
            raise CommandError('--merge needs exactly one --model.')
        model = models[0]
        for pair in opts['merge']:
            try:
                keep_pk, drop_pk = (int(x) for x in pair.split(':'))
            except ValueError:
                raise CommandError(f'--merge expects KEEP:DROP, got {pair!r}')
            keeper = model._default_manager.get(pk=keep_pk)
            loser = model._default_manager.get(pk=drop_pk)
            summary = merge([loser], keeper, delete=not opts['keep_inactive'])
            self.stdout.write(self.style.SUCCESS(
                f'{model.__name__}: {drop_pk} → {keep_pk}; moved {summary["moved"] or "nothing"}'))
