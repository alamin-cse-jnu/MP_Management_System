"""Split MP.nationality into the bilingual pair the rest of the system uses.

Written by hand: ``makemigrations`` proposes RemoveField + AddField, which drops
every stored nationality. RenameField keeps the column and its data.

The English backfill matches on the Bangla value, so it is NFC-normalised first
— Bangla on production is not byte-normalised and a naive ``==`` silently misses
visually identical strings (see GOTCHAS in CLAUDE.md). Anything that is not
recognisably "Bangladeshi" is left blank for an operator to fill in.
"""

import unicodedata

from django.db import migrations, models

_BANGLADESHI_BN = {'বাংলাদেশী', 'বাংলাদেশি'}


def fill_nationality_en(apps, schema_editor):
    MP = apps.get_model('mp', 'MP')
    for pk, bn in MP.objects.values_list('pk', 'nationality_bn'):
        norm = unicodedata.normalize('NFC', (bn or '').strip())
        value = 'Bangladeshi' if norm in _BANGLADESHI_BN else ''
        MP.objects.filter(pk=pk).update(nationality_en=value)


def clear_nationality_en(apps, schema_editor):
    """Reverse: nothing to restore — nationality_bn is the surviving column."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0010_spouse_passport'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mp',
            old_name='nationality',
            new_name='nationality_bn',
        ),
        migrations.AlterField(
            model_name='mp',
            name='nationality_bn',
            field=models.CharField(blank=True, default='বাংলাদেশী', max_length=100,
                                   verbose_name='জাতীয়তা (বাংলায়)'),
        ),
        migrations.AddField(
            model_name='mp',
            name='nationality_en',
            field=models.CharField(blank=True, default='Bangladeshi', max_length=100,
                                   verbose_name='Nationality'),
        ),
        migrations.RunPython(fill_nationality_en, clear_nationality_en),
    ]
