"""ClassResult master table + the standard class grades.

`Education.class_result` was free text, so picking the "শ্রেণি / Class" result
type revealed an empty box while "বিভাগ / Division" revealed a populated
dropdown. This is the master table that closes that gap; `mp/0013` converts the
field itself.

Seeding matches on the NFC-normalised Bangla name **and** the English name — prod
Bangla is not byte-normalised, so a bn-only `get_or_create` silently duplicates
instead of matching (CLAUDE.md gotcha 17, learned the hard way in `master/0010`).
"""

import unicodedata

from django.db import migrations, models

SEED = [
    ('প্রথম শ্রেণি',  'First Class',  1),
    ('দ্বিতীয় শ্রেণি', 'Second Class', 2),
    ('তৃতীয় শ্রেণি',  'Third Class',  3),
]


def _norm(s):
    return unicodedata.normalize('NFC', (s or '').strip()).casefold()


def seed(apps, schema_editor):
    ClassResult = apps.get_model('master', 'ClassResult')
    existing = [(_norm(r.name_bn), _norm(r.name_en)) for r in ClassResult.objects.all()]
    for name_bn, name_en, order in SEED:
        key_bn, key_en = _norm(name_bn), _norm(name_en)
        if any(key_bn == bn or key_en == en for bn, en in existing):
            continue
        ClassResult.objects.create(name_bn=name_bn, name_en=name_en,
                                   ordering=order, is_active=True)
        existing.append((key_bn, key_en))


def unseed(apps, schema_editor):
    """Reverse: drop only the untouched seeded rows, never an admin's edits."""
    ClassResult = apps.get_model('master', 'ClassResult')
    for name_bn, name_en, _ in SEED:
        ClassResult.objects.filter(name_bn=name_bn, name_en=name_en).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0010_seed_result_masters'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name_bn', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('ordering', models.IntegerField(default=0)),
            ],
            options={'ordering': ['ordering']},
        ),
        migrations.RunPython(seed, unseed),
    ]
