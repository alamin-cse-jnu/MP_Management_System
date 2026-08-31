# -*- coding: utf-8 -*-
from django.db import migrations

# The MP COVID form's "টিকার নাম" dropdown is fed by VaccineName, which was empty
# on every DB — so the field looked broken (a select with no options, and no
# obvious place to fill it). Seed the vaccines actually administered in
# Bangladesh's COVID-19 programme; an operator can still add/soft-delete rows in
# Master Data → কোভিড-১৯ → টিকার নাম.
#
# Matched on name_en, NOT name_bn: Bangla text on prod is not byte-normalised,
# so a bn-keyed get_or_create silently inserts visual duplicates.

VACCINES = [
    # name_bn,                  name_en,                    ordering
    ('অক্সফোর্ড-অ্যাস্ট্রাজেনেকা', 'Oxford-AstraZeneca',        10),
    ('কোভিশিল্ড',                 'Covishield',                20),
    ('সিনোফার্ম',                 'Sinopharm',                 30),
    ('সিনোভ্যাক',                 'Sinovac',                   40),
    ('ফাইজার-বায়োএনটেক',        'Pfizer-BioNTech',           50),
    ('মডার্না',                   'Moderna',                   60),
    ('জনসন অ্যান্ড জনসন',        'Johnson & Johnson (Janssen)', 70),
    ('স্পুতনিক-ভি',               'Sputnik V',                 80),
]


def seed(apps, schema_editor):
    VaccineName = apps.get_model('master', 'VaccineName')
    for name_bn, name_en, ordering in VACCINES:
        VaccineName.objects.get_or_create(
            name_en=name_en,
            defaults={'name_bn': name_bn, 'ordering': ordering, 'is_active': True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0011_class_result'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
