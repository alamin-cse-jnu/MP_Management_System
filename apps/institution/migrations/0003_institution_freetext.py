from django.db import migrations, models


def copy_institution_to_text(apps, schema_editor):
    """Copy the retired GovernmentInstitution FK label into the new text fields."""
    InstitutionAssignment = apps.get_model('institution', 'InstitutionAssignment')
    for obj in InstitutionAssignment.objects.select_related('institution').all():
        inst = obj.institution
        if inst:
            obj.institution_bn = inst.name_bn or ''
            obj.institution_en = inst.name_en or ''
            obj.save(update_fields=['institution_bn', 'institution_en'])


class Migration(migrations.Migration):

    dependencies = [
        ('institution', '0002_remove_institutionassignment_nomination_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='institutionassignment',
            name='institution_bn',
            field=models.CharField(default='', max_length=300, verbose_name='প্রতিষ্ঠান (বাংলা)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='institutionassignment',
            name='institution_en',
            field=models.CharField(blank=True, max_length=300, verbose_name='Institution (English)'),
        ),
        migrations.RunPython(copy_institution_to_text, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='institutionassignment',
            name='institution',
        ),
        migrations.AlterModelOptions(
            name='institutionassignment',
            options={'ordering': ['institution_bn']},
        ),
    ]
