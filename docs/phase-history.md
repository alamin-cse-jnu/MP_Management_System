# Phase history — MP Information Management System

Build log for Phases 15–25 plus the production deploy log. Split out of
`CLAUDE.md` so it no longer loads into every session. Read it when you need the
history or rationale behind a specific phase; the live traps it contains are
summarised in `CLAUDE.md` → `## GOTCHAS`.

---

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

## PHASE 24 — Field-feedback fixes (2026-08-23) ✅
Four user observations on the running local stack. Two were real bugs, two were
missing fields/UX.

- **Spouse + Child মোবাইল নম্বর** — `Spouse.mobile` / `Child.mobile`
  (CharField 30, blank; migration `mp/0009`). Added to `SpouseForm` (after NID)
  and `ChildForm` (after NID/birth-reg), to both add/edit templates, and as a
  column on the read-only `_tab_spouse.html` / `_tab_children.html` tables.
  Not added to the biodata PDFs (not requested).

- **Education page: picking a Result Type showed NOTHING in Result.** Two
  independent causes, both fixed:
  1. **The display toggle was a no-op.** `education_sections.html` styles
     `.edu-result-field { display: none; }` in CSS but the cascade JS revealed a
     block with `b.style.display = ''`. Clearing an inline style does not
     override a stylesheet rule — it hands the element straight back to
     `display:none`, so the "revealed" input was never visible for ANY result
     type. Now sets an explicit **`'block'`** (same trap fixed on the
     `.edu-result-empty` / `.edu-result-warn` rows). **Never toggle visibility
     with `style.display = ''` when a CSS rule hides the element.**
  2. **`DivisionResult` master was empty (0 rows) on every DB**, so even once
     visible, "বিভাগ" revealed a dropdown with no options. Migration
     `master/0010_seed_result_masters` seeds the 4 canonical division results
     (প্রথম/দ্বিতীয়/তৃতীয় বিভাগ · উত্তীর্ণ) **and** the missing `ResultType` rows
     keyed by `result_format` (gpa · cgpa · percentage · pass_fail joined the two
     that existed) so every format the form supports is reachable. `get_or_create`
     never touches an admin-created row.
  - Safety net added: if a revealed block's only control is a dropdown with no
    options, an amber "no options exist — add them in Master Data" line replaces
    the silently-empty select, linking to `master:education_master`.
  - Browser-verified: all 6 result types reveal their matching control, Division
    lists 4 options, and the warning appears/disappears with the pool.

- **`/mp/` search now filters as you type** (no more type-then-click-Filter).
  The results table + pagination + count moved to **`templates/mp/_mp_list_results.html`**;
  `mp_list` returns just that partial when `HX-Request` is set. The filter
  `<form>` carries `hx-get`/`hx-target="#mp-results"`/`hx-push-url="true"` with
  `hx-trigger="keyup changed delay:300ms from:#mp-search, search from:#mp-search,
  filters-changed"`, so search + parliament + type + status always travel
  together and the URL stays shareable. Spinner via `hx-indicator`; the Filter
  button remains the no-JS fallback.
  - **⚠ Select2 fires jQuery events, not native ones.** The dropdowns' old
    `onchange="this.form.submit()"` worked only because jQuery's `.trigger()`
    also invokes a matching inline `on*` attribute — it does **not** dispatch a
    native DOM event, so htmx's native `change` listener never fires. Replacing
    the inline handler with a plain htmx `change` trigger silently broke the
    dropdowns (verified: value changed, no request). Fixed with a jQuery bridge in
    `{% block extra_js %}` that re-emits `htmx.trigger('#mp-filter-form',
    'filters-changed')`. **Any future htmx-on-change over a Select2 control needs
    this bridge.**
  - Browser-verified: 349 → 297 → 40 → 10 → 2 as "Mirza" is typed (Bangla too:
    144 → 51 → 18 for "আবুল"), Select2 picks on Type/Status re-filter, combined
    search+dropdown works, empty state renders.

- **⚠ Templates are cached by gunicorn** — production settings compile templates
  once per worker, so a template edit on the bind-mounted local stack is NOT
  visible until `docker compose restart web`. The Django test client (fresh
  process) will show the new markup while the browser still shows the old one;
  this masked the education display bug for one round of testing.

✅ **Deployed to production 2026-08-23** — see the deploy log below.

---

## PHASE 25 — NOC generation for MP foreign travel (2026-08-23) ✅
`/travel/create/` recorded the tour GO, but the **অনাপত্তি সনদ / No Objection
Certificate** was still typed by hand in Word. Now generated from the tour + MP
data, edited in CKEditor, and printed / downloaded as PDF or Word.
Source scans: `docs/NOC for MP/`.

