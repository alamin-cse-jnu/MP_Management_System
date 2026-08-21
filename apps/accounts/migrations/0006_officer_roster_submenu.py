from django.db import migrations

# Add the PRP officer roster page under the Foreign Travel menu on existing DBs
# (fixtures/initial/officer_menu.json covers fresh installs). Roles that can
# already edit the tour list get the same rights here, since syncing the roster
# is part of managing tours.
NEW_URL = 'officer:officer_list'
SOURCE_URL = 'travel:tour_list'
PERM_FIELDS = ['can_view', 'can_add', 'can_edit', 'can_delete', 'can_export']


def add_submenu(apps, schema_editor):
    Menu = apps.get_model('accounts', 'Menu')
    SubMenu = apps.get_model('accounts', 'SubMenu')
    RolePermission = apps.get_model('accounts', 'RolePermission')

    source = SubMenu.objects.filter(url_name=SOURCE_URL).first()
    menu = source.menu if source else Menu.objects.filter(name_en='Foreign Travel').first()
    if menu is None:
        return

    new_sub, created = SubMenu.objects.get_or_create(
        url_name=NEW_URL,
        defaults={'menu': menu, 'name_bn': 'কর্মকর্তা তালিকা (PRP)',
                  'name_en': 'Officer Roster (PRP)', 'ordering': 30,
                  'is_active': True},
    )
    if not created or source is None:
        return

    for rp in RolePermission.objects.filter(submenu=source):
        RolePermission.objects.get_or_create(
            role_id=rp.role_id, submenu=new_sub,
            defaults={f: getattr(rp, f, False) for f in PERM_FIELDS},
        )


def remove_submenu(apps, schema_editor):
    SubMenu = apps.get_model('accounts', 'SubMenu')
    SubMenu.objects.filter(url_name=NEW_URL).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_consolidate_ministry_committee'),
    ]

    operations = [
        migrations.RunPython(add_submenu, remove_submenu),
    ]
