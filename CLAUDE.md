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
| 16 | PRP API import + conflict-safe sync (see below) | ✅ |
| 17 | Observation fixes — prioritized task list (see below) | ✅ |

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
python manage.py loaddata fixtures/initial/sync_menu.json
python manage.py createsuperuser
python manage.py makemessages -l bn && python manage.py compilemessages
python manage.py test apps/

# PRP API import + sync (Phase 16)
export PRP_API_USER=... PRP_API_PASS=...
python manage.py import_mp_api --fetch --dry-run        # report unresolved dropdown values
python manage.py import_mp_api --fetch                  # initial create (skips existing)
python manage.py import_mp_api --fetch --sync           # conflict-safe re-sync → review in UI
```

### Phase 16 — PRP API import & sync (2026-07)
- **Command** `apps/mp/management/commands/import_mp_api.py` — pulls MP data from
  prp.parliament.gov.bd. Sources: `API_Data.txt` (default), `--url`, or live
  `--fetch` (two-step token auth: POST `…?action=token` → Bearer → GET
  `…?action=mpdata_list&parliamentNo=13`). Creds via `--username/--password` or
  env `PRP_API_USER`/`PRP_API_PASS`. Flags: `--dry-run --update --sync
  --no-images --limit N`.
- **Mapping**: API sends English-only labels → resolved to existing master FKs
  via `apps/mp/api_sync.py` (alias dicts shared with `import_mp_excel.py`;
  districts have 11 old-spelling aliases). Unresolved values are reported, never
  guessed. Occupation skipped (dirty free-text). Reserved seats (≥301) get a
  constituency FK by `ordering` (contradicts old rule #2 — code wins).
- **Sync policy — system is canonical, never blind-overwrite.** `--sync`:
  empty API → skip; system-empty + API value → auto-fill; both differ →
  `MPSyncConflict` (pending) for UI review. Collections (bank/spouse/child) are
  **add-only** (matched by acct-no/NID; system-only rows flagged, not deleted).
  **Photos**: `--sync` (and the UI Sync button) backfill a **missing** photo/
  signature from the API (`rec['image']`/`rec['signature']`, public URLs); an
  existing image is never overwritten. Use `--no-images` to skip, or
  `--images-only` to (re)download for all MPs.
- **Review UI**: `MP → Sync Conflicts` (`mp:sync_conflict_list`), grouped by MP,
  per-row + bulk [Use API]/[Keep system]. Resolution applies one field.
- **Schema added**: MP `signature`, Address `personal_email`, `MPSyncConflict`
  model (migrations 0003 + 0004). Contact lands on the MP's `present` Address row.

---

## PHASE 17 — Observation fixes (from `docs/observation.docx`, 2026-07-23) ✅
## All 12 observations addressed (P1 + P2 + P3/17.11). Pending: live verify + `migrate`.

Prioritized task list from user field observations. Priority = impact ÷ risk:
**P1** = quick, high-value, low-risk. **P2** = medium rework. **P3** = large /
structural. Some items reverse Phase 15 decisions — noted inline.

### P1 — quick wins (template / view tweaks)
- [x] **17.1 Print: hide search bar** — DONE. Added a global `@media print` block
      in `base.html` (hides `.mp-topbar`/`.mp-sidebar`/`.no-print`/`.d-print-none`,
      resets `.mp-main` margins). Marked each report's filter `<form>` `no-print`
      (party/cabinet/committee/contact/district/foreign_tours/institution/
      qualification/women/pa_ps + mp_committee_summary; all_mp/custom_report/
      family already were). Data tables sit outside the form, so nothing is lost.
- [x] **17.2 PDF downloads, not print** — DONE (with 17.6). New `?format=pdf`
      path serves a real PDF as `attachment` (downloads, no print dialog). See 17.6.
- [x] **17.3 Travel detail: show GO** — ALREADY IMPLEMENTED in current code
      (Phase 15 travel rework, which postdates observation.docx). `tour_detail.html`
      includes `partials/_go_file.html` (line ~64); form has `enctype` + `go_file`,
      view passes `request.FILES`, model field present. ⏳ needs live re-verify
      (no local DB) — if a real GO still doesn't show, check media serving.
- [x] **17.4 Family Report: add Constituency** — DONE. `family_report` view
      prefetches `election_infos→constituency`, derives per-MP constituency
      (reserved seats → "—"); added column to screen + print templates + Excel/CSV.
- [x] **17.5 Constituency list: keep pagination on edit** — DONE. Edit link carries
      `?next={{ request.GET.urlencode }}`; `constituency_update` reads `next`
      (POST/GET), renders it as a hidden field + Back/Cancel links, redirects back
      to the preserved page/filter on save.

### P2 — medium reworks
- [x] **17.2 + 17.6 PDF download + page-fit** — DONE. New reusable
      `render_report_pdf()` (`apps/reports/utils.py`): WeasyPrint → xhtml2pdf
      cascade, embeds SolaimanLipi by file URI, returns `attachment` (downloads).
      `base_print.html` now emits a conditional `@page` (A4 **landscape** for wide
      reports via `pdf_landscape`), `table-layout:fixed` + `overflow-wrap:anywhere`
      so columns never overflow (17.6), and skips the auto-`window.print()` in
      `pdf_mode`. All 13 report views gained a `fmt=='pdf'` branch; every PDF
      button repointed from `format=print`→`format=pdf` (family/custom got a new
      PDF button). Verified: falls back to xhtml2pdf here (no GTK) → valid 4.4 KB
      PDF; WeasyPrint renders on the Docker/Ubuntu server. ⏳ live-verify Bangla
      shaping + landscape fit on the server (WeasyPrint path not runnable in dev).
- [x] **17.7 Sidebar persistence** — DONE. `base.html` JS: persists expanded
      submenus + desktop collapsed state in `localStorage`, restores on load
      (pre-paint for collapse), auto-opens + highlights the group matching the
      current path (longest-prefix match). New `.mp-nav-sub.active` style in
      `theme.css`.
- [x] **17.8 Committee create: default role = member** — DONE. Step-2 pre-selects
      the "member" (সদস্য) position for every MP (`_default_member_position()`
      resolves it by name, falls back to first); blanks default to member (no more
      per-MP required validation). Info banner: "only change the Chairperson".
- [x] **17.9 Institution → free text** — DONE, **fully retired**. `institution` FK
      → `institution_bn`/`institution_en` text on `InstitutionAssignment`
      (migration `institution/0003` copies old FK labels first). Removed the
      `GovernmentInstitution` model (`master/0006` drops the table), its form, CRUD
      registry, menu fixture row + `accounts/0002` deletes the seeded menu row.
      Forms/views/list/report templates all use free text + `q`/text filters.
- [x] **17.10 Travel create rework** — DONE. ✅ Reordered create/edit form
      (**Tour Type → Purpose → GO info**). ✅ Officer designation → free-text field,
      **fully retired** `OfficerDesignation` master (travel `designation` FK →
      CharField, migration `travel/0003` copies labels; `master/0007` drops the
      table; menu row + `accounts/0002` cleanup). ✅ **Single-submit one page** —
      `tour_form.html` now saves tour header + countries + officers + participants
      in one POST via inline formsets (`CountryFormSet`/`OfficerFormSet` in
      `travel/forms.py`) + the mp_picker (participants reconciled add/drop). Shared
      `_tour_form()` handles both create & edit; JS adds/removes formset rows
      (delete = tick `-DELETE`, hidden). Old add/remove sub-endpoints remain but
      are unused. Verified: POST create persists tour+country+officer (302).

### P3 — structural (17.11 in progress: data layer done, UI pending)
**Design locked (2026-07-23):** REPLACE the generic add-one-record cascade form
with a **single page of fixed level-sections** (like the observation screenshot),
saved in one submit. Sections in order: **SSC · HSC · Diploma/Vocational ·
Graduation · Masters · PhD**, then a free-text **Self-educated** (bn+en) section.
Each academic section = one `Education` row bound to a fixed `EducationLevel`
(mapped by `level_type`: secondary/higher_sec/diploma/bachelor/masters/phd).

- [x] **17.11 MP Education redesign** — DONE.
  - [x] Nothing mandatory — every field `required=False`.
  - [x] Model fields — `Education.roll_no/reg_no/course_duration` (`mp/0005`),
        `MP.self_education_bn/en` (`mp/0006`).
  - [x] Seeded 6 canonical `EducationLevel` rows (`master/0008`, get_or_create by
        `level_type`). PhD included.
  - [x] **UI** — `EducationSectionForm` (`apps/mp/forms.py`): one per level, degree
        (Examination) list **level-scoped** → solves level-scoped exam types;
        `has_data()` decides save-vs-delete. `education_sections` view
        (`apps/mp/views.py`, `_EDU_SECTIONS`) loads/saves all 6 academic sections
        + MP self-education in ONE POST — filled sections upsert, cleared ones
        delete. Template `mp/education_sections.html`: fixed sections
        (SSC·HSC·Diploma·Graduation·Masters·PhD + free-text Self-educated),
        Institute on SSC/HSC, consistent two-column layout, per-section **result
        cascade** (JS map ResultType pk→`result_format` shows the matching input;
        `result_type`+`division_result` kept native to avoid Select2 issues).
        URL `mp:education_sections` replaces the old add/edit/delete;
        `_tab_education.html` now read-only summary + "Edit Education" button;
        old `education_form.html` deleted. Verified: GET renders all sections;
        POST creates SSC row with GPA result "5.00 / 5.00", saves self-education,
        and clearing a section deletes its row.

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
