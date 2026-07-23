from django.db import migrations, models


def copy_designation_to_text(apps, schema_editor):
    """Copy the retired OfficerDesignation FK label into the new text field."""
    ForeignTourOfficer = apps.get_model('travel', 'ForeignTourOfficer')
    for obj in ForeignTourOfficer.objects.select_related('designation').all():
        d = obj.designation
        if d:
            obj.designation_tmp = d.name_bn or d.name_en or ''
            obj.save(update_fields=['designation_tmp'])


class Migration(migrations.Migration):

    dependencies = [
        ('travel', '0002_remove_foreigntourparticipant_departure_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='foreigntourofficer',
            name='designation_tmp',
            field=models.CharField(blank=True, default='', max_length=200,
                                   verbose_name='পদবী / Designation'),
        ),
        migrations.RunPython(copy_designation_to_text, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='foreigntourofficer',
            name='designation',
        ),
        migrations.RenameField(
            model_name='foreigntourofficer',
            old_name='designation_tmp',
            new_name='designation',
        ),
        migrations.AlterField(
            model_name='foreigntourofficer',
            name='designation',
            field=models.CharField(blank=True, max_length=200,
                                   verbose_name='পদবী / Designation'),
        ),
    ]
