from django.db import migrations

# Add the NOC pages under the Foreign Travel menu on existing DBs
# (fixtures/initial/noc_menu.json covers fresh installs). Issuing an NOC is part
# of managing a tour, so roles that can already work the tour list inherit the
# same rights here — same carry-over shape as 0006_officer_roster_submenu.
SOURCE_URL = 'travel:tour_list'
NEW_SUBMENUS = [
    # url_name,             name_bn,                     name_en,                    ordering
    ('noc:noc_list',      'অনাপত্তি সনদ (NOC)',        'No Objection Certificates', 40),
    ('noc:noc_settings',  'NOC লেটারহেড ও টেমপ্লেট',   'NOC Letterhead & Templates', 50),
]
PERM_FIELDS = ['can_view', 'can_add', 'can_edit', 'can_delete', 'can_export']


def add_submenus(apps, schema_editor):
    Menu = apps.get_model('accounts', 'Menu')
    SubMenu = apps.get_model('accounts', 'SubMenu')
    RolePermission = apps.get_model('accounts', 'RolePermission')

    source = SubMenu.objects.filter(url_name=SOURCE_URL).first()
    menu = source.menu if source else Menu.objects.filter(name_en='Foreign Travel').first()
    if menu is None:
        return

    for url_name, name_bn, name_en, ordering in NEW_SUBMENUS:
        new_sub, created = SubMenu.objects.get_or_create(
            url_name=url_name,
            defaults={'menu': menu, 'name_bn': name_bn, 'name_en': name_en,
                      'ordering': ordering, 'is_active': True},
        )
        if not created or source is None:
            continue
        for rp in RolePermission.objects.filter(submenu=source):
            RolePermission.objects.get_or_create(
                role_id=rp.role_id, submenu=new_sub,
                defaults={f: getattr(rp, f, False) for f in PERM_FIELDS},
            )


def remove_submenus(apps, schema_editor):
    SubMenu = apps.get_model('accounts', 'SubMenu')
    SubMenu.objects.filter(url_name__in=[u for u, _, _, _ in NEW_SUBMENUS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_officer_roster_submenu'),
    ]

    operations = [
        migrations.RunPython(add_submenus, remove_submenus),
    ]
