# ref-reports.md — Report Engine & Audit Trail

---

## STANDARD REPORTS

Every report has: **[প্রিন্ট]  [PDF]  [Excel]  [CSV]**

| Report | Base Model | Key Filters |
|--------|-----------|-------------|
| সকল সংসদ সদস্য তালিকা | MP | Parliament, Party, District, Gender |
| মহিলা সদস্য তালিকা | MP | Parliament |
| দল ভিত্তিক তালিকা | MP | Parliament, Party |
| জেলা/বিভাগ ভিত্তিক | MP | District, Division |
| পেশাদার যোগ্যতা ভিত্তিক | MP | Qualification (Doctor/Engineer) |
| মন্ত্রিসভা তালিকা | MinistryAssignment | Parliament, MinisterType |
| কমিটি সদস্য তালিকা | CommitteeAssignment | Committee, Position |
| এমপি কমিটি সারসংক্ষেপ | CommitteeAssignment | MP |
| প্রতিষ্ঠান নিয়োগ তালিকা | InstitutionAssignment | Institution |
| বিদেশ সফর তালিকা | ForeignTour | Type, Country, Year |
| এমপি বায়োডাটা (একক) | MP + all related | MP ID |
| যোগাযোগ তালিকা | MP + Office | District, Party |

---

## AUDIT TRAIL

All models include these fields:
```python
created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
created_by = FK(CustomUser, null=True, related_name='+')
updated_by = FK(CustomUser, null=True, related_name='+')
```

Audit log model:
```python
class AuditLog(Model):
    user       = FK(CustomUser)
    model_name = CharField()
    object_id  = IntegerField()
    action     = CharField()    # CREATE / UPDATE / DELETE
    changes    = JSONField()    # {'field': ['old', 'new']}
    timestamp  = DateTimeField(auto_now_add=True)
    ip_address = GenericIPAddressField()
```

---

## PHASE 1 KICKOFF PROMPT

Use this to start a fresh Phase 1 implementation session:

```
Read CLAUDE.md and docs/ reference files. Then start Phase 1:

1. Create Django project structure with config/ and apps/ layout
2. Create requirements.txt with all dependencies
3. Create config/settings/base.py with:
   - PostgreSQL config
   - All installed apps listed
   - HTMX + Select2 static config
   - Static/media file config
   - i18n settings for bn + en (LANGUAGE_CODE = 'bn')
   - Custom AUTH_USER_MODEL = 'accounts.CustomUser'
4. Create all 10 app skeletons
   (accounts, master, parliament, mp, ministry,
    committee, institution, travel, office, reports)
5. Create templates/base.html with:
   - Bootstrap 5
   - HTMX script
   - Language toggle button (bn/en)
   - Sidebar nav (reads Menu/SubMenu from DB)
   - Bilingual header
6. Create templates/base_print.html (no nav, print-optimized)

Do NOT write any models yet — skeleton only.
```