### ⚠ The samples are TWO DIFFERENT DOCUMENTS, not one translated
| | `NOC Sample-1/2.pdf` (English) | `NOC Bangla Sample-1/2.png` |
|---|---|---|
| What | the certificate itself | the **forwarding letter** that issues it |
| Letterhead | logo + right-hand contact block | centred text only, no logo |
| Body | `Sub:` + one "This is to certify that…" paragraph | `বিষয়:` + two numbered paras + `সংযুক্ত: অনাপত্তি সনদ।` |
| Extra | — | second block on the SAME page: **অনুলিপি** list (7 recipients) + a second signature |
| Date | `20 August 2026` | dual `০২ ভাদ্র ১৪৩৩` / `১৭ আগস্ট ২০২৬`, Bengali digits |

Each carries its **own memo number**, so a Bangla NOC and an English NOC are two
independent `NOC` rows. Do not "unify" them into one bilingual document.

### New app `apps/noc/`
- **`NOCLetterhead`** — one active row (`NOCLetterhead.current()`, self-creating):
  org/wing/section/website/phone/fax/email/address (bn+en), `memo_prefix`, and
  **`speaker_title_bn/_en`** — that one flips between Speaker and Acting Speaker
  with who presides, so it must never be hardcoded. Edited at `/noc/settings/`.
- **`NOCTemplate`** — `language` + `body_html` carrying `{placeholder}` tokens,
  seeded by `noc/0002` from the scans. ⏳ **the Bangla wording is transcribed from
  an image — proofread it at `/noc/settings/`.**
- **`NOC`** — tour + mp + language + memo_no + serial_no + issue_date + spouse +
  signatory (+ snapshot) + `body_html` + status. **No unique constraint** on
  (tour, mp, language): a corrected re-issue is legitimate.
- **The signatory is snapshotted** from the PRP roster exactly like
  `ForeignTourOfficer.snapshot_fields()`, so an old NOC still reads correctly
  after the officer transfers. New `OfficerChoiceField` (single-select sibling of
  `OfficerMultipleChoiceField`) in `apps/officer/form_fields.py`; both now share
  `_officer_label()`.

### Generation — `apps/noc/generation.py`
`build_context()` returns a flat dict; `render_body()` fills it by **regex token
substitution, never the Django template engine** — a DB-stored template must not
be able to execute template tags. Unknown tokens are left visible (a template typo
shows up rather than silently blanking); `unresolved_tokens()` reports them.
`next_serial()` + `suggest_memo_no()` auto-number from `memo_prefix` + 2-digit
year + serial; the field stays hand-editable.

### New utilities
- **`utils/bangla_date.py`** — Gregorian → বঙ্গাব্দ on the **revised Bangladesh
  calendar** (১ বৈশাখ = 14 April always; six 31-day months, five of 30, চৈত্র 30,
  ফাল্গুন 29 — 30 in a Gregorian leap year). Verified against both samples, both
  year boundaries and a full 365-day walk. Also `format_range_en/bn` reproducing
  the samples' compression (`10 to 28 August 2026`, `২১-২৯ আগস্ট ২০২৬`).
- **`utils/html_to_docx.py`** — python-docx walker over the editor's HTML (stdlib
  `html.parser`). **`_set_run_font()` sets `w:cs` (and `w:szCs`), not just
  `w:ascii`/`w:hAnsi`** — Bengali is a *complex script*, so without `w:cs` Word
  falls back to Times New Roman and renders boxes. A bounded converter by design:
  odd pasted markup degrades to plain paragraphs rather than raising.
- **`utils/html_sanitize.py`** — allowlist run on every save (`body_html` is later
  rendered `|safe`). Strips `<script>`/`<iframe>` with their content, all `on*`
  handlers, `javascript:` URLs and `url()` inside CSS; unknown tags lose the tag
  but keep their text.

### Editor
CKEditor 5 **super-build 41.4.2, vendored** at `static/vendor/ckeditor5/` (UMD
global `CKEDITOR`; v41 needs no licence key — v44+ would). Shared init in
`static/js/noc_editor.js`, used by both the document editor and the template
editor. Two settings that break it if removed:
- **`removePlugins: PREMIUM`** — the super-build bundles the commercial plugins;
  left in, they demand a licence key and the editor never mounts.
- **`htmlSupport: { allow: [{name: /.*/, attributes: true, classes: true, styles: true}] }`**
  — without it CKEditor strips the inline column widths, `text-indent` and
  `font-size` the layout depends on, and the letterhead collapses to one column.

CKEditor writes back to its `<textarea>` only through its own submit handling, so
the init hooks the form's `submit` event and copies `editor.getData()` across.

