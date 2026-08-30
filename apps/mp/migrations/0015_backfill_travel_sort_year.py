"""Backfill PersonalForeignTravel.sort_year for rows created before 0014.

`sort_year` is maintained by `save()`, so any row written before the column
existed is left NULL. `Meta.ordering` leads with `sort_year DESC nulls_last`, so
those rows sink below every later row regardless of how recent they are — a 2012
trip entered yesterday would rank under a 1998 trip entered today.

Three such rows existed on production when this was written.
"""

from django.db import migrations


def backfill(apps, schema_editor):
    Travel = apps.get_model('mp', 'PersonalForeignTravel')
    for pk, from_date, year in Travel.objects.filter(
            sort_year__isnull=True).values_list('pk', 'from_date', 'year'):
        value = from_date.year if from_date else year
        if value is not None:
            Travel.objects.filter(pk=pk).update(sort_year=value)


def noop(apps, schema_editor):
    """Reverse: leave the values in place — they are derived, not authored."""


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0014_alter_personalforeigntravel_options_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
