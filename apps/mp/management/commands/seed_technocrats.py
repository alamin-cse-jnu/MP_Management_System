"""Seed the technocrat ministers listed in docs/technocrat.md.

Technocrat ministers are cabinet members who hold no parliamentary seat. They
are stored as MP rows with ``member_type='technocrat'`` (no ElectionInfo — no
constituency, party, oath or gazette date) plus one MinistryAssignment per
ministry held.

Idempotent: re-running updates nothing that already exists and never creates
duplicate assignments. Master rows (Ministry, MinisterType) are resolved by
bn-then-en name and reported when unresolved — never guessed or auto-created,
matching the policy in apps/mp/api_sync.py.

    python manage.py seed_technocrats --dry-run
    python manage.py seed_technocrats

On a database whose Ministry / MinisterType master tables are still empty, pass
``--create-masters`` to create exactly the rows named above (and nothing else).
Every created row is printed. Without the flag the command reports what is
missing and creates no master data.
"""
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.master.models import Ministry, MinisterType
from apps.mp.models import MP
from apps.ministry.models import MinistryAssignment
from apps.parliament.models import Parliament


APPOINTED = datetime.date(2026, 2, 17)

# mp_id values assigned by the Secretariat.
TECHNOCRATS = [
    {
        'mp_id':     '013050101',
        'name_bn':   'ড. খলিলুর রহমান',
        'name_en':   'Dr. Khalilur Rahman',
        'position':  ('মন্ত্রী', 'Minister'),
        'ministries': [('পররাষ্ট্র মন্ত্রণালয়', 'Ministry of Foreign Affairs')],
        'appointed': APPOINTED,
    },
    {
        'mp_id':     '013050201',
        'name_bn':   'মোঃ আমিনুল হক',
        'name_en':   'Md. Aminul Haque',
        'position':  ('প্রতিমন্ত্রী', 'State Minister'),
        'ministries': [('যুব ও ক্রীড়া মন্ত্রণালয়', 'Ministry of Youth and Sports')],
        'appointed': APPOINTED,
    },
    {
        'mp_id':     '013050301',
        'name_bn':   'মোহাম্মদ আমিন উর রশিদ',
        'name_en':   'Mohammad Amin Ur Rashid',
        'position':  ('মন্ত্রী', 'Minister'),
        'ministries': [
            ('মৎস্য ও প্রাণিসম্পদ মন্ত্রণালয়', 'Ministry of Fisheries and Livestock'),
            ('কৃষি মন্ত্রণালয়',                  'Ministry of Agriculture'),
        ],
        'appointed': APPOINTED,
    },
]


def _resolve(model, name_bn, name_en):
    """Find a master row by Bangla name, then English. Never creates."""
    obj = model.objects.filter(name_bn=name_bn).first()
    if obj:
        return obj
    return model.objects.filter(name_en__iexact=name_en).first()