### Layout is table-based ON PURPOSE
WeasyPrint (PDF), the browser (print) and the docx walker all reproduce table
columns faithfully; float/flex layout survives none of the three.

### Output — one A4 shell, three formats
`templates/noc/print/noc_document.html` deliberately does **not** extend
`base_print.html` (which stamps a generic report header on every page).
`?format=print` · `?format=pdf` through the existing
`render_report_pdf(..., landscape=False)` · `?format=docx` through
`utils/html_to_docx.py`. **New dependency `python-docx==1.1.2` → deploying this
needs `docker compose up -d --build`.**

- **The Bangla letter needs its own page box.** Letter + অনুলিপি list on one sheet
  overflowed to two pages at the shared settings. Fixed with `body.noc-bn`:
  `@page` margin `12mm 16mm` (vs `15mm 18mm`), `font-size: 11.5pt`,
  `line-height: 1.38`, tighter `li`. Mirrored in `static/css/noc.css` for the
  preview. **Keep those two in sync** — loosening either re-splits the page.
- pypdf's `extract_text()` renders Bangla as gibberish even when the PDF is
  perfect: SolaimanLipi is embedded as a CID/Type0 subset and ligature glyphs do
  not reverse-map. Check `/Producer` and the embedded font list, or look at the
  page, rather than trusting extracted text.

### Entry points
`/travel/<pk>/` gains an **অনাপত্তি সনদ (NOC)** card — one row per participant with
their passport, the NOCs already issued, and two issue buttons (Bangla letter /
English certificate). `/noc/` lists everything with the same HTMX live-search
pattern as `/mp/`, **including the Select2 → htmx jQuery bridge** (see Phase 24).
Submenus under বিদেশ ভ্রমণ via `fixtures/initial/noc_menu.json` +
`accounts/0007_noc_submenu` (carries `travel:tour_list` role permissions across).
`('apps.noc', 'NOC')` added to `AUDITED_MODELS`.

### Passport capture on the tour form
`MP.passport_number` is what the NOC prints, and it is often blank when a tour is
entered — so `/travel/create/` now shows a **Participant passports** panel: one row
per ticked MP, prefilled from the profile (tagged প্রোফাইল থেকে / from profile) or
blank (নতুন / new), written back to the profile on save.
`static/js/tour_passports.js` only *listens* to the picker's checkboxes —
**`mp_picker.js` and `partials/_mp_picker.html` are untouched**, because committee
step-1 and the institution bulk form share them. **An absent or blank input never
clears a stored passport** (a JS failure must not wipe data); clearing one is a
profile-level action.
`Spouse.passport_number` added too (`mp/0010`) — English sample-2 prints the
accompanying spouse's passport number.

### Field-feedback round 1 (2026-08-23)
Five fixes from the first real use of the NOC pages.

- **Stray horizontal rules in every generated letter.** CKEditor wraps each table
  it saves in **`<figure class="table">`**, and `table` is also a *Bootstrap
  component* class: `.table > :not(caption) > * > *` then paints
  `border-bottom: 1.1px solid #000` and `padding: 8px` onto every `<tr>`. So a
  document grew a black rule under each row the moment it was saved — the
  templates themselves were clean, which is why only *saved* letters showed it
  (measured with `getComputedStyle`: `1.11111px` inside the figure, `0px`
  outside). Fixed in `utils/html_sanitize.py`: `TRANSPARENT_TAGS = {'figure'}`
  unwraps the wrapper (keeping its children), and `DENY_CLASSES = {'table'}`
  strips that class wherever it appears. This also drops `figure`'s Reboot bottom
  margin and helps the DOCX/PDF paths. Existing rows were re-sanitised in place.
  **Any future editor-authored HTML rendered inside the app must not carry
  Bootstrap component class names.**

- **Changing the Date / Signatory / Memo No did nothing to the letter.** Because
  the whole page is `body_html`, those values live both as columns and as text
  inside the HTML. `noc_edit` now keeps them in step:
  - **is_pristine → re-render.** If the body is still exactly what the template
    produces, it is re-rendered from the new context. This is what makes a
    *blank* signatory work: there is no old text to find, so a patch could never
    insert it.
  - **hand-edited → `patch_body()`.** Only the old rendered strings are swapped
    for the new ones (`generation.SYNCED_KEYS`), so manual edits survive.
    Keys that changed but had nothing to replace are reported and the user is
    told to press Regenerate.

- **Signatory selection silently did nothing.** `form.is_valid()` runs
  `construct_instance()`, which writes the posted FK straight onto the instance —
  so the old guard `officer.pk != noc.signatory_id` compared the new value with
  itself and was **always False**, and `snapshot_signatory()` never ran: the FK
  moved while the printed name/designation stayed stale. `noc_edit` now captures
  the old state **before** binding the form and snapshots unconditionally.
  **Never read pre-edit state off a ModelForm's instance after `is_valid()`.**

