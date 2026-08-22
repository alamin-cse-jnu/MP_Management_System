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
17. Technocrat ministers = cabinet members with NO seat. Stored as MP rows with
    member_type='technocrat' and NO ElectionInfo (no constituency/party/election).
    They NEVER count towards the 350 — every MP count/report goes through
    MP.objects.parliament_members(). Included in ministry/travel/institution
    pickers, excluded from committee. PRP sync never touches them.

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
| 18 | Education master-data pools (school/university groups) + self-educated tick | ✅ |
| 19 | Education master data → single-page manager (tab-rail + inline HTMX CRUD) | ✅ |
| 20 | MP detail edit tabs → two-column grouped composition (General, Election, Address) + dashboard tiny-bar click fix | ✅ |
| 21 | Master data → grouped single-page managers (Geography, Personal, Professional, Travel, Language, Ministry, Committee) mirroring Education | ✅ |
| 22 | Technocrat ministers — cabinet members with no seat (see below) | ✅ |
| 23 | Accompanying Officers → PRP employee sync (roster + picker, see below) | ✅ |

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

# PRP officer roster sync (Phase 23) — same PRP_API_USER / PRP_API_PASS
python manage.py sync_officers --dry-run                # report keep-set + skips, save nothing
python manage.py sync_officers                          # upsert + retire (never deletes)
python manage.py sync_officers --file employees.json    # offline payload (testing)
python manage.py loaddata fixtures/initial/officer_menu.json
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

## PHASE 18 — Education master-data pools + self-educated tick (2026-07-24) ✅
Field-feedback refinement of the Phase 17.11 education page (`/mp/<id>/education/`).

- **Roll No / Reg No removed** — dropped from the SSC/HSC UI *and* the DB
  (`Education.roll_no`/`reg_no` deleted, migration `mp/0007`). Dead
  `EducationForm` class (old cascade form, unused since 17.11) removed from
  `apps/mp/forms.py` + its import.
- **Two shared master-data pools for groups.** `EducationGroup.applicable_to`
  choices restructured `secondary/higher_sec/university/all` →
  **`school` / `university` / `all`** (`master/0009`, with a RunPython that
  collapses old `secondary`+`higher_sec` rows into `school`). `_LEVEL_GROUP_MAP`
  (in both `apps/mp/forms.py` and `apps/master/views.py`) now maps
  SSC/HSC/Diploma → `['school','all']` and Grad/Masters/PhD → `['university','all']`.
  Effect: the **Board, Group, Result Type** dropdowns show ONE shared list across
  SSC/HSC/Diploma (each section still stores its own value); **University +
  Subject** already shared across Grad/Masters/PhD. Examination (DegreeName) stays
  per-level-scoped. Admin tags each group `school`/`university`/`all` in Master Data.
- **Self-educated = tick + optional note.** New `MP.is_self_educated` boolean
  (`mp/0007`); the two `self_education_bn/en` textareas are kept as an OPTIONAL
  note. Template shows a checkbox first, notes labelled optional; read-only
  `_tab_education.html` shows a "Self-educated" badge.
- Verified in the running Docker stack: `migrate` OK, `check` clean, education
  page GET 200 / POST 302 (tick + note persist), school-level group pools identical.

---

## PHASE 19 — Education master data: single-page manager (2026-07-24) ✅
The 7 separate education master menus/pages (Levels, Groups, Subjects, Degree
Names, Institutions, Result Types, Division Results) are consolidated into ONE
page at **`/master/education/`** — left **tab-rail** + inline **HTMX** add/edit/
toggle. Reuses the existing master ModelForms (no new forms/models).

- **Config-driven** — `EDU_ENTITIES` (in `apps/master/views.py`) lists the 7
  tables (model, form, icon, bilingual hint, extra `cols`). Order: Examinations
  (Degree Names) · Groups · Subjects · Institutions · Result Types · Division
  Results · Levels (marked `advanced`). `EDU_MAP` = key→spec.
- **Views** — `education_master` (shell, tab-rail with live counts),
  `education_panel` (table partial), `education_form` (GET opens inline add/edit
  form, POST validates+saves), `education_toggle`. All swap a single
  `#edu-panel` (`hx-swap=outerHTML`); one helper `_render_edu_panel`. Invalid
  POST re-renders the panel with the form open + errors; success shows an inline
  "saved" banner + highlights the row. Filter (search + active/inactive/all)
  posts via `#edu-filter`, carried on every action via `hx-include`.
