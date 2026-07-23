from django.db import migrations

# Phase 17.11: the redesigned education page has fixed level-sections. Guarantee a
# canonical EducationLevel row exists for each so the sectioned form always works.
# get_or_create by level_type never duplicates an admin-created row of that type.
LEVELS = [
    # level_type,    name_bn,              name_en,               degree_order, ordering
    ('secondary',   'এসএসসি',              'SSC',                  2,  20),
    ('higher_sec',  'এইচএসসি',             'HSC',                  3,  30),
    ('diploma',     'ডিপ্লোমা/ভোকেশনাল',   'Diploma/Vocational',   3,  35),
    ('bachelor',    'স্নাতক',              'Graduation (Bachelor)', 4,  40),
    ('masters',     'স্নাতকোত্তর',          'Masters',              5,  50),
    ('phd',         'পিএইচডি',             'PhD',                  6,  60),
]


def seed_levels(apps, schema_editor):
    EducationLevel = apps.get_model('master', 'EducationLevel')
    for level_type, name_bn, name_en, degree_order, ordering in LEVELS:
        EducationLevel.objects.get_or_create(
            level_type=level_type,
            defaults={
                'name_bn': name_bn, 'name_en': name_en,
                'degree_order': degree_order, 'ordering': ordering,
                'is_active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0007_delete_officerdesignation'),
    ]

    operations = [
        migrations.RunPython(seed_levels, migrations.RunPython.noop),
    ]
