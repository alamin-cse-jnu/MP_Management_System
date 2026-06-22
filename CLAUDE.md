# CLAUDE.md — MP Information Management System
# Bangladesh Parliament Secretariat
# Read this file at the start of EVERY session and update after every session .

---

## PROJECT OVERVIEW

A bilingual (Bangla + English) Django-based web application for managing
Members of Parliament (MP) information for Bangladesh Parliament.

- **350 MPs** per parliament tenure
  - Seats 1–300 : Directly elected
  - Seats 301–350 : Women reserved (সংরক্ষিত মহিলা আসন)
- **Currently active :** 13th Parliament (ত্রয়োদশ জাতীয় সংসদ)
- **Bilingual :** Every screen and report supports Bangla and English
- **NO Django Admin Panel** — ALL operations through the custom-built system only

---

## TECH STACK

```
Backend       : Django 5.2 LTS
Database      : PostgreSQL
Frontend      : Django Templates + HTMX + Bootstrap 5
Dropdowns     : Select2 (searchable, multi-select where needed)
Dynamic Forms : HTMX (cascading dropdowns, inline formsets)
PDF Export    : WeasyPrint
Excel Export  : openpyxl
Bangla Fonts  : SolaimanLipi (for print templates)
Auth          : Django built-in + custom role middleware
```

---

## DEPLOYMENT (production)

```
Server   : 172.16.220.158 (Ubuntu, internal IP, no domain/TLS yet)
Path     : /opt/mp_management  (plain files, NOT a git checkout)
Stack    : docker compose → db (postgres16) + web (gunicorn) + nginx
Serving  : nginx :80  →  proxy →  gunicorn web:8000 (config.settings.production, DEBUG=False)
           nginx serves /static/ + /media/ from named volumes; web is internal-only.
Settings : entrypoint.sh exports DJANGO_SETTINGS_MODULE=config.settings.production,
           runs migrate + collectstatic, then execs gunicorn (3 workers, 120s timeout).
TLS      : OFF. production.py secure-cookie/HSTS/SSL-redirect are env-driven via
           USE_TLS (default False) so HTTP login works. Set USE_TLS=True + add a
           cert/443 server block when a domain/cert exists.
Deploy   : no CI. Sync changed files over SFTP to /opt/mp_management, then
           `docker compose up -d` (add --build only when requirements.txt changes).
           No migration unless models changed. Rollback files: *.prebak on server.
```

---

## CRITICAL RULES

```
1. NEVER use or reference Django's built-in /admin/ panel.
   ALL CRUD — including Master Data — is done through the custom UI.

2. Every model storing user-visible data has BOTH _bn and _en fields.
   Dropdowns always show:  বাংলা নাম (English Name)

3. Language toggle stored in session:
   request.session['LANGUAGE'] = 'bn' | 'en'

4. Soft delete on master data (is_active=False) — never hard delete
   when FK references exist.

5. Superadmin bypasses all role permission checks.
```

---

## PROJECT STRUCTURE

```
mp_management/
├── CLAUDE.md
├── docs/                      ← Detailed reference docs
│   ├── ref-conventions.md     ← Bilingual, MP ID, address, HTMX patterns
│   ├── ref-models.md          ← MP model + operational module models
│   ├── ref-master-data.md     ← Master data menu + accounts/roles
│   ├── ref-education.md       ← Education sub-system (complex)
│   └── ref-reports.md         ← Reports table + audit trail
├── requirements.txt
├── manage.py
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/          ← Users, Roles, Permissions, Menus
│   ├── master/            ← ALL reference/dropdown CRUD (Master Data)
│   ├── parliament/        ← Parliament tenure, Constituency
│   ├── mp/                ← MP master profile + all sub-models
│   ├── ministry/          ← Ministry assignment module
│   ├── committee/         ← Standing committee module
│   ├── institution/       ← Institution assignment module
│   ├── travel/            ← Foreign travel module
│   ├── office/            ← Parliament office address
│   └── reports/           ← Report engine
├── templates/
│   ├── base.html
│   ├── base_print.html    ← Print-optimized (no nav/sidebar)
│   ├── partials/          ← HTMX partial templates
│   └── {app}/             ← Per-app templates
├── static/
│   ├── css/ js/ img/
│   └── fonts/             ← SolaimanLipi.ttf
├── locale/
│   ├── bn/LC_MESSAGES/
│   └── en/LC_MESSAGES/
└── fixtures/
    └── initial/           ← divisions.json, districts.json, upazilas.json
```

---

## KEY BUSINESS RULES

1. Seats 1–300 = Direct elected. Must have constituency FK.
2. Seats 301–350 = Women reserved. No constituency. Party assigned.
3. Only ONE parliament `is_active=True` at a time (mutex on save).
4. Constituency = admin-entered text (display_bn + display_en). No auto-generation.
5. MP ID = entered manually (e.g. 013000101). System validates uniqueness only.
6. Address = Division dropdown + District dropdown + Upazila dropdown + ONE free text field.
7. Education result field is dynamic — shown based on ResultType selection (HTMX).
8. ProfessionalQualification ≠ Profession. Both are M2M multi-select on MP model.
9. Previous Parliamentary History = free text only. No FK to Constituency.
10. Ministry/Committee entry works from BOTH the module AND the MP profile.
11. ALL master data models have full CRUD in the custom system. No Django admin.
12. Soft delete on master data (is_active=False) to preserve FK integrity.
13. Foreign tour GO can cover multiple MPs (ForeignTourParticipant).
14. Office address = সংসদ অফিস ONLY. OneToOne with MP.
15. Superadmin bypasses all role permission checks.
16. Report export requires can_export=True in RolePermission.