- **Template picker removed** from the editor (user: not their concern). It stays
  on the model as plumbing for Regenerate; `NOCForm.Meta.fields` no longer lists it.

- **Tour page shows ISSUED documents only.** `/travel/<pk>/` lists **final** NOCs
  only, at most one per language (latest wins if a correction was re-issued), and
  offers the issue button only while that language has no final — once both exist
  the cell reads "উভয়টি জারি হয়েছে". A muted "N টি খসড়া চলমান" link appears when
  drafts exist, so the same NOC is not started twice. Drafts are managed at
  `/noc/`, where **drafts are deletable and finals are not** — the list shows a
  lock instead of a bin, and `noc_delete` refuses a final server-side too, since
  hiding a control is not a permission check. It honours a local-path `?next` so
  deleting from the list returns to the list.

### Verified on the local Docker stack
Bangla calendar against both samples; both documents generate with **zero
unresolved placeholders**; the spouse clause and signatory block match sample-2's
wording; PDF is 1 A4 page each from WeasyPrint 69 with SolaimanLipi embedded;
DOCX is A4 with tables + logo preserved and `w:cs=SolaimanLipi` on runs; CKEditor
mounts with a full toolbar and a save round-trip preserves the logo, all four
tables and the `18%` column widths; the sanitiser strips script/onclick/iframe
while leaving the document intact; passport prefill / back-fill / no-clobber;
letterhead + template saves; regression sweep over travel, committee,
institution, mp and reports.
✅ **Deployed to production 2026-08-23** — see the deploy log below.

---

## PHASE 26 — Field-feedback round 2 (2026-08-30) ✅
Six user observations from the running stacks (local + 172.16.220.158).

- **Users need পদবি + ছবি.** `CustomUser.designation_bn` / `designation_en`
  (CharField 200, blank) and `photo` (ImageField → `media/user_photos/`);
  migration `accounts/0008`. Both create and update forms carry them, the form is
  now `enctype="multipart/form-data"` and its views pass `request.FILES`, and the
  `_BootstrapMixin` learned to style a `ClearableFileInput`. The list page gained
  a photo thumbnail (falling back to the initial-letter `.mp-avatar`) and a
  Designation column, and `?q=` now searches designation too. The topbar and
  sidebar footer show the photo when set and prefer designation over role.
  New CSS: `.mp-avatar-img` / `.mp-avatar-img-sm` — same footprint as the
  initial-letter avatar so the header does not shift.

- **The same street address is retyped three times.** Each address sub-tab now
  offers a **"একই ঠিকানা?" tick per already-saved sibling** (present / permanent /
  ঢাকাস্থ). The tick greys out and disables that tab's location + address-detail
  card; the copy itself happens **server-side** in `mp_address_save`, which reads
  the source row and overwrites `_ADDRESS_COPY_FIELDS` on the target.
  - Server-side on purpose: copying in the browser would mean replaying the
    division→district→upazila cascade (three fetches) just to make the target's
    dropdowns contain the source's options. Copying after `form.save(commit=False)`
    sidesteps queryset validation entirely.
  - **Contact fields are never copied** — telephone/mobile/whatsapp/e-mail belong
    to the present address only.
  - A tick naming an address that is not saved yet is refused with a message
    rather than writing a blank row; a tick that names its own type is ignored.

- **Every date field showed MM/DD/YYYY.** A native `<input type="date">` renders
  in the **browser's** locale, so nothing the server sends can change it. Two
  halves to the fix:
  1. **`static/js/date_dmy.js` + flatpickr 4.6.13** (CDN, beside the other
     vendored CDN libs). Attached in `altInput` mode: the visible box is a text
     input formatted `d/m/Y`, the original input is switched to `type=hidden` and
     keeps the ISO `Y-m-d` value — and only the original carries the `name`, so
     that is what posts. `allowInput` lets the user type `25/12/1980` directly.
     Idempotent and re-run on `htmx:afterSwap`, `shown.bs.modal`, `shown.bs.tab`;
     `window.enhanceDateFields(root)` is exposed for hand-built rows.
  2. **`utils/form_dates.normalize_date_fields(form)`**, called at the end of all
     ten `_BootstrapMixin.__init__`s. Pins `widget.format` to `%Y-%m-%d` and sets
     `input_formats` to a locale-independent list.
  - ⚠ **This fixed a live bug, not just cosmetics.** Django renders a bound date
    with the *active locale's first* `DATE_INPUT_FORMATS` entry — `%d/%m/%Y` under
    `bn`. `<input type="date">` rejects a non-ISO value attribute, so **in Bangla
    mode every saved date rendered as an empty box.** Pinning the widget format
    to ISO is what makes both the input and flatpickr see the stored value.
  - The normaliser sets `widget.input_type`, not `attrs['type']`: a `type` left in
    attrs is rendered *in addition to* the widget's own, so every date input was
    emitting a duplicate `type="date"` attribute.