- **Templates** — `master/education_master.html` (tab-rail + CSS + client-side
  active-tab highlight) and `master/partials/edu_panel.html` (filter + inline
  form + table). Select2 re-inits automatically via the existing
  `htmx:afterSwap` hook.
- **Global HTMX CSRF** — added a `htmx:configRequest` handler in `base.html` that
  attaches `X-CSRFToken` to every HTMX request (needed for POST swaps; benefits
  all future HTMX POSTs).
- **Old pages removed entirely** — the 7 education dicts dropped from
  `MASTER_SPECS` (their `/master/<entity>/` list/add/edit/toggle routes no longer
  exist → 404). `master_home` Education section is now ONE card. Menu: `menu_data.
  json` submenu row (pk 40) repointed to `master:education_master`; migration
  `accounts/0003` deletes the 7 old submenus on existing DBs (CASCADE clears their
  RolePermissions) after **carrying each role's combined education permissions**
  onto the new consolidated submenu. Superadmin bypasses permissions.
- **URLs** — `master:education_master` + `education_panel` / `education_form_add`
  / `education_form_edit` / `education_toggle` (all `/master/education/<key>/…`).
- Verified in the running Docker stack: `migrate`+`check` clean; page/panel/
  add-form GET 200; inline create + toggle 200 (persist); old list URL 404;
  new submenu present, 7 old submenus gone.

---

## PHASE 20 — MP General Info edit form redesign (2026-07-24) ✅
The **edit** panel of the MP detail "General Information" tab
(`templates/mp/_tab_general.html`, `#general-edit`) was a flat, ungrouped form —
the six name fields (self/father/mother × bn/en) were each full-width and
stacked, causing heavy vertical scroll. Rebuilt as a **two-column grouped**
composition (user-chosen).

- **Left column** cards: **Identity** (Name/Father/Mother, bn|en paired) ·
  **Personal Details** (DOB, NID, Gender, Birthplace, Home District, Marital,
  Nationality, Religion, Blood, TIN — all 2-up) · **Profession & Qualification**
  (current/previous multi + professional qualifications).
- **Right column** cards: **Photo** (thumb + upload) · **Passport** (no,
  issue/expiry, place) · **Freedom Fighter** (3 checkboxes inline) ·
  **Additional Info** (Hobbies + Other Info, bn|en paired).
- **Election tab** (`_tab_election.html`, `#election-edit`) redone the same way:
  left = **Constituency & Parliament** (+ times elected) · **Party & Membership**
  (party + read-only member type); right = **Key Dates** (election/oath/gazette) ·
  **Nomination & GO (System)** (nomination date, GO no/date).
- **Shared styling** — `.gi-card` / `.gi-card-title` / `.gi-col` live in
  `static/css/theme.css` (generic, reusable across all edit tabs), not scoped per
  tab. Columns get `.gi-col` for last-child margin handling. Reapply to any other
  edit tab by wrapping fields in `.gi-card` + a `.gi-card-title`.
- **Template/CSS only** — forms, views, URLs, read-only view panels, and the
  show/cancel-edit JS all unchanged; same field names + error handling
  (`|striptags` on errors). `collectstatic` runs on container start (entrypoint),
  so the theme.css change is served by nginx after a restart.
- **Address tab** (`_tab_address.html` → shared `_address_fields.html`) redone the
  same way — one partial edit covers all 3 sub-tabs (Present/Permanent/Dhaka):
  **left column** = **Location** (division/district/upazila cascade + pouroshova
  bn/en + postal) **+ Address Details** (bn/en); **right column** = **Contact**
  (present only, via `show_contact`) with **two emails** — Personal
  (`personal_email`) + Official (`email`). `personal_email` added to
  `AddressForm.Meta.fields` (model field already existed from Phase 16). No-contact
  sub-tabs render the left column full-width (`col-12`). Cascade `onchange`
  handlers are on the widgets (keyed by prefix), so reordering fields is safe.
- Verified: detail page GET 200 with `.gi-card` markup on all three tabs; invalid
  POST (blank required name / bad parliament) re-renders 200 with the right edit
  panel shown so errors are visible; cascade handlers intact; nginx serves updated
  theme.css.