---

## DEVELOPMENT PHASES

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Project setup, settings, app skeletons, base templates | ✅ |
| 2 | master/ — all reference models + CRUD UI | ✅ |
| 3 | accounts/ — Role + Permission + Middleware | ✅ |
| 4 | parliament/ — Parliament + Constituency CRUD | ✅ |
| 5 | mp/ — MP entry form sections 1–6 with HTMX | ✅ |
| 6 | mp/ — Education sub-form (dynamic result fields) | ✅ |
| 7 | mp/ — Sections 7–19 remaining sub-models | ✅ |
| 8 | ministry/ + committee/ modules | ✅ |
| 9 | institution/ + travel/ + office/ modules | ✅ |
| 10 | reports/ — all standard reports | ✅ |
| 11 | PDF biodata Bangla + English (WeasyPrint) | ✅ | 
| 12 | Excel/CSV exports + Dashboard KPIs | ✅ |
| 13 | Audit log + activity monitoring | ✅ |
| 14 | Custom Report Builder (12 filters, column selector, Excel/CSV/Print) | ✅ |
| 15 | UX improvements round (see below) | ✅ |

⬜ Not started | 🔄 In progress | ✅ Done

### Phase 15 — improvements (2026-06)
- **All dropdowns searchable**: Select2 forced on every `.form-select` system-wide
  (`minimumResultsForSearch:0`); opt out with `data-no-select2`. Custom-report
  multi-selects (`.filter-select2`) keep their own init.
- **MP dropdown** (`apps/mp/form_fields.py`): serial order — direct-elected by
  `constituency.ordering` (1→300) then reserved (301→350) by `mp_id`; label is
  `Name — Constituency — MP-ID`. New `MPMultipleChoiceField` for multi-select.
- **GO uploads**: shared `utils/go_files.py` validator (pdf/jpg/jpeg/png, ≤10 MB).
  `go_file` FileField on Ministry / Committee / Institution assignments + ForeignTour;
  shown via `partials/_go_file.html` in list/detail.
- **Ministry**: GO upload; status-toggle removed; edit loads MP (editable).
- **Institution**: removed `nomination_date`; added `nominated_by` (pm/speaker);
  multi-MP create → one row per MP; MP filter on list.
- **Committee**: two-step create — step1 (committee + guide-only total + multi-MP),
  step2 (position per MP). Single-MP create still works from MP profile.
- **Constituency**: new `district` FK (→division) for constituency-based reports.
  District/Division report has a `basis` toggle: home district vs constituency (1–300).
- **Foreign Travel**: per-country `from_date`/`to_date` (participant dates removed;
  tour range derived via `ForeignTour.overall_from_date/overall_to_date`);
  bulk multi-MP add; new `ForeignTourOfficer` (free-text id/name + `OfficerDesignation`
  master FK, searchable in tour list); GO upload; reorganized detail page.
- **Multi-MP picker**: the Select2 multi-select for choosing many MPs
  (committee step1, institution bulk, travel participant-add) is replaced by a
  **filterable checkbox panel** — search (name/MP-ID/constituency), party +
  seat-type quick-filter chips, "select all shown", clear, live count, and
  chosen-chips strip. Rendered via `{% mp_picker form.mps %}`
  (`apps/mp/templatetags/mp_picker_tags.py` → `partials/_mp_picker.html`);
  `MPMultipleChoiceField` unchanged (validation identical). Party chips come
  from new `_party_bn/_party_en` annotations on `MPChoiceField.annotated_queryset`.
  Assets: `static/css/mp_picker.css`, `static/js/mp_picker.js` (HTMX-swap safe).

---

## COMMANDS

```bash
python manage.py runserver
python manage.py makemigrations && python manage.py migrate
python manage.py loaddata fixtures/initial/divisions.json
python manage.py loaddata fixtures/initial/districts.json
python manage.py loaddata fixtures/initial/upazilas.json
python manage.py loaddata fixtures/initial/menu_data.json
python manage.py loaddata fixtures/initial/parliament_menu.json
python manage.py loaddata fixtures/initial/parliament_data.json
python manage.py loaddata fixtures/initial/mp_menu.json
python manage.py loaddata fixtures/initial/ministry_menu.json
python manage.py loaddata fixtures/initial/committee_menu.json
python manage.py loaddata fixtures/initial/institution_menu.json
python manage.py loaddata fixtures/initial/travel_menu.json
python manage.py loaddata fixtures/initial/reports_menu.json
python manage.py loaddata fixtures/initial/audit_menu.json
python manage.py createsuperuser
python manage.py makemessages -l bn && python manage.py compilemessages
python manage.py test apps/
```

---

## REFERENCE DOCS

Read these when working on the relevant area:

| File | When to read |
|------|-------------|
| `docs/ref-conventions.md` | Bilingual fields, template tag, Bengali numerals, MP ID format, address design, HTMX cascade patterns |
| `docs/ref-models.md` | MP model (all 17 sections), Ministry/Committee/Institution/Travel/Office models |
| `docs/ref-master-data.md` | Master data menu structure, generic CRUD views, Accounts/Role/Permission models |
| `docs/ref-education.md` | Education sub-system — master models, MP education record, dynamic form, report queries |
| `docs/ref-reports.md` | Standard reports table, audit trail model |
| `docs/ref-design.md` | Color palette, login layout, sidebar/topbar, cards, tables, forms, buttons, print styles |
| `docs/ref-form-mapping.md` | PDF form → system field mapping; exact field order per section; 3 model fixes from PDF audit |