- **Education: SSC/HSC must not offer a university, degrees must not offer a
  board.** `EducationSectionForm` now splits the `EducationInstitution` pool by
  the section's `level_type` (types come from Master Data, as asked):
  | section | শিক্ষাবোর্ড (`board_affiliation`) | প্রতিষ্ঠান (`institution`) |
  |---|---|---|
  | SSC / HSC / Diploma | `inst_type='board'` | everything **except** board/university/foreign |
  | Graduation / Masters / PhD | university + foreign | university + foreign |
  - `_keep_current()` widens either queryset to still contain a value that is
    **already stored** but would now be filtered out — otherwise a mistyped master
    row would be silently wiped the next time the section was saved.

- **Bank শাখা was not bilingual.** The model always had `branch_name_bn/_en`;
  three templates just rendered `.bank_name_bn` / `.branch_name_bn` directly.
  `_tab_bank.html`, `reports/mp_biodata.html` and `reports/pdf/mp_biodata_xhtml.html`
  now use `|tr:"bank_name"` / `|tr:"branch_name"` (the PDF `mp_biodata_bn.html`
  already did).

- **Biodata PDF: Member Type + Nationality were Bangla-only.**
  - `get_member_type_display()` can only ever return the Bangla half of
    `MEMBER_TYPE_CHOICES`. Added `MP.MEMBER_TYPE_LABELS` plus `member_type_bn` /
    `member_type_en` properties so the existing `tr` filter works:
    `{{ mp|tr:"member_type" }}`. Swapped in across mp_detail, `_tab_election`,
    both biodata PDFs and `print/cabinet.html`. (`reports/views._custom_cell`
    already had its own `MEMBER_TYPE_EN` map and was left alone; `report_tags._cell`
    is Bangla-only by design.)
  - `MP.nationality` was a single CharField, against the bilingual rule. Split into
    `nationality_bn` / `nationality_en` — migration **`mp/0011_mp_nationality_bilingual`,
    hand-written**: `makemigrations` proposes RemoveField + AddField, which drops
    every stored nationality, so it uses **RenameField** and then backfills
    `nationality_en` from an **NFC-normalised** match on the Bangla value
    (`বাংলাদেশী` / `বাংলাদেশি` → `Bangladeshi`, anything else left blank for an
    operator). Verified on all 352 local rows.

Verified: 34 content assertions over both languages (users list/form, address copy
POST incl. the contact-fields-not-copied case, DD/MM/YYYY round-trip both ways,
the four education pools, bank branch, biodata HTML+PDF), plus browser checks —
8 date fields on `/mp/1/` all showing `DD/MM/YYYY` while posting ISO, and the
Dhaka tab's copy ticks dimming/disabling the right card.

---

## PHASE 27 — Personal / pre-tenure foreign travel (2026-08-30) ✅
The profile's travel tab listed only GO-based tours and led with a button into
the system-wide travel module. Two things were wrong: the tab did not read as
*this MP's* travel, and there was nowhere to record a trip the MP took **before**
their parliamentary career (or privately), which has no GO and never will.

**Model** — `mp.PersonalForeignTravel`, deliberately in `apps/mp/` rather than
`apps/travel/`: it is an MP sub-record like Award/Publication, and `travel`
already imports `mp` (the reverse would be circular).

| field | rule |
|---|---|
| `country` FK → `master.Country` | **required — the only one** |
| `purpose` FK → `master.TravelPurpose` | optional |
| `from_date` / `to_date` | optional; `clean()` rejects a reversed pair |
| `note_bn/_en`, `ordering` | optional |

No parliament FK **on purpose** — predating the tenure is the whole point. Only
country is required because a decades-old trip is still worth recording when the
MP no longer remembers the purpose or the exact dates. `Meta.ordering` is
`from_date DESC nulls_last` so undated rows sink rather than float to the top.
No new master data: Country and TravelPurpose already exist and are admin-managed.

**Tab** — `_tab_travel.html` rebuilt as two sections under a heading that names
the MP:
1. **দাপ্তরিক ভ্রমণ (GO-ভিত্তিক)** — read-only, **one row per country visited**
   (country · purpose · duration · type · GO no.). Per-country rows fit the
   requested columns better than one row per GO, since `ForeignTourCountry`
   carries its own dates. A GO whose country rows are not filled in yet still
   renders one summary row rather than vanishing.