### Dashboard — tiny-bar click fix (2026-07-24)
`templates/accounts/dashboard.html` (ApexCharts): a bar with a very low value
(e.g. Times-Elected "1st Time") renders almost no height, so its bar is nearly
unclickable (ApexCharts has no `minBarLength`). Fix: `makeColumnsClickable(elId,
count, onPick)` helper makes the **entire column area clickable** — a single click
listener on the chart div maps the click's x-position (within the
`.apexcharts-grid` rect, over full plot height + the label band) to a category
index, so even a 1px bar is selectable. Wired to the Times-Elected chart's
`mounted`/`updated` events (bound once, grid re-queried per click so it survives
resize); still navigates to `all_mp?times_elected=<id>`, and the bar's own
`dataPointSelection` is kept as a fallback. Reusable for other column charts;
division bar (horizontal) would need a y-axis variant. NOTE: JS interaction not
auto-verifiable here (no browser tool) — needs a manual click test in the app.

---

## PHASE 21 — Master data grouped single-page managers (2026-07-28) ✅
Extends the Phase 19 Education pattern to **7 more clusters** so related master
tables are managed together on ONE page each (left tab-rail + inline HTMX add/
edit/toggle). Groups: **Geography** (Divisions·Districts·Upazilas) · **Personal
Info** (Religions·Blood Groups·Marital·Genders) · **Professional Info**
(Professions·Professional Qualifications) · **Travel** (Countries·Travel Types·
Purposes) · **Language** (Foreign Languages·Proficiency Levels) · **Ministry**
(Ministries·Minister Types) · **Committee** (Standing Committees·Committee
Positions). Reaches at `/master/<group>/`. (Ministry + Committee consolidated by
migration `accounts/0005_consolidate_ministry_committee`; the other 5 by `0004`.)

- **Config-driven, generic** — `MASTER_GROUPS` (in `apps/master/views.py`) lists
  each group (key, title/icon/subtitle bn+en) + its entity specs (key, model,
  form, title, icon, hint, `cols`). One generic view set (`_build_group_views`
  → master/panel/form/toggle) is **bound per-group** and registered with its own
  named URLs (`master:<group>_master` / `_panel` / `_form_add` / `_form_edit` /
  `_toggle`), so menu links + `@perm_required` resolve exactly like Education
  (permission gate is at the `_master` submenu; inline actions pass through).
  Reuses the existing master ModelForms + the edu queryset/param helpers.
- **Templates** — `master/group_master.html` (tab-rail shell, `.grp-*` CSS) +
  `master/partials/group_panel.html` (filter + inline form + table). Both reverse
  the group's dynamically-named URLs via **`{% url group.panel_url e.key %}`**
  (precomputed name-strings `master_url/panel_url/form_add_url/form_edit_url/
  toggle_url` set on each group dict at module load). Select2 re-inits via the
  existing `htmx:afterSwap` hook; global HTMX CSRF header already in `base.html`.
- **Consolidation (mirrors Phase 19)** — the 14 per-table entries were **removed
  from `MASTER_SPECS`** (their `/master/<entity>/` list/add/edit/toggle routes now
  404). `master_home` shows each cluster as ONE "all-in-one" card; standalone
  tables (Political, Ministry, Minister Types, Committees, Institution Roles,
  Special Roles, PA/PS, Vaccines) keep their individual CRUD pages. Menu:
  `menu_data.json` replaces the 14 submenus (pk 10-12,20-23,30-31,90-92,100-101)
  with 5 group submenus (pk 10/20/30/90/100 → `master:<group>_master`); migration
  `accounts/0004_consolidate_master_groups` deletes the old submenus on existing
  DBs **after carrying each role's unioned permissions** onto the new group
  submenu (same helper shape as `0003`). Superadmin bypasses permissions.
- **Not touched** — Education manager, the district/upazila HTMX cascade endpoints
  (used by the MP address form), and all standalone master models.
- Verified locally on an isolated SQLite build (Django test client): all 5 group
  pages + master home render 200; panel/add-form/edit-form (prefilled) render;
  POST create (incl. FK district form) + toggle persist; invalid POST re-renders
  the inline form with errors; bad entity key → 404; old per-table URLs removed;
  migration 0004 creates the 5 submenus, deletes the old ones, and carries unioned
  role permissions. ⏳ not yet deployed to the live server.

---

## PHASE 22 — Technocrat ministers (2026-08-20) ✅
Cabinet members appointed **without a parliamentary seat** (no constituency, no
party, no election) were absent from the system, leaving the cabinet report
incomplete. Source: `docs/technocrat.md`; full design in `docs/technocrat-plan.md`.

