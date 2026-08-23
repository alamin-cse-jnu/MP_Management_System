from django.db import migrations

# The education page's Result box is driven by ResultType.result_format: picking a
# type reveals the matching input. Two of those formats need their OWN master rows
# to be usable at all — 'division' renders a DivisionResult dropdown, which was
# empty on every DB, so choosing "বিভাগ" revealed a select with no options and the
# Result box looked broken. Seed the canonical options, and the standard result
# types themselves, so every format the form supports is reachable out of the box.
# get_or_create never touches an admin-created row.

DIVISION_RESULTS = [
    # name_bn,        name_en,        ordering
    ('প্রথম বিভাগ',   '1st Division',  10),
    ('দ্বিতীয় বিভাগ', '2nd Division',  20),
    ('তৃতীয় বিভাগ',   '3rd Division',  30),
    ('উত্তীর্ণ',       'Pass',          40),
]

# Keyed on result_format — one canonical type per format the education form knows.
RESULT_TYPES = [
    # result_format, name_bn,          name_en,      ordering
    ('division',    'বিভাগ',           'Division',    10),
    ('class',       'শ্রেণি',          'Class',       20),
    ('gpa',         'জিপিএ',           'GPA',         30),
    ('cgpa',        'সিজিপিএ',         'CGPA',        40),
    ('percentage',  'শতকরা',           'Percentage',  50),
    ('pass_fail',   'উত্তীর্ণ/অনুত্তীর্ণ', 'Pass/Fail',   60),
]


def seed(apps, schema_editor):
    DivisionResult = apps.get_model('master', 'DivisionResult')
    ResultType     = apps.get_model('master', 'ResultType')

    for name_bn, name_en, ordering in DIVISION_RESULTS:
        DivisionResult.objects.get_or_create(
            name_bn=name_bn,
            defaults={'name_en': name_en, 'ordering': ordering, 'is_active': True},
        )

    for result_format, name_bn, name_en, ordering in RESULT_TYPES:
        ResultType.objects.get_or_create(
            result_format=result_format,
            defaults={'name_bn': name_bn, 'name_en': name_en,
                      'ordering': ordering, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0009_alter_educationgroup_applicable_to'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