2. **ব্যক্তিগত / পূর্ববর্তী ভ্রমণ** — full add/edit/delete, following the
   award/publication CRUD pattern.

The "ভ্রমণ মডিউল" button is demoted to a small text link beside the official
section; the primary button is now **+ ভ্রমণ যোগ করুন**.

- **`ForeignTourCountry.effective_from_date` / `effective_to_date`** — a leg's
  own dates, falling back to the tour's overall span. Added because
  `{% firstof a b as var %}` stores the **rendered string**, not the date object,
  so `{{ d|date:"d/m/Y" }}` on it silently produces nothing. Model properties
  keep the fallback out of the template entirely.
- The view does **not** call `full_clean()` after `form.save(commit=False)` —
  `ModelForm._post_clean()` already runs `Model.clean()`, so the reversed-date
  check surfaces as a proper field error instead of an uncaught `ValidationError`.

**Biodata** — section 18 in all three biodata templates now unions both sources
and gains a **ধরন / Type** column labelling each row দাপ্তরিক / ব্যক্তিগত.
Travel *reports* stay GO-only: they are administrative documents about the GO
process, not the MP's life history.

**Not changed:** MP sub-CRUD URLs like `mp:award_create` derive a `mp:award_list`
submenu that does not exist, so `perm_required` finds no SubMenu and enforces
login only. The new travel CRUD inherits that same gap. Pre-existing across every
MP sub-CRUD — closing it would need SubMenu rows for all of them and could lock
out existing roles, so it was left alone deliberately.

Verified: 27 assertions over both languages — both sections render, country-only
save works, a missing country is rejected, reversed dates are refused with a
visible error, rows appear on the tab and in the biodata HTML + PDF, delete works,
and no other MP's GO leaks onto the tab. Browser-checked with a real 4-country GO
plus one full and one country-only personal row.

---

## PHASE 28 — Master-data completeness (2026-08-30) ✅
Three user observations, all variations on "this field should come from Master
Data, and it doesn't".

### 28.1 — Bilingual name columns (deployed separately, see the deploy log)
Every "বাংলা নাম | English Name" **pair** rendered its first column as
`{{ obj|tr:"name" }}`. `tr` follows the *UI* language, so in English mode both
columns showed English. Fixed in the three master templates that cover every
master-data menu, plus parliament / constituency / menu / role. A single column
headed just "Name" keeps `tr` — that one *should* follow the UI language.
Recorded as gotcha 8.

### 28.2 — Class results from Master Data
Picking result type **বিভাগ / Division** revealed a populated dropdown; picking
**শ্রেণি / Class** revealed an empty text box. Same field, two behaviours,
because `Education.class_result` was a free-text CharField while
`division_result` was an FK.

- **`master.ClassResult`** — sibling of `DivisionResult`, same shape, managed on
  `/master/education/` as a new **শ্রেণি ভিত্তিক ফলাফল / Class Results** tab.
  `master/0011` creates it and seeds প্রথম/দ্বিতীয়/তৃতীয় শ্রেণি, matching on the
  **NFC-normalised** Bangla name *and* the English name so it cannot duplicate
  prod's existing rows (gotcha 17).
- **`mp/0013` converts the field, hand-written.** `RenameField` to a legacy
  column → add the FK → `RunPython` backfill → drop the legacy column. The
  backfill matches free text against either language, and **creates a master row
  for any value it does not recognise**, so dropping the old column cannot lose a
  typed value. Verified by migrating a scratch dataset holding prod's exact case
  (`First Class`) plus a deliberately unmapped `Grade A`: 3 in, 3 out, 0 nulls,
  and `Grade A` survived as a new master row.
- Both dropdowns are now built the same way — `_keep_current()` so a
  deactivated-but-stored option is never silently wiped, and `data-no-select2`
  so they render correctly inside the hidden result block.
- **`result_display` was Bangla-only** (`self.division_result.name_bn`), so the
  English biodata printed Bangla results. Replaced with
  `result_display_bn` / `result_display_en` properties + `{{ edu|tr:"result_display" }}`
  in all five consuming templates.
- The legacy `partials/education_result_fields.html` + `master:result_fields`
  view (dead since Phase 17.11 — no template references the URL) was updated to
  match rather than left contradicting the model.

**Still free text: `result_text`, used by the `pass_fail` result type.** Prod has
one row (`পাস`). It is the same shape of problem and would be the same fix; left
alone because only `class` was asked for. Note prod has already worked around it
by adding `উত্তীর্ণ / Pass` to **DivisionResult**.

### 28.3 — Year-only travel
An MP often remembers only "sometime in 2024", not exact dates, and recording
that beats recording nothing.