- **Third `member_type`** — `MP.MEMBER_TYPE_CHOICES` gains `'technocrat'`
  (`টেকনোক্র্যাট মন্ত্রী`), migration `mp/0008` (choices-only, no column change).
  A technocrat = an `MP` row with **no `ElectionInfo` at all** + one
  `MinistryAssignment` per ministry. `ElectionInfo.constituency` was already
  nullable and `MinistryAssignment` already allowed several rows per person, so
  **no other schema change** was needed. Rejected alternatives: a separate
  `Technocrat` model (would duplicate the whole ministry/biodata stack) and a
  nullable `MinistryAssignment.mp` (nullable-FK churn across every template).
- **"350 means 350"** — `MP.objects.parliament_members()` (a `MPQuerySet` on
  `apps/mp/models.py`) is the ONE definition of "actual member" =
  `.exclude(member_type='technocrat')`. Applied at: dashboard `mp_qs`
  (`accounts/views.py`), `_mp_qs_base()` + report-index stats + contact/custom/
  family report querysets (`reports/views.py`), `mp_list` default and the PRP
  "missing photo" count (`mp/views.py`). Ministry/cabinet surfaces deliberately
  do NOT exclude them. `MP.is_technocrat` property + `MP.objects.technocrats()`.
- **Three-way labels** — three places assumed "not direct ⇒ reserved" and would
  mislabel a technocrat as সংরক্ষিত (মহিলা): `reports/templatetags/report_tags.py`,
  the custom-report formatter (`reports/views.py`, now via new `MEMBER_TYPE_EN`
  map for English), and the `mp_list.html` badge. All use
  `get_member_type_display()`. New `.badge-warning` in `theme.css` (amber) marks
  technocrats.
- **Pickers** — `MPChoiceField` / `MPMultipleChoiceField` / `annotated_queryset()`
  gain `include_technocrats` (**default `True`**). Ministry, foreign-travel and
  institution keep them (a technocrat can travel on a GO / be nominated);
  **committee passes `False`** (membership requires a seat) — `committee/forms.py`
  ×2 + `committee/views.py` step-2. Technocrats sort last (`'direct'` <
  `'reserved'` < `'technocrat'`) and are labelled `Name — টেকনোক্র্যাট — MP-ID`.
- **MP detail** — `_tabs_for(mp)` hides tab ২ (নির্বাচন) and tab ১১ (কমিটি) for
  technocrats; `mp_detail` clamps a stale `?active=` to a tab that exists.
  `mp_create` redirects a new technocrat to `tab-ministry`, not `tab-election`.
  Create form (`mp_create.html`) gains the third option.
- **Cabinet report + ministry list** — new **সদস্যের ধরন** column (screen, print,
  Excel/CSV) and an MP/Technocrat filter carried through export + pagination links.
  Dashboard Ministers tile shows "এর মধ্যে N টেকনোক্র্যাট".
