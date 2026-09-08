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
14. Soft delete on master data (is_active=False) to preserve FK integrity.
15. Foreign tour GO can cover multiple MPs (ForeignTourParticipant).
13b. Foreign travel has TWO sources, kept apart on purpose. **Official** travel
    runs through the GO process (`travel.ForeignTour`) and is **read-only on the
    MP profile** — a GO is never created from a profile. **Personal / pre-tenure**
    travel (`mp.PersonalForeignTravel`) is entered on the profile, has no GO and
    no parliament FK, and only `country` is required — purpose and dates are
    optional because a decades-old trip is worth recording half-remembered.
    Both appear in biodata section 18, labelled দাপ্তরিক / ব্যক্তিগত. Travel
    *reports* stay GO-only.
16. Office address = সংসদ অফিস ONLY. OneToOne with MP.
17. Superadmin bypasses all role permission checks.
18. Report export requires can_export=True in RolePermission.
19b. An MP can hold THREE unrelated kinds of office at once and they are stored
    separately on purpose: `MinistryAssignment` = what they run,
    `CommitteeAssignment.position` = what they chair, `SpecialPositionHistory`
    = where they sit in the House (Speaker, Deputy Speaker, Chief Whip, Whip,
    Leader of the House / Opposition). Offices flagged
    `SpecialRoleType.is_unique_per_parliament` allow only ONE *sitting* holder
    per parliament — enforced in `SpecialPositionHistory.clean()`, which
    deliberately ignores inactive rows so history survives. Ending a term
    un-ticks `is_active`; nothing is deleted. Entry runs through
    `parliament:position_*` from BOTH the module and the MP profile tab — there
    is no second write path, and adding one would bypass the guard.

19. Technocrat ministers = cabinet members with NO seat. Stored as MP rows with
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
| 15 | UX improvements round (see `docs/phase-history.md`) | ✅ |
| 16 | PRP API import + conflict-safe sync (see `docs/phase-history.md`) | ✅ |
| 17 | Observation fixes — prioritized task list (see `docs/phase-history.md`) | ✅ |
| 18 | Education master-data pools (school/university groups) + self-educated tick | ✅ |
| 19 | Education master data → single-page manager (tab-rail + inline HTMX CRUD) | ✅ |
| 20 | MP detail edit tabs → two-column grouped composition (General, Election, Address) + dashboard tiny-bar click fix | ✅ |
| 21 | Master data → grouped single-page managers (Geography, Personal, Professional, Travel, Language, Ministry, Committee) mirroring Education | ✅ |
| 22 | Technocrat ministers — cabinet members with no seat (see `docs/phase-history.md`) | ✅ |
| 23 | Accompanying Officers → PRP employee sync (roster + picker, see `docs/phase-history.md`) | ✅ |
| 24 | Field-feedback fixes — spouse/child mobile, education Result cascade, live MP search | ✅ |
| 25 | NOC generation — bilingual editable documents (CKEditor) + PDF/Word/print, tour passport capture | ✅ |
| 26 | Field-feedback round 2 — user designation/photo, address "same as" ticks, DD/MM/YYYY dates, education board-vs-university pools, bank branch + biodata bilingual fixes (see `docs/phase-history.md`) | ✅ |
| 27 | Personal / pre-tenure foreign travel on the MP profile — travel tab split into official (GO, read-only) + personal (full CRUD) | ✅ |
| 28 | Master-data completeness — bilingual name columns, Class Results master table, year-only travel | ✅ |
| 29 | Field-feedback round 3 — COVID dose form bilingual + vaccine master pool seeded/discoverable, Post Office field on MP address, master-search keystroke loss, Bangla-numeral search | ✅ |
| 30 | MP list completeness bar → weighted 100-point score (27 scored fields, 4/2 points each) + missing-field tooltip | ✅ |
| 31 | Education page → repeatable degrees (double graduation / masters / PhD / diploma) via per-row prefixes + pk binding (see `docs/phase-history.md`) | ✅ |
| 32 | Two divisions told apart — dashboard chart + custom-report filters/columns get a constituency vs home-district basis, `Constituency.district` backfill | ✅ |
| 33 | Parliamentary positions (Speaker / Deputy Speaker / Chief Whip / Whip / Leader of the House …) — seeded master, single-holder guard, `/parliament/positions/` module, holders report + report columns | ✅ |
| 34 | Custom report — ALL chip instead of 348, pagination removed (whole report on one page), print fixed, PDF made 5–10× faster (column widths, parallel layout, result cache), static-asset cache fixed | ✅ |

⬜ Not started | 🔄 In progress | ✅ Done

## COMMANDS

