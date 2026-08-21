"""Link tour officers to the PRP-synced roster and make the snapshot bilingual.

`name`/`designation` are RENAMED to `name_bn`/`designation_bn` (preserving the
existing values) and `_en` siblings are added, so the frozen snapshot follows
CRITICAL RULE #2 like every other user-visible field. `officer_id` becomes
`prp_id` because the new `officer` FK claims the `officer_id` attribute.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('officer', '0001_initial'),
        ('travel', '0003_officer_designation_freetext'),
    ]

    operations = [
        migrations.RenameField(
            model_name='foreigntourofficer', old_name='officer_id', new_name='prp_id'),
        migrations.RenameField(
            model_name='foreigntourofficer', old_name='name', new_name='name_bn'),
        migrations.RenameField(
            model_name='foreigntourofficer', old_name='designation', new_name='designation_bn'),
        migrations.AlterField(
            model_name='foreigntourofficer',
            name='prp_id',
            field=models.CharField(blank=True, max_length=50, verbose_name='PRP ID'),
        ),
        migrations.AlterField(
            model_name='foreigntourofficer',
            name='designation_bn',
            field=models.CharField(blank=True, max_length=200,
                                   verbose_name='পদবী / Designation'),
        ),
        migrations.AddField(
            model_name='foreigntourofficer',
            name='name_en',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='foreigntourofficer',
            name='designation_en',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='foreigntourofficer',
            name='is_external',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='foreigntourofficer',
            name='officer',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.PROTECT,
                                    related_name='tour_assignments', to='officer.officer'),
        ),
        migrations.AlterModelOptions(
            name='foreigntourofficer',
            options={'ordering': ['name_bn']},
        ),
    ]