- **Ministry list grouped by minister (2026-08-20 follow-up)** — field report: "a
  minister with multiple ministries only shows one". Nothing was missing; the page
  paginated **assignments** while `MinistryAssignment.Meta.ordering` sorts by
  minister-type then ministry *name*, scattering one person's rows across pages
  (শেখ রবিউল আলম's 3 ministries sat on pages 1, 2 AND 3). **13 ministers hold
  several ministries** (3 hold three). `assignment_list` now groups by MP —
  `qs.order_by().values('mp').annotate(rank=Min('minister_type__ordering'),
  sort_name=Min('mp__name_bn')).order_by('rank','sort_name')` (the bare
  `order_by()` is required or Meta.ordering folds into the GROUP BY) — paginates
  the **groups** (25 ministers/page), then fetches that page's assignments in one
  query into `rows=[{'mp','assignments'}]`. Template renders **one `<tbody>` per
  minister** with `rowspan` on the serial + name cells, a "⧉ Nটি মন্ত্রণালয়" badge
  when >1, and per-ministry dates/GO/edit/delete unchanged. Footer reports BOTH
  counts (ministers · assignments). Order = cabinet rank, then name.
  Verified on prod: 48 ministers / 64 assignments over 2 pages, each minister once,
  all 64 assignments rendered, all 13 multi-ministry groups on a single page each.
- **Cabinet report grouped too (2026-08-20)** — the grouping was extracted to
  **`apps/ministry/grouping.py`** (`minister_group_order` / `build_minister_groups`
  / `all_minister_groups`) and both pages now share it. `/reports/cabinet/`:
  screen + print + PDF render one `<tbody>` per minister with `rowspan` on the
  serial/MP-ID/name/member-type cells; screen paginates ministers. **Excel/CSV stay
  one row per assignment** (a cell cannot span rows in CSV) but are ordered by
  minister, the serial column counts MINISTERS (repeating down that minister's
  ministries, matching the screen), and the name repeats on every row so the sheet
  stays filterable. Counts shown as "N জন মন্ত্রী · M টি নিয়োগ".
- **MP profile Ministry + Committee tabs grouped by PARLIAMENT (2026-08-20)** —
  these tabs show ONE person, so the repeating column is Parliament, not the MP.
  Generic **`utils/assignment_grouping.py` → `group_by_parliament(qs, *order_within)`**
  (in `utils/` beside `go_files.py` because it is now shared by two modules; the
  minister-specific helpers stay in `apps/ministry/grouping.py`). `_detail_ctx`
  adds `ministry_groups` + `committee_groups`; the flat `*_assignments` lists are
  KEPT because the 4 biodata templates read the plain related manager.
  Real bug fixed: **neither** `MinistryAssignment.Meta.ordering`
  (`minister_type__ordering, ministry__name_bn`) **nor** `CommitteeAssignment.Meta.
  ordering` (`committee__name_bn`) mentions parliament, so an MP who served in two
  parliaments got INTERLEAVED tenures. Now `-parliament__ordinal` first, then
  `minister_type__ordering/ministry__name_bn` or `position__ordering/committee__name_bn`.
  Templates `_tab_ministry.html` / `_tab_committee.html` = one `<tbody>` per
  parliament, `rowspan` on the Parliament cell + "⧉ Nটি মন্ত্রণালয়/কমিটি" badge.
  Verified on prod: all 13 multi-ministry MPs and 30 multi-committee MPs, plus
  single/none/empty-state, and every regression surface (both module lists, cabinet
  + committee reports, biodata).
- **Institution grouped everywhere + NEW MP profile tab 19 (2026-08-20)** — there
  was **no institution tab** on the MP profile (institution existed only as a module
  + report), and prod has **0 institution rows** (module never used), so this is
  groundwork. Three pieces: (1) new **`templates/mp/_tab_institution.html`** as
  **tab ১৯. প্রতিষ্ঠান** (added to `_TAB_LIST` + a pane in `mp_detail.html`),
  grouped by parliament; (2) `/institution/` module list grouped **by MP**
  (paginates MPs); (3) `/reports/institution-assignments/` grouped by MP on
  screen/print/PDF, flat-but-MP-ordered in Excel/CSV. Institution create/edit/
  delete launched from a profile now return to `?active=tab-institution` (create
  previously landed on `tab-general` because no tab existed) and honour `from_mp`.
- **All grouping consolidated into `utils/assignment_grouping.py`** —
  `apps/ministry/grouping.py` **deleted**; its helpers are now generic:
  `mp_group_order(qs, rank_field=None)` / `build_mp_groups` / `all_mp_groups`
  (rank_field = `minister_type__ordering` for ministry, `role__ordering` for
  institution) plus `group_by_parliament(qs, *order_within)`. Importers:
  `apps/ministry/views.py`, `apps/institution/views.py`, `apps/reports/views.py`,
  `apps/mp/views.py`.
- **Latent biodata crash fixed** — `mp_biodata` still prefetched
  `institution_assignments__institution`, but that FK was retired in Phase 17.9
  (free text since). Any MP with institution rows raised
  `AttributeError: Cannot find 'institution' on InstitutionAssignment`; it stayed
  hidden ONLY because the table is empty — entering the first institution record
  would have 500'd the biodata page. Now prefetches `__role`/`__parliament`.
- **⚠ Django `{# #}` comments are SINGLE-LINE ONLY** — `django.template.base.tag_re`
  is compiled WITHOUT `re.DOTALL`, so `{#` … newline … `#}` is not a comment at all:
  it renders as **literal visible text on the page**. Four such comments introduced
  during this phase leaked onto the dashboard, ministry list, cabinet report and
  institution list on the live server (caught by the user). All collapsed to one
  line. **Use `{% comment %}…{% endcomment %}` for anything multi-line.** Guard: a
  regex scan for `{#` followed by a newline before any `#}` must find nothing
  across `templates/` (a `{#` surviving into rendered HTML is the same symptom).
- **CSV BOM bug fixed (found while testing the above, affected ALL 13 report CSVs)**
  — `export_csv` declared `content_type='text/csv; charset=utf-8-sig'`. Django
  encodes **every** `response.write()` with the declared codec, so the BOM was
  prepended to **every row**, corrupting the first column of every line
  (`﻿1,013050101,…`). Now `charset=utf-8` + a single explicit
  `response.write('﻿')`. Verified across 7 report CSVs: exactly one BOM, at
  byte 0.
- **PRP sync is MP-only** (confirmed with the user) — `import_mp_api` roster
  lookups use `parliament_members()`, plus a safety net that SKIPs any record
  whose `mp_id` matches an existing technocrat, so the API can never convert one
  into an elected member.
- **Seed** — `python manage.py seed_technocrats [--dry-run] [--parliament N]
  [--create-masters]`.
  Idempotent; resolves `Ministry`/`MinisterType` by bn-then-en name and **reports
  unresolved masters instead of creating them** (api_sync policy); refuses an
  `mp_id` already held by an elected member. **`--create-masters`** (opt-in) creates
  exactly the 4 Ministry + 2 MinisterType rows named in the doc — needed on a DB
  whose ministry masters are still empty, as the local dev DB was. Seeds the
  3 people / 4 assignments:
  `013050101` ড. খলিলুর রহমান (পররাষ্ট্র, মন্ত্রী) · `013050201` মোঃ আমিনুল হক
  (যুব ও ক্রীড়া, প্রতিমন্ত্রী) · `013050301` মোহাম্মদ আমিন উর রশিদ
  (মৎস্য ও প্রাণিসম্পদ **+** কৃষি, মন্ত্রী), all appointed 2026-02-17.
- **Biodata PDF** stays available for technocrats (election rows render empty).
- Verified on an isolated SQLite build (Django test client, 47 checks, all pass):
  seed dry-run/real/re-run, queryset splits, picker inclusion per module, tab
  hiding + `?active=` clamping, dashboard/report/ministry counts, cabinet
  filter + CSV column, create-redirect.
- **Local Docker stack seeded (2026-08-20)** — `mp/0008` applied, masters created
  via `--create-masters` (Ministry + MinisterType were 0 rows locally), 3
  technocrats + 4 assignments written. Live check: MP rows 352, `parliament_members()`
  349, technocrats 3; dashboard `total_mps=349 technocrat_mps=3`, mp_list 349
  (technocrat filter → 3), ministry list 4, cabinet 4, all_mp 349.
  ⏳ **production server not yet deployed** — needs SFTP sync, `docker compose up -d`,
  `migrate`, then `seed_technocrats --dry-run` there (the server DOES have ministry
  master data, so it should resolve without `--create-masters`; if any name differs,
  the dry run names it).

---

## PHASE 23 — Accompanying Officers from the PRP roster (2026-08-22) ✅
`/travel/create/` → *Accompanying Officers* was a **free-text** formset (ID /
name / designation typed by hand). PRP publishes the Secretariat employee
roster, so officers are now **picked from a synced list**. Full design +
verification log: `docs/officer-sync-plan.md`.

- **KEEP-RULE (locked with the user)** — an employee enters the system only if
  `class == 1` **AND** `status == 'Active'` **AND** he has a designation **AND**
  an office. Live payload: **3,839 employees → 227 kept** (skipped: 3,376 not
  class-1, 173 inactive, 63 incomplete). The 66 class-1 "Active" people with no
  designation/office are deliberately excluded — per the user they are stale PRP
  rows, not genuinely serving officers. The live `Finance Admin Test` account
  falls outside the keep-set for free.
- **New app `apps/officer/`** — `Officer` model keyed on `prp_id` (bilingual name
  + designation, partial office block, contact). `Officer.objects.selectable()`
  (`is_active=True`) is THE definition of "can be added to a tour", mirroring
  `MP.objects.parliament_members()`. **Photos are not stored** (user decision).
- **Rows are never deleted.** An officer who falls out of the keep-set is
  RETIRED: `is_active=False` + `deactivated_at` + a `deactivated_reason`
  (`inactive` · `class_changed` · `incomplete` · `absent`). He stays on tours he
  is already on, but cannot be searched or added to any NEW tour. If he returns
  to the keep-set the next sync reactivates him automatically.
- **`ForeignTourOfficer` freezes history** (`travel/0004`) — new `officer` FK
  (`PROTECT`, nullable) + `is_external`, and the snapshot columns went bilingual:
  `officer_id`→**`prp_id`** (an FK named `officer` claims the `officer_id`
  attribute — they would have collided), `name`→`name_bn` + new `name_en`,
  `designation`→`designation_bn` + new `designation_en` (also fixes a standing
  CRITICAL RULE #2 violation). The snapshot — not the FK — is what templates
  render, so a past GO reads exactly as recorded even after the officer's
  designation changes or he leaves.
- **`sync_officers` command** — token → `employeeInformations` → upsert by
  `prp_id` → retire absentees → link legacy free-text rows whose `prp_id`
  matches. Idempotent (2nd run: `created 0 · unchanged 227`).
  **Wipe-guard**: refuses to retire the roster if the keep-set is empty or under
  50 % of the currently-active count (a bad API response must never empty the
  picker); `--force` overrides. Flags: `--dry-run --file --limit --force`.
- **Roster page `/officer/` is ordered by PRP ID ascending** (user's call, 2026-08-22
  — do NOT "restore" the old `-is_active, name_bn` order). Every `prp_id` is a
  9-digit numeric string, so the plain text sort IS the numeric sort; no Cast
  needed unless PRP ever issues a shorter/longer id. The tour picker
  (`form_fields.py`) deliberately KEEPS name order — you type to search there,
  so alphabetical suggestions read better.
- **Roster page `/officer/`** (submenu under বিদেশ ভ্রমণ, `accounts/0006` seeds it
  on existing DBs and carries the tour-list role permissions across) — search by
  name/PRP-ID/designation, wing + status (active/retired/all) filters, tour
  counts, last-sync stamp, and a **Sync** button gated like `mp:sync_run`.
  Retired rows stay listed **with their reason** — that is where you find out why
  someone can no longer be added.
- **Tour form picker — TYPE-TO-SEARCH** (`{% officer_picker %}`,
  `apps/officer/templatetags/officer_picker_tags.py` → `partials/_officer_picker.html`).
  Two rounds of user feedback reshaped this, so do NOT "restore" either dropped
  piece: (1) the wing filter chips were removed — 22 of 227 officers have no
  wing, so the label fell back to the office name and the row rendered 25+
  buttons; (2) the always-visible scrolling list was removed — with 227 officers
  the user wants to type and pick, not scroll. Final shape: **search box →
  suggestion dropdown (max 12, ↑/↓/Enter/Esc) → selected officers as chips.**
  The full roster still ships as **hidden checkboxes** (`.of-picker-store`), so
  the POSTed `officers` field and its server-side validation are IDENTICAL to a
  plain multi-select — only visibility is JS-driven. Assets: **new**
  `static/css/officer_picker.css` + `static/js/officer_picker.js` (class prefix
  `.of-`, registered in `base.html`); the MP picker's `.mp-picker` CSS/JS is
  untouched and unaffected. Search index per officer = name bn+en · PRP ID ·
  designation bn+en · office · wing. The queryset is `selectable()` **plus
  officers already attached to this tour** — retired ones arrive pre-checked and
  render as an amber নিষ্ক্রিয় chip, so editing an old tour can never silently
  drop them; removing the chip + save drops them for good and they cannot be
  re-added (a new tour's store excludes them entirely: 226 vs 227).
- **External officers kept as an escape hatch** (user decision) — a collapsed
  *"PRP তালিকায় নেই এমন কর্মকর্তা"* accordion keeps the old formset for people
  outside the Secretariat (ministry/embassy), saved with `is_external=True` and
  never touched by sync. The picker handles rows with an `officer` FK, the
  formset handles rows without one — **disjoint sets**, so they never fight.
- **Shared PRP plumbing** — `utils/prp_api.py` (`get_token` / `fetch_json` /
  `secure_get` / `credentials`); `import_mp_api` now delegates to it
  (re-verified live: `--fetch --dry-run` still authenticates and reports).
- **Retired endpoints removed** — `travel:officer_add` / `officer_remove` (dead
  since the Phase 17.10 single-page form) deleted along with their URLs.
- **Two fixes found while testing** — (1) the Countries & Dates **ক্রম ("#")**
  column was 4rem wide but the cell inherits 1.25rem side padding, leaving the
  number unreadable → `.tf-col-order` trims the padding and floors the input at
  4.5rem; (2) `tour_list`'s `annotate()` sets `group_by`, which hides
  `Meta.ordering` from the paginator (`UnorderedObjectListWarning` — pages could
  repeat/skip tours) → explicit `.order_by('-go_date')`; same fix on the roster.

### Custom Report — MP picker + full EN labels (2026-08-22)
Field feedback on `/reports/custom-report/`:
- **"এমপি আইডি" filter → "সংসদ সদস্য / MP".** Options now read
  `ID — Name — Constituency` in the active language, so Select2's own text search
  covers all three. Built in the view (`custom_report`) from
  `MPChoiceField.annotated_queryset()`, because the old `.values('mp_id','name_bn')`
  rows are **dicts** and `|tr` uses `getattr` — on a dict it silently returned
  '', so the dropdown had been showing bare IDs with no name at all.
  The field still POSTs plain `mp_id` values, so `_build_custom_qs` is unchanged.
  Technocrats stay excluded (the report is MP-only).
- **Constituency filter removed** — redundant now that the MP picker searches by
  constituency. Template row, `sel['constituency']`, the `constituencies`
  queryset and the `enable_constituency` branch in `_build_custom_qs` are all
  gone; a stale bookmarked URL carrying it still returns 200 (ignored).
- **English mode was leaking Bangla.** Every hardcoded string on the page is now
  wrapped in `{% ui %}` (~30 of them: বয়স পরিসীমা, নির্বাচনের সংখ্যা, স্থায়ী কমিটি,
  all Select2 placeholders, buttons, breadcrumbs, result counts). The **column
  labels** were the other half: `CUSTOM_REPORT_COLS` is Bangla-only, so the
  column picker, screen table, print/PDF header and Excel/CSV headers all stayed
  Bangla. New `CUSTOM_REPORT_COLS_EN` + `_custom_cols()` resolve the pair for the
  active language (templates keep unpacking the same 2-tuples), and `_ui(bn, en)`
  is the Python-side `{% ui %}` for export headers. Verified: EN CSV header reads
  `SL,MP ID,Name (English),Constituency,Times Elected,Standing Committee`; BN
  unchanged. **`ALL_MP_COLS` / `CONTACT_COLS` have the same Bangla-only shape and
  were NOT touched** — same fix applies if those pages get the same report.
- **Same `|tr`-on-a-dict bug fixed in the Family Report** MP dropdown, which had
  been rendering `013000101 —` with no name in Bangla mode.

---

## PRODUCTION DEPLOY LOG

**2026-08-22 — Phases 22-follow-ups + 23 deployed to 172.16.220.158** (commit `e6573b6`).
55 files SFTP-synced (each md5-verified) + `docker compose restart web`; migrations
`accounts/0006` · `officer/0001` · `travel/0004` applied clean; collectstatic picked
up `officer_picker.css/js`. Backups `mp_*_backup_20260822_032133`.
`travel/0004` verified on the one existing free-text officer row: `officer_id`→`prp_id`,
`name`→`name_bn`, `designation`→`designation_bn`, all values preserved.
`sync_officers` on prod: **3,839 records → 227 kept** (3,376 not class-1 · 173 inactive
· 63 incomplete), the legacy free-text row auto-linked to its `Officer`; a second run
reported `created 0 · unchanged 227` (idempotent).

### ⚠ PRP API TLS — the missing intermediate (fixed 2026-08-22)
`prp.parliament.gov.bd` serves **only its leaf certificate** and omits the
`GoGetSSL RSA DV CA` intermediate that chains it to the USERTrust root. Windows
hides this by fetching the intermediate itself over AIA, so BOTH PRP commands
worked from a dev box and died inside the Linux container with
`[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer certificate`.
This is **unrelated to the system's own lack of TLS** (`USE_TLS=False`, plain
HTTP on :80) — that governs inbound browser traffic; this is the app acting as an
outbound *client*, which needs no certificate of its own.
Fix: the intermediate ships as **`utils/certs/prp_chain.pem`** and
**`prp_api.ssl_context()`** builds `ssl.create_default_context()` + that cert, used
by `fetch_json()` and by `import_mp_api._download()` (photo/signature URLs hit the
same host). It **adds** trust rather than disabling verification, so it keeps working
if PRP ever fixes their chain. Do NOT "simplify" this to `verify=False`.

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
| `docs/technocrat-plan.md` | Technocrat ministers — why they reuse the MP model, the "350 means 350" exclusion list, picker/sync scope rules |
| `docs/officer-sync-plan.md` | PRP officer roster — the keep-rule, retirement semantics, frozen tour snapshot, wipe-guard, verification log |
| `docs/API.txt` | PRP endpoints (token / employeeInformations / offices) + a sample employee record |