```bash
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

# NOC documents (Phase 25)
python manage.py loaddata fixtures/initial/noc_menu.json

# Parliamentary positions (Phase 33) — menu for /parliament/positions/ and the
# holders report. The offices themselves are seeded by master/0014.
python manage.py loaddata fixtures/initial/position_menu.json

# Constituency → District backfill (Phase 32) — the constituency-basis division
# chart and district_wise?basis=constituency both need this FK populated.
python manage.py backfill_constituency_district --dry-run   # print matches + unresolved
python manage.py backfill_constituency_district             # fill empty rows only
```

---

## GOTCHAS

Traps that cost real debugging time here. Each one looks correct and fails
silently — full context in `docs/phase-history.md`.

**Django / templates**
1. **EVERY template construct is SINGLE-LINE ONLY** — `django.template.base.tag_re`
   (`({%.*?%}|{{.*?}}|{#.*?#})`) is compiled without `re.DOTALL`, so `.` never
   matches a newline and an opener whose closer sits on the next line is not
   recognised as a tag at all. Django raises nothing; the construct renders as
   **visible literal text on the page**.
   - This bites `{% … %}` and `{{ … }}` exactly as hard as `{# … #}`. Wrapping a
     long `{% ui "বাংলা" "English" %}` onto two lines — the obvious thing to do
     with a bilingual label — prints the tag source to the user. Six of those
     shipped in Phase 33 before a user reported it.
   - Use `{% comment %}…{% endcomment %}` for multi-line comments; keep every
     other tag on one line however long it gets.
   - Guard: `python utils/check_template_tags.py` (exit 1 + file:line on any
     hit). Run it after touching templates.
2. **gunicorn workers cache templates AND Python code** — production settings
   compile templates once per worker, and every module is imported once at boot,
   so a template *or* `.py` edit on the bind-mounted stack is invisible until
   `docker compose restart web`.
   - Symptom: the Django test client (a fresh process) returns **200** while the
     browser returns the old markup, or **500**.
   - Worst case: running `migrate` without restarting leaves the workers holding
     **pre-migration model code against the post-migration schema** — every page
     touching the changed table 500s, with no traceback in the log (DEBUG=False
     sends `django.request` to `mail_admins`, not stdout). This bit `/mp/<pk>/`
     locally after `mp/0013` turned `class_result` into an FK.
   - So: **after any migrate on a bind-mounted stack, restart web.** On the
     server the entrypoint does migrate→collectstatic→gunicorn in one boot, so a
     deploy is never exposed to this — only local dev is.
3. Never read pre-edit state off a ModelForm's instance **after** `is_valid()` —
   `construct_instance()` has already written the posted values onto it, so a
   `new != old` guard compares a value with itself and is always False. Capture the
   old state *before* binding the form.
4. `annotate()` sets `group_by`, which hides `Meta.ordering` from the paginator
   (`UnorderedObjectListWarning`; pages can repeat or skip rows). Add an explicit
   `.order_by(...)` on any annotated queryset you paginate.
5. **Date widgets must be pinned to ISO.** Django renders a bound date with the
   *active locale's first* `DATE_INPUT_FORMATS` entry — `%d/%m/%Y` under `bn` —
   and `<input type="date">` silently rejects any non-ISO `value`, so in Bangla
   mode every saved date renders as an **empty box**. `utils/form_dates.py`
   (`normalize_date_fields`, called from all ten `_BootstrapMixin.__init__`s)
   pins `widget.format='%Y-%m-%d'`. Set `widget.input_type`, never
   `attrs['type']` — a `type` in attrs is rendered *in addition to* the widget's
   own, giving a duplicate attribute.
6. `makemigrations` turns a bilingual field split (`x` → `x_bn` + `x_en`) into
   **RemoveField + AddField, dropping every stored value**. Hand-write it with
   `RenameField` — see `mp/0011_mp_nationality_bilingual`.
7. `get_..._display()` returns only the Bangla half of a `choices` tuple. For a
   bilingual label, add `<field>_bn` / `<field>_en` **properties** and use the
   existing `{{ obj|tr:"<field>" }}` filter (`MP.MEMBER_TYPE_LABELS`).
8. **`|tr:` is for a cell that follows the UI language — never for a column whose
   header names a language.** A "বাংলা নাম | English Name" **pair** must render
   `{{ obj.name_bn }}` / `{{ obj.name_en }}` literally; `{{ obj|tr:"name" }}` in
   the first column makes *both* read English in English mode. This was wrong in
   all three master-data list templates plus parliament / constituency / menu /
   role. A single name column headed just "Name" is the opposite case — `tr` is
   correct there (see `user_list.html`).

9. A **fixed section per category is a display choice, not a data rule.** The
   education page kept `existing[lt] = edu` for the *first* row per level, so an
   MP's second graduation / masters / PhD was invisible and unreachable in the
   editor while rendering fine in every biodata and report (they all iterate
   `mp.educations.all()`). Repeated rows bind **by posted pk, not by position** —
   index binding re-points every form after a removed row at the wrong record.
   Build the pk map from that MP's rows only, so a forged id falls through to a
   new row instead of another MP's data.