- `PersonalForeignTravel.year` (optional IntegerField, 1900–2100).
- **`sort_year`**, a denormalised sort key kept in sync by `save()`
  (`from_date`'s year if dated, else `year`). Without it a year-only row has no
  date to sort on and sinks below every dated row no matter how recent — the new
  `Meta.ordering` leads with `sort_year DESC nulls_last`. `save()` parses a
  string date as well as a `date`: Django does not coerce on assignment, so an
  importer or data migration doing `objects.create(from_date='2012-07-10')`
  would otherwise crash on `.year`. `mp/0015` backfills rows written before the
  column existed.
- **`when_display`** property — `'01/05/2019 – 20/05/2019'`, or `'2024'`, or
  `'—'` — so the profile tab and all three biodata templates cannot drift apart.
- `clean()` rejects a year that **contradicts** a typed `from_date`: that is a
  data-entry slip, not a second fact. Out-of-range years are refused too.
- The form groups departure/return/year into one "কখন / When" block that says in
  so many words that the year alone is enough.

Verified: 33 assertions — both result dropdowns populated and native, the class
result saving as an FK and rendering per-language, year-only save, the
date-range case, ordering (2024 year-only sorts above 2019 dated), both rejection
paths, the travel tab, all three biodata templates and the PDF, and the new
Master Data tab in both languages.

---

## PRODUCTION DEPLOY LOG

**2026-08-30 (c) — Phase 28.2 + 28.3 deployed to 172.16.220.158.**
Class-result master table + year-only travel. Migrations `master/0011` ·
`mp/0013` · `mp/0014`.

- **`mp/0013` rewrites a live column**, so it was rehearsed first: a scratch
  dataset holding prod's exact value (`First Class`) plus a deliberately
  unrecognised `Grade A` migrated 3-in / 3-out, 0 nulls, with `Grade A` preserved
  as a newly created master row.
- Prod pre-state: 16 education rows, **1** with `class_result='First Class'`,
  5 with a `division_result`, 1 with `result_text='পাস'`.
- `result_text` (the `pass_fail` type) is deliberately still free text — see
  Phase 28.2.
- **Follow-up `mp/0015` (same day).** Post-deploy verification found three
  user-entered travel rows with `sort_year=NULL` — `0014` added the column but
  `sort_year` is only maintained by `save()`, so rows written before it existed
  stayed NULL and, under `sort_year DESC nulls_last`, sank below every later row
  regardless of date. `0015` backfills from `from_date`/`year`. Prod's three rows
  now read 2012 / 2006 / 2006.
- The same check exposed a latent crash: `save()` did `self.from_date.year`, but
  Django does not coerce on assignment, so `objects.create(from_date='2012-07-10')`
  (any importer or data migration) reached `save()` with a **str** and raised
  `AttributeError`. `_year_of()` now parses either form.
- ⚠ Verification-script lesson: the personal-travel rollback check asserted
  `count() == 0`, which was only true on an empty table. Real user rows appeared
  between deploys and it reported a false failure. Assert on *your own* fixture,
  never on a global count.

**2026-08-30 (b) — bilingual name-column fix deployed to 172.16.220.158.**
7 templates, md5-verified; no migrations, no static, `docker compose restart web`
(templates are compiled once per gunicorn worker — gotcha 2 — so a restart is
mandatory even for a template-only deploy).

- **Bug:** every "বাংলা নাম | English Name" **pair** rendered its first column as
  `{{ obj|tr:"name" }}`. `tr` follows the *UI* language, so in English mode both
  columns showed the English name. Correct in Bangla mode, which is why it
  survived this long.
- **Fix:** a column whose header names a language renders that language
  literally — `{{ obj.name_bn }}` / `{{ obj.name_en }}`. Fixed in
  `master/generic_list.html`, `master/partials/edu_panel.html`,
  `master/partials/group_panel.html` (these three cover **every** master-data
  menu, standalone and grouped), and — same bug, found while checking — in
  `parliament_list`, `constituency_list` (name pair *and* the district bn/en
  pair), `accounts/menu_list` (menu + submenu rows) and `accounts/role_list`.
- **Deliberately not changed:** `user_list.html`, whose single name column is
  headed just "Name" and *should* follow the UI language. Same for
  `master/home.html`'s tile labels.
- Verified: 19 pages × 2 languages — every "Bengali Name" cell stays Bangla in
  English mode, and on populated tables the two columns are confirmed to hold
  *different* values (e.g. `ঢাকা` / `Dhaka`, `কৃষি মন্ত্রণালয়` /
  `Ministry of Agriculture`). Recorded as gotcha 8 in CLAUDE.md.

**2026-08-30 — Phases 26 + 27 deployed to 172.16.220.158** (working tree on top of `f0b5fb5`;
deployed **uncommitted** — commit locally to keep the log anchored).
42 files SFTP-synced, each md5-verified; no `--build` (`requirements.txt` unchanged), so
`docker compose restart web`. Backups `mp_code_backup_20260830_042754.tgz` (9.4 M) +
`mp_db_backup_20260830_042754.sql` (2.0 M).
Migrations `accounts/0008` · `mp/0011` · `mp/0012` applied clean; collectstatic picked up
`date_dmy.js` + `theme.css`.

- **`mp/0011` (nationality split) verified against real data.** Pre-flight showed prod holds
  exactly two values — 350 × `বাংলাদেশী` and 2 × `বাংলাদেশি` (they differ in the final vowel
  sign, ‌`0x9c0` vs `0x9bf`) — both inside the migration's NFC-normalised match set. After:
  **352/352 kept `nationality_bn`, 352/352 backfilled `nationality_en='Bangladeshi'`.** The
  hand-written `RenameField` is what made this non-destructive; the autogenerated
  RemoveField+AddField would have wiped all 352.
- Verified: 19 pages × 2 languages all 200, all seven observation items re-checked on prod,
  biodata PDF renders (WeasyPrint, 141 KB bn / 132 KB en), zero traceback/exception lines
  since restart, counts unchanged (mp=352 tours=51 officers=227 ministry=64 users=18).
  The personal-travel write path was exercised inside a transaction that was rolled back, so
  `mp_personalforeigntravel` is left at 0 rows.
- **⚠ Operational note — the SSC/HSC "প্রতিষ্ঠান" dropdown is empty on prod.** All 33
  `EducationInstitution` rows are typed `university` (20) or `board` (13); **none** are `other`,
  and the new school-level Institute pool excludes board/university/foreign by design (Phase 26).
  No data is at risk — 0 stored education rows reference an excluded value, and all 7 school-level
  rows only set the board — but staff cannot pick a school/college until those are added in
  Master Data with type **Other**.

**2026-08-23 — Phases 24 + 25 deployed to 172.16.220.158** (commit `f0b5fb5`, range `e6573b6..HEAD`
= `db01557` TLS sync + `2b6ca04` employee order + `f0b5fb5` issues and NOC).
59 files SFTP-synced (each md5-verified). **First deploy needing `--build`** since
`requirements.txt` gained `python-docx==1.1.2`: `docker compose build web` (old container kept
serving) → `docker compose up -d web`; gunicorn answered in 5s. Migrations `accounts/0007` ·
`master/0010` · `mp/0009` · `mp/0010` · `noc/0001` · `noc/0002` all clean; collectstatic took 6 files
including the 4.3 MB vendored CKEditor bundle (nginx serves it, 200/4328436 B).
Backups `mp_*_backup_20260823_075810` (5.5 M code, 1.9 M db).
Verified on prod: 14 pages 200, MP live-search partial, both NOC templates render with **zero
unresolved placeholders** against a real tour, PDF 1 A4 page each from WeasyPrint 69 with
SolaimanLipi embedded, DOCX valid, `noc_noc` still 0 rows (nothing test-created), logs clean,
row counts unchanged (mp=352 tours=45 officers=227 ministry=64).

- **Two `docker compose` gotchas met here:** `docker compose images web` exits 1 right after a
  rebuild ("No such image: sha256:…" — it still resolves the replaced image id), which makes a
  successful build look failed; and `docker compose exec` does **not** inherit the entrypoint's
  `DJANGO_SETTINGS_MODULE`, so pass `-e DJANGO_SETTINGS_MODULE=config.settings.production`.
  `static_collected` is a named **volume**, so `ls` it inside the container, not on the host.
- **⚠ `master/0010` created near-duplicate DivisionResult rows on prod.** The seed matches on
  `name_bn`, and prod's existing `দ্বিতীয় বিভাগ` / `৩য় বিভাগ` use **different byte sequences** for the
  same-looking Bangla (they do not match a `LIKE` on the normal form), so get_or_create added its
  own copies: ids 4 (`দ্বিতীয় বিভাগ`/2nd Division) and 5 (`তৃতীয় বিভাগ`/3rd Division) now sit beside
  ids 2 and 3. Nothing references any of them (`used_by=0` for all six), so it is cosmetic — the
  Division dropdown just lists two visually identical options. **Prod already had division rows, so
  the education Result bug there was purely the CSS `display=''` bug, not missing master data.**
  Same family as the known duplicate `কৃষি মন্ত্রণালয়`. Any future bn-keyed seeder should normalise
  or match on `name_en` too.

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
