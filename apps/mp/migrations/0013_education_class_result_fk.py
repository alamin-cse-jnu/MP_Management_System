"""Education.class_result: free-text CharField → FK to master.ClassResult.

Hand-written. The rename-then-backfill-then-drop sequence exists so no typed
value is lost: anything already in the text column is matched to a ClassResult
(NFC-normalised, on either language), and **a master row is created for any value
that has no match** — so the column can be dropped afterwards knowing nothing was
silently discarded.

Production at the time of writing held one such row: 'First Class'.
"""

import unicodedata

import django.db.models.deletion
from django.db import migrations, models


def _norm(s):
    return unicodedata.normalize('NFC', (s or '').strip()).casefold()


def to_fk(apps, schema_editor):
    Education = apps.get_model('mp', 'Education')
    ClassResult = apps.get_model('master', 'ClassResult')

    lookup = {}
    for row in ClassResult.objects.all():
        lookup.setdefault(_norm(row.name_bn), row.pk)
        lookup.setdefault(_norm(row.name_en), row.pk)

    next_order = (ClassResult.objects.count() or 0) + 1
    qs = Education.objects.exclude(class_result_legacy='').exclude(
        class_result_legacy__isnull=True)
    for pk, raw in qs.values_list('pk', 'class_result_legacy'):
        key = _norm(raw)
        target = lookup.get(key)
        if target is None:
            # Unrecognised free text — preserve it as a new master row rather
            # than dropping it on the floor.
            row = ClassResult.objects.create(
                name_bn=raw.strip(), name_en=raw.strip(),
                ordering=next_order, is_active=True)
            next_order += 1
            target = row.pk
            lookup[key] = target
        Education.objects.filter(pk=pk).update(class_result_id=target)


def to_text(apps, schema_editor):
    """Reverse: write the master row's Bangla name back into the text column."""
    Education = apps.get_model('mp', 'Education')
    for edu in Education.objects.exclude(class_result__isnull=True).select_related(
            'class_result'):
        Education.objects.filter(pk=edu.pk).update(
            class_result_legacy=edu.class_result.name_bn[:50])


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0012_personalforeigntravel'),
        ('master', '0011_class_result'),
    ]

    operations = [
        migrations.RenameField(
            model_name='education',
            old_name='class_result',
            new_name='class_result_legacy',
        ),
        migrations.AddField(
            model_name='education',
            name='class_result',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='master.classresult', verbose_name='শ্রেণি'),
        ),
        migrations.RunPython(to_fk, to_text),
        migrations.RemoveField(
            model_name='education',
            name='class_result_legacy',
        ),
    ]