10. `all(f.is_valid() for f in forms)` **short-circuits** — forms after the first
    invalid one are never cleaned and render no errors. Materialise the list.

**Frontend**
11. Never toggle visibility with `style.display = ''` when a CSS rule hides the
    element — clearing an inline style hands it straight back to `display:none`.
    Set an explicit value (`'block'`).
12. **Select2 fires jQuery events, not native DOM events.** An inline `onchange=`
    attribute still runs (jQuery's `.trigger()` invokes it), but htmx's native
    `change` listener never fires. Any htmx-on-change over a Select2 control needs a
    jQuery bridge that re-emits via `htmx.trigger(...)`.
13. **Never let a live-search request swap the search box itself.** htmx replaces
    the target node, so an `hx-target` that contains the focused `input` destroys
    it mid-typing: the caret is lost and every character typed while the request
    was in flight is dropped — the box "misses keystrokes". Search triggers must
    swap only the results region (`hx-target="#…-rows"` + `hx-select="#…-rows"`,
    row count via `hx-select-oob`, plus `hx-sync="this:replace"`); full-panel
    swaps are fine for add/edit/toggle, which are clicks, not typing. Was wrong
    in both master-data managers (`group_panel.html`, `edu_panel.html`).
14. Numbers are **stored ASCII, displayed Bangla**, so an operator reads ১৫২ off
    the screen and types it back into a search box that only matches `152`. Every
    search over an MP ID / memo / GO number goes through `utils/bn_digits.search_q`,
    which ORs each field against both digit spellings.
15. Editor-authored HTML must not carry **Bootstrap component class names**.
    CKEditor wraps saved tables in `<figure class="table">`, and `.table > …` then
    paints a border on every row. `utils/html_sanitize.py` unwraps `figure` and
    strips the `table` class — keep that guard if you add another editor surface.
16. CKEditor 5 super-build needs **both** `removePlugins: PREMIUM` (bundled
    commercial plugins otherwise demand a licence key and the editor never mounts)
    and the `htmlSupport` allow-all block (otherwise inline column widths,
    `text-indent` and `font-size` are stripped and the letterhead collapses).

**Exports / Bangla**
17. CSV: declare `charset=utf-8` and write the BOM **once** explicitly. Declaring
    `utf-8-sig` makes Django encode *every* `response.write()` with it, prepending a
    BOM to every row and corrupting the first column of every line.
18. DOCX Bengali runs need `w:cs` (and `w:szCs`) set, not just `w:ascii`/`w:hAnsi` —
    Bengali is a *complex script*, so without `w:cs` Word falls back to Times New
    Roman and renders boxes. See `utils/html_to_docx.py`.
19. `pypdf.extract_text()` renders Bangla as gibberish **even when the PDF is
    perfect** — SolaimanLipi embeds as a CID/Type0 subset whose ligature glyphs do
    not reverse-map. Verify a PDF by its `/Producer` + embedded font list, or by
    looking at the page. Never trust extracted text.
20. Keep the `body.noc-bn` `@page` box in sync between
    `templates/noc/print/noc_document.html` and `static/css/noc.css` — loosening
    either re-splits the Bangla letter onto a second page.

**Data / production**
21. **Bangla on prod is not byte-normalised.** Visually identical strings can differ
    in code points, so any seeder or importer keyed on `name_bn` silently
    *duplicates* instead of matching. Normalise (`unicodedata.normalize('NFC', …)`)
    or match on `name_en` as well.
22. The PRP API serves **only its leaf certificate**, omitting the intermediate.
    Windows hides this via AIA fetch; the Linux container fails with
    `CERTIFICATE_VERIFY_FAILED`. Use `prp_api.ssl_context()` +
    `utils/certs/prp_chain.pem` — it *adds* trust. Do **NOT** "simplify" to
    `verify=False`.
23. `docker compose` traps: `docker compose images web` exits 1 right after a
    rebuild (making a successful build look failed); `docker compose exec` does
    **not** inherit the entrypoint's `DJANGO_SETTINGS_MODULE`, so pass
    `-e DJANGO_SETTINGS_MODULE=config.settings.production`; `static_collected` is a
    named **volume**, so `ls` it inside the container, not on the host.

23b. **A GET filter form has a request-line budget.** Ticking all 348 MPs in a
    report picker put every `mp_id=…` pair on the URL — ~5.8 KB — and gunicorn
    rejected it before Django saw anything: a bare `Bad Request / Request Line
    is too large (5798 > 4094)`, no traceback, no log line in the app. Two
    guards now: the MP picker collapses a *complete* selection to the single
    value `__all__` (`static/js/filter_all_option.js` → `ALL_SENTINEL` /
    `_multi()` in `apps/reports/views.py`, re-expanded when the form is
    re-rendered so the chips still show), and gunicorn runs with
    `--limit-request-line 8190` (its maximum) with nginx's
    `large_client_header_buffers` kept wider. The sentinel is opt-in per
    `<select>` via `data-all-sentinel` and is **only** safe on the MP picker:
    the master-data filters cross a relation, so "all 64 districts" still drops
    every MP without a constituency, which "no filter" does not.
    Also: pagination links must not rebuild the query with
    `{% for k,v in request.GET.items %}` — a QueryDict's `.items()` yields only
    the LAST value of a repeated key, so paging a report filtered on several MPs
    silently dropped all but one. Use `{% qs_page n %}` (`report_tags`).

23c. **Report generation is the heavy, shared workload — treat it as one.**
    A 348-row x 24-column custom report cost 33 s of PDF on prod, and every
    surface (screen / print / PDF / Excel) recomputed the same cells. What was
    wrong and what fixed it, in order of size:
    - **Column widths.** `table-layout: fixed` with no widths splits an A4
      landscape page into 24 equal 11 mm columns, so a name breaks into
      "Muham / mad / Nawsh / ad" and **two rows fill a page — 97 pages**.
      `COL_WIDTH` + a `<colgroup>` gives 23 pages, and WeasyPrint's cost tracks
      the number of *lines*, so the layout fix is also the biggest speed fix.
    - **`overflow-wrap: anywhere`** (set on th/td in `base_print.html`) costs
      ~30% of layout time on a big Bangla table — every grapheme becomes a
      break candidate. The custom report overrides it with `break-word`.
    - **Inline `style=` per cell.** 8 700 one-off declaration blocks for
      WeasyPrint to parse. Class-based CSS instead; ~8% and a 5x smaller HTML.
    - **Parallel layout.** `render_report_pdf(split_key=...)` cuts the rows into
      chunks, lays each out in a forked process and merges with pypdf. Capped at
      `cpu // 2` and skipped when `getloadavg()` says the box is busy — under
      concurrency, serial rendering keeps total throughput higher. Workers must
      never touch the ORM: they share the parent's DB socket.
    - **Result cache.** `caches['reports']` (file-based, so it is shared across
      gunicorn workers — LocMemCache is per process) keyed on filters + columns
      + language + `AuditLog` max id. An edit invalidates instantly; master-data
      renames are not audited, so a label can be stale for the 15-minute TTL.
    - **Prefetch only what the chosen columns read** (`COL_PREFETCH`): a
      six-column report went from 27 queries to 19.
    Never paginate this report: it is read, printed and exported whole, and the
    old Print button printed only the visible page.

23d. **Static assets were served with `expires 30d` and no content hash** —
    Django 5.1 removed `STATICFILES_STORAGE`, which this project still set, so
    collectstatic silently stopped hashing filenames. A returning browser then
    kept a month-old copy of any edited CSS/JS and never revalidated: **a deploy
    was invisible until a hard refresh**. nginx now sends
    `Cache-Control: public, no-cache` for `/static/` (keep the copy, revalidate
    — a 304 on a LAN). Turning the manifest storage back on needs the vendored
    `ckeditor.js.map` to exist first, and a collectstatic failure stops the
    container booting (`entrypoint.sh` runs it under `set -e`).

**Two divisions — never one "Division"**
24. An MP has **two** divisions and they disagree (Dhaka: 70 seats vs 94 home
    districts on live data). The *seat* division is
    `ElectionInfo → constituency → district → division`; the *home* division is
    `home_district → division`. "MP of Dhaka Division" normally means the seat, so
    that is the default everywhere, but any chart, column or report that shows one
    must **say which** — the dashboard card has a basis toggle and a caption, the
    district-wise report has `?basis=home|constituency`, and the custom report
    builder has `division_basis` / `district_basis` plus a `con_division` /
    `con_district` column pair beside the home pair. `Constituency.district` is
    admin-entered and nullable: when it is empty the constituency basis silently
    collapses to a near-empty chart, so run
    `manage.py backfill_constituency_district` before trusting it. Reserved seats
    (301–350) can never appear on the constituency basis — they have no
    constituency by rule.

**Deliberate choices — do not "restore" these**
25. The officer roster page `/officer/` is ordered by **PRP ID ascending** (not
    `-is_active, name_bn`); the tour officer picker is **type-to-search only** — its
    wing filter chips and always-visible scrolling list were removed on user
    feedback, not lost.

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
| `docs/NOC for MP/` | NOC source scans — the English certificate and the Bangla forwarding letter are DIFFERENT documents |
| `docs/API.txt` | PRP endpoints (token / employeeInformations / offices) + a sample employee record |
| `docs/phase-history.md` | Phases 15–25 build log + production deploy log — why a thing is the way it is |
