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
12. Soft delete on master data (is_active=False) to preserve FK integrity.
13. Foreign tour GO can cover multiple MPs (ForeignTourParticipant).
13b. Foreign travel has TWO sources, kept apart on purpose. **Official** travel
    runs through the GO process (`travel.ForeignTour`) and is **read-only on the
    MP profile** — a GO is never created from a profile. **Personal / pre-tenure**
    travel (`mp.PersonalForeignTravel`) is entered on the profile, has no GO and
    no parliament FK, and only `country` is required — purpose and dates are
    optional because a decades-old trip is worth recording half-remembered.
    Both appear in biodata section 18, labelled দাপ্তরিক / ব্যক্তিগত. Travel
    *reports* stay GO-only.
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
```

---

## GOTCHAS

Traps that cost real debugging time here. Each one looks correct and fails
silently — full context in `docs/phase-history.md`.

**Django / templates**
1. `{# … #}` comments are **SINGLE-LINE ONLY** — `django.template.base.tag_re` is
   compiled without `re.DOTALL`, so a `{#` … newline … `#}` block is not a comment
   and renders as **visible text on the page**. Use `{% comment %}…{% endcomment %}`
   for anything multi-line. Guard: no `{#` may be followed by a newline before its `#}`.
2. **Templates are cached by gunicorn** — production settings compile them once per
   worker, so a template edit on the bind-mounted stack is invisible until
   `docker compose restart web`. The Django test client (fresh process) will show
   the new markup while the browser still shows the old one.
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

**Frontend**
8. Never toggle visibility with `style.display = ''` when a CSS rule hides the
   element — clearing an inline style hands it straight back to `display:none`.
   Set an explicit value (`'block'`).
9. **Select2 fires jQuery events, not native DOM events.** An inline `onchange=`
   attribute still runs (jQuery's `.trigger()` invokes it), but htmx's native
   `change` listener never fires. Any htmx-on-change over a Select2 control needs a
   jQuery bridge that re-emits via `htmx.trigger(...)`.
10. Editor-authored HTML must not carry **Bootstrap component class names**.
    CKEditor wraps saved tables in `<figure class="table">`, and `.table > …` then
    paints a border on every row. `utils/html_sanitize.py` unwraps `figure` and
    strips the `table` class — keep that guard if you add another editor surface.
11. CKEditor 5 super-build needs **both** `removePlugins: PREMIUM` (bundled
    commercial plugins otherwise demand a licence key and the editor never mounts)
    and the `htmlSupport` allow-all block (otherwise inline column widths,
    `text-indent` and `font-size` are stripped and the letterhead collapses).

**Exports / Bangla**
12. CSV: declare `charset=utf-8` and write the BOM **once** explicitly. Declaring
    `utf-8-sig` makes Django encode *every* `response.write()` with it, prepending a
    BOM to every row and corrupting the first column of every line.
13. DOCX Bengali runs need `w:cs` (and `w:szCs`) set, not just `w:ascii`/`w:hAnsi` —
    Bengali is a *complex script*, so without `w:cs` Word falls back to Times New
    Roman and renders boxes. See `utils/html_to_docx.py`.
14. `pypdf.extract_text()` renders Bangla as gibberish **even when the PDF is
    perfect** — SolaimanLipi embeds as a CID/Type0 subset whose ligature glyphs do
    not reverse-map. Verify a PDF by its `/Producer` + embedded font list, or by
    looking at the page. Never trust extracted text.
15. Keep the `body.noc-bn` `@page` box in sync between
    `templates/noc/print/noc_document.html` and `static/css/noc.css` — loosening
    either re-splits the Bangla letter onto a second page.

**Data / production**
16. **Bangla on prod is not byte-normalised.** Visually identical strings can differ
    in code points, so any seeder or importer keyed on `name_bn` silently
    *duplicates* instead of matching. Normalise (`unicodedata.normalize('NFC', …)`)
    or match on `name_en` as well.
17. The PRP API serves **only its leaf certificate**, omitting the intermediate.
    Windows hides this via AIA fetch; the Linux container fails with
    `CERTIFICATE_VERIFY_FAILED`. Use `prp_api.ssl_context()` +
    `utils/certs/prp_chain.pem` — it *adds* trust. Do **NOT** "simplify" to
    `verify=False`.
18. `docker compose` traps: `docker compose images web` exits 1 right after a
    rebuild (making a successful build look failed); `docker compose exec` does
    **not** inherit the entrypoint's `DJANGO_SETTINGS_MODULE`, so pass
    `-e DJANGO_SETTINGS_MODULE=config.settings.production`; `static_collected` is a
    named **volume**, so `ls` it inside the container, not on the host.

**Deliberate choices — do not "restore" these**
19. The officer roster page `/officer/` is ordered by **PRP ID ascending** (not
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
