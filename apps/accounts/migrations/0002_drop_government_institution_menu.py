from django.db import migrations


def drop_menu(apps, schema_editor):
    """Remove retired master menu links (Phase 17.9 institution, 17.10 officer)."""
    SubMenu = apps.get_model('accounts', 'SubMenu')
    SubMenu.objects.filter(url_name__in=[
        'master:government_institution_list',
        'master:officer_designation_list',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(drop_menu, migrations.RunPython.noop),
    ]
