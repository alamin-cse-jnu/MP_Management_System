from django.db import migrations

# Fold the Ministry and Committee per-table master submenus into ONE grouped
# single-page manager each. Same pattern as 0004_consolidate_master_groups.
GROUPS = [
    {'new_url': 'master:ministry_master', 'name_bn': 'মন্ত্রণালয় (মন্ত্রণালয়/মন্ত্রীর ধরন)',
     'name_en': 'Ministry', 'ordering': 70,
     'old': ['master:ministry_list', 'master:minister_type_list']},
    {'new_url': 'master:committee_master', 'name_bn': 'কমিটি (স্থায়ী কমিটি/পদ)',
     'name_en': 'Committee', 'ordering': 80,
     'old': ['master:standing_committee_list', 'master:committee_position_list']},
]
PERM_FIELDS = ['can_view', 'can_add', 'can_edit', 'can_delete', 'can_export']


def consolidate(apps, schema_editor):
    Menu = apps.get_model('accounts', 'Menu')
    SubMenu = apps.get_model('accounts', 'SubMenu')
    RolePermission = apps.get_model('accounts', 'RolePermission')

    master_menu = Menu.objects.filter(name_en='Master Data').first()

    for g in GROUPS:
        old_subs = list(SubMenu.objects.filter(url_name__in=g['old']))
        menu = old_subs[0].menu if old_subs else master_menu
        if menu is None:
            continue

        new_sub, _ = SubMenu.objects.get_or_create(
            url_name=g['new_url'],
            defaults={'menu': menu, 'name_bn': g['name_bn'],
                      'name_en': g['name_en'], 'ordering': g['ordering'],
                      'is_active': True},
        )

        agg = {}
        for rp in RolePermission.objects.filter(submenu__in=old_subs):
            cur = agg.setdefault(rp.role_id, {f: False for f in PERM_FIELDS})
            for f in PERM_FIELDS:
                cur[f] = cur[f] or getattr(rp, f, False)
        for role_id, perms in agg.items():
            RolePermission.objects.update_or_create(
                role_id=role_id, submenu=new_sub, defaults=perms)

        SubMenu.objects.filter(url_name__in=g['old']).delete()


def undo(apps, schema_editor):
    SubMenu = apps.get_model('accounts', 'SubMenu')
    SubMenu.objects.filter(url_name__in=[g['new_url'] for g in GROUPS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_consolidate_master_groups'),
    ]

    operations = [
        migrations.RunPython(consolidate, undo),
    ]
