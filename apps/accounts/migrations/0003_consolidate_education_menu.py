from django.db import migrations

OLD_URLS = [
    'master:education_level_list',
    'master:education_group_list',
    'master:education_subject_list',
    'master:degree_name_list',
    'master:education_institution_list',
    'master:result_type_list',
    'master:division_result_list',
]
NEW_URL = 'master:education_master'
PERM_FIELDS = ['can_view', 'can_add', 'can_edit', 'can_delete', 'can_export']


def consolidate(apps, schema_editor):
    """Replace the 7 separate education master submenus with one consolidated
    entry, carrying each role's combined education permissions to the new one."""
    Menu = apps.get_model('accounts', 'Menu')
    SubMenu = apps.get_model('accounts', 'SubMenu')
    RolePermission = apps.get_model('accounts', 'RolePermission')

    old_subs = list(SubMenu.objects.filter(url_name__in=OLD_URLS))

    menu = old_subs[0].menu if old_subs else Menu.objects.filter(name_en='Master Data').first()
    if menu is None:
        return

    new_sub, _ = SubMenu.objects.get_or_create(
        url_name=NEW_URL,
        defaults={'menu': menu, 'name_bn': 'শিক্ষা মাস্টার ডেটা',
                  'name_en': 'Education Master Data', 'ordering': 50, 'is_active': True},
    )

    # Carry over permissions: union of the role's perms across the old submenus.
    agg = {}
    for rp in RolePermission.objects.filter(submenu__in=old_subs):
        cur = agg.setdefault(rp.role_id, {f: False for f in PERM_FIELDS})
        for f in PERM_FIELDS:
            cur[f] = cur[f] or getattr(rp, f, False)
    for role_id, perms in agg.items():
        RolePermission.objects.update_or_create(
            role_id=role_id, submenu=new_sub, defaults=perms)

    # Delete old submenus — CASCADE removes their RolePermission rows.
    SubMenu.objects.filter(url_name__in=OLD_URLS).delete()


def undo(apps, schema_editor):
    """Best-effort reverse: drop the consolidated submenu. The 7 originals are
    not restored (re-run the menu_data fixture if you need them back)."""
    SubMenu = apps.get_model('accounts', 'SubMenu')
    SubMenu.objects.filter(url_name=NEW_URL).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_drop_government_institution_menu'),
    ]

    operations = [
        migrations.RunPython(consolidate, undo),
    ]
