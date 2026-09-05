"""Seed the parliamentary offices a member can hold on top of the seat.

`SpecialRoleType` existed but was never populated with the offices of the House,
so Speaker / Deputy Speaker / Chief Whip / Whip / Leader of the House / Leader of
the Opposition could not be recorded against anyone. These are the standing
offices of the Jatiya Sangsad; `ordering` is protocol precedence, and the ones
there can only be one of at a time carry `is_unique_per_parliament`.

Matching is on `name_en` (ASCII, byte-stable) rather than `name_bn` — visually
identical Bangla on production can differ in code points, and a bn-keyed
get_or_create silently duplicates instead of matching (CLAUDE.md gotcha 21). An
admin-created row with the same English name is updated in place, never doubled;
nothing already stored is deleted.
"""
from django.db import migrations

# name_bn, name_en, ordering, unique-per-parliament
OFFICES = [
    ('স্পিকার',                     'Speaker',                          10,  True),
    ('ডেপুটি স্পিকার',              'Deputy Speaker',                   20,  True),
    ('সংসদ নেতা',                   'Leader of the House',              30,  True),
    ('সংসদ উপনেতা',                 'Deputy Leader of the House',       40,  True),
    ('বিরোধীদলীয় নেতা',            'Leader of the Opposition',         50,  True),
    ('বিরোধীদলীয় উপনেতা',          'Deputy Leader of the Opposition',  60,  True),
    ('চিফ হুইপ',                    'Chief Whip',                       70,  True),
    ('হুইপ',                        'Whip',                             80,  False),
    ('সভাপতিমণ্ডলীর সদস্য',         'Member, Panel of Chairmen',        90,  False),
    ('সংসদীয় দলের নেতা',           'Parliamentary Party Leader',      100,  False),
]


def seed(apps, schema_editor):
    SpecialRoleType = apps.get_model('master', 'SpecialRoleType')
    for name_bn, name_en, ordering, unique in OFFICES:
        row = SpecialRoleType.objects.filter(name_en__iexact=name_en).first()
        if row is None:
            SpecialRoleType.objects.create(
                name_bn=name_bn, name_en=name_en, ordering=ordering,
                is_unique_per_parliament=unique, is_active=True,
            )
            continue
        # Row already there (hand-entered, or a re-run): only fill in the flag and
        # precedence, never overwrite a name the Secretariat may have corrected.
        row.is_unique_per_parliament = unique
        if not row.ordering:
            row.ordering = ordering
        row.save(update_fields=['is_unique_per_parliament', 'ordering'])


def unseed(apps, schema_editor):
    """Reverse only removes offices nobody was appointed to."""
    SpecialRoleType = apps.get_model('master', 'SpecialRoleType')
    names = [en for _bn, en, _o, _u in OFFICES]
    SpecialRoleType.objects.filter(
        name_en__in=names, specialpositionhistory__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0013_specialroletype_is_unique_per_parliament'),
        ('mp', '0017_alter_specialpositionhistory_options_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