class Command(BaseCommand):
    help = 'Seed technocrat ministers (docs/technocrat.md) and their ministry assignments.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would change; write nothing.')
        parser.add_argument('--parliament', type=int, default=None,
                            help='Parliament pk (default: the active parliament).')
        parser.add_argument('--create-masters', action='store_true',
                            help='Create the Ministry / MinisterType rows named in '
                                 'docs/technocrat.md if they are missing. Off by '
                                 'default — normally masters are entered in the UI.')

    def handle(self, *args, **options):
        dry = options['dry_run']
        make_masters = options['create_masters']

        # Under --dry-run nothing is written, so a master "created" for the first
        # technocrat would look missing again for the next one. Remember the
        # pretend-creates so the report counts each row once.
        pretend = {}

        def resolve(model, name_bn, name_en):
            """Resolve a master row, optionally creating it under --create-masters."""
            obj = _resolve(model, name_bn, name_en)
            if obj or not make_masters:
                return obj
            key = (model.__name__, name_bn)
            if key in pretend:
                return pretend[key]
            self.stdout.write(self.style.SUCCESS(
                f'  +MASTER {model.__name__}: {name_bn} ({name_en})'))
            if dry:
                # Unsaved instance: truthy for the caller, never touches the DB
                # because every write below is guarded by `if not dry`.
                obj = model(name_bn=name_bn, name_en=name_en)
            else:
                obj = model.objects.create(name_bn=name_bn, name_en=name_en)
            pretend[key] = obj
            return obj

        if options['parliament']:
            parliament = Parliament.objects.filter(pk=options['parliament']).first()
        else:
            parliament = Parliament.objects.filter(is_active=True).first()
        if not parliament:
            self.stderr.write(self.style.ERROR(
                'No active parliament found. Load fixtures/initial/parliament_data.json first.'))
            return

        self.stdout.write(f'Parliament: {parliament}')
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing will be written.\n'))

        unresolved = []
        created_mps = created_assigns = skipped = 0

        with transaction.atomic():
            for spec in TECHNOCRATS:
                mp_id = spec['mp_id']

                pos_bn, pos_en = spec['position']
                minister_type = resolve(MinisterType, pos_bn, pos_en)
                if not minister_type:
                    unresolved.append(f'MinisterType: {pos_bn} ({pos_en})')

                clash = MP.objects.filter(mp_id=mp_id).exclude(
                    member_type='technocrat').first()
                if clash:
                    self.stderr.write(self.style.ERROR(
                        f'  CLASH {mp_id} already belongs to elected member '
                        f'"{clash.name_bn}" — assign a different mp_id.'))
                    continue

                mp = MP.objects.filter(mp_id=mp_id).first()
                if mp:
                    skipped += 1
                    self.stdout.write(f'  EXISTS {mp_id} | {spec["name_en"]}')
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'  MP     {mp_id} | {spec["name_en"]} | technocrat'))
                    created_mps += 1
                    if not dry:
                        mp = MP.objects.create(
                            mp_id       = mp_id,
                            parliament  = parliament,
                            member_type = 'technocrat',
                            name_bn     = spec['name_bn'],
                            name_en     = spec['name_en'],
                        )

                for min_bn, min_en in spec['ministries']:
                    ministry = resolve(Ministry, min_bn, min_en)
                    if not ministry:
                        unresolved.append(f'Ministry: {min_bn} ({min_en})')
                        continue
                    if not minister_type:
                        continue
                    # In a dry run the MP and/or the master row may be unsaved,
                    # so the "already assigned?" query cannot be made — just
                    # report what would be created.
                    if dry and (mp is None or ministry.pk is None
                                or minister_type.pk is None):
                        self.stdout.write(f'    +MIN {min_en} — {pos_en}')
                        created_assigns += 1
                        continue

                    exists = MinistryAssignment.objects.filter(
                        mp=mp, parliament=parliament, ministry=ministry).exists()
                    if exists:
                        self.stdout.write(f'    EXISTS {min_en}')
                        continue
                    self.stdout.write(self.style.SUCCESS(f'    +MIN {min_en} — {pos_en}'))
                    created_assigns += 1
                    if not dry:
                        MinistryAssignment.objects.create(
                            mp            = mp,
                            parliament    = parliament,
                            ministry      = ministry,
                            minister_type = minister_type,
                            start_date    = spec['appointed'],
                            is_active     = True,
                        )

            if dry:
                transaction.set_rollback(True)

        if unresolved:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(
                'Unresolved master data — add these in Master Data, then re-run '
                '(or re-run with --create-masters to create exactly these rows):'))
            for u in sorted(set(unresolved)):
                self.stdout.write(self.style.ERROR(f'  • {u}'))

        self.stdout.write('')
        self.stdout.write(
            f'MPs created: {created_mps} | already present: {skipped} | '
            f'assignments created: {created_assigns}')
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — rolled back.'))
