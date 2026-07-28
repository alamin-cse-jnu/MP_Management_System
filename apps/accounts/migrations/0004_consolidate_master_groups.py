from django.db import migrations

# Each group replaces several per-table master submenus with ONE consolidated
# submenu pointing at the new grouped single-page manager. Same pattern as
# 0003_consolidate_education_menu, generalized for the 5 new groups.
GROUPS = [
    {'new_url': 'master:geography_master', 'name_bn': 'ভূগোল (বিভাগ/জেলা/উপজেলা)',
     'name_en': 'Geography', 'ordering': 20,
     'old': ['master:division_list', 'master:district_list', 'master:upazila_list']},
    {'new_url': 'master:personal_master', 'name_bn': 'ব্যক্তিগত তথ্য (ধর্ম/রক্ত/বৈবাহিক/লিঙ্গ)',
     'name_en': 'Personal Info', 'ordering': 30,
     'old': ['master:religion_list', 'master:blood_group_list',
             'master:marital_status_list', 'master:gender_list']},
    {'new_url': 'master:professional_master', 'name_bn': 'পেশাগত তথ্য (পেশা/যোগ্যতা)',
     'name_en': 'Professional Info', 'ordering': 40,
     'old': ['master:profession_list', 'master:professional_qualification_list']},
    {'new_url': 'master:travel_master', 'name_bn': 'ভ্রমণ (দেশ/ধরন/উদ্দেশ্য)',
     'name_en': 'Travel', 'ordering': 100,
     'old': ['master:country_list', 'master:travel_type_list', 'master:travel_purpose_list']},
    {'new_url': 'master:language_master', 'name_bn': 'ভাষা (বিদেশি ভাষা/দক্ষতা)',
     'name_en': 'Language', 'ordering': 110,
     'old': ['master:foreign_language_list', 'master:proficiency_level_list']},
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

        # Carry over permissions: union of each role's perms across the old subs.
        agg = {}
        for rp in RolePermission.objects.filter(submenu__in=old_subs):
            cur = agg.setdefault(rp.role_id, {f: False for f in PERM_FIELDS})
            for f in PERM_FIELDS:
                cur[f] = cur[f] or getattr(rp, f, False)
        for role_id, perms in agg.items():
            RolePermission.objects.update_or_create(
                role_id=role_id, submenu=new_sub, defaults=perms)

        # Delete old submenus — CASCADE removes their RolePermission rows.
        SubMenu.objects.filter(url_name__in=g['old']).delete()


def undo(apps, schema_editor):
    """Best-effort reverse: drop the consolidated submenus. The originals are
    not restored (re-run the menu_data fixture if you need them back)."""
    SubMenu = apps.get_model('accounts', 'SubMenu')
    SubMenu.objects.filter(url_name__in=[g['new_url'] for g in GROUPS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_consolidate_education_menu'),
    ]

    operations = [
        migrations.RunPython(consolidate, undo),
    ]
