# Accompanying Officers — PRP employee sync (Phase 23) ✅ IMPLEMENTED

> Built and verified 2026-08-22 against the live API and the local Docker
> stack. Deltas from the original plan are marked **[shipped]** below.

**Problem.** `/travel/create/` → *Accompanying Officers* is a free-text formset
(ID / Name / Designation typed by hand). PRP already publishes the Secretariat
employee roster, so officers should be **picked from a synced list**, not typed.

**Rule (locked with the user, 2026-08-22).** Only **Class-1, Active** employees
**that have both a designation and an office** are kept. An officer already saved
on a tour is kept forever; once he leaves that list he can no longer be searched
or added to any *new* tour.

---

## 1. What the live API actually returns

`GET {BASE}/api/secure/external?action=employeeInformations`
(token auth identical to `import_mp_api`: POST `…?action=token` → Bearer).
Probed 2026-08-22 with the existing `PRP_API_USER` / `PRP_API_PASS`:

| | |
|---|---|
| Records in one call | **3,839** (~2 MB, no paging) |
| `class` | 5:1208 · 3:1003 · 4:600 · **1:463** · 2:314 · 0:251 |
| `status` | Active 2075 / Inactive 1764 |
| class 1 + Active | 293 |
| …of those, **no designation AND no `officeDetails`** | 66 (the *same* 66 records) |
| **KEEP-SET (class 1 + Active + designation + office)** | **227** |

The 227 are clean: **0** blank `nameBn`/`nameEn`/`designation*`/`mobile`,
**0** duplicate `prpId`, and the live test account
`110100055 — Finance Admin Test` falls outside it automatically.
(One duplicate `prpId` — `450600035` — exists in the full payload but is
class-4 Inactive; the upsert still guards against it.)

**`officeDetails` is partial** — only `officeId`/`officeName*` is always present:
`wing*` missing for 22 of 227 · `branch*` for 28 · `section*` for 65.
So every office column is nullable and the wing filter needs an "other" bucket.
Wings present: B&IT 43 · Legislative Support 38 · Administrative Support 34 ·
Committee Support 26 · F&PR 24 · IPA&S 24 · Human Resource 16 · (no wing) 22.

`prpId` is a 9-char string. Fields available per record: `prpId, nameBn, nameEn,
designationBn, designationEn, mobile, telephone, gender, status, class, photo,
officeDetails{wing,branch,section,office × Id/NameBn/NameEn}`.

**Photos are not stored** (user decision) — the roster and picker are text-only.

**[shipped]** First live sync: 3,839 records in → **227 kept**, skipped
`inactive` 173 · `incomplete` 63 · `not_class_1` 3,376. (Skip counts differ
slightly from the table above because the classifier tests class → status →
completeness in order, so someone both Inactive *and* incomplete counts once,
as `inactive`.)

---

## 2. New app `apps/officer/`

Kept out of `master/` (that is admin-CRUD with the grouped-manager UI) and out of
`travel/` (committee support staff / PA-PS may reuse the roster later).

```python
class OfficerQuerySet(models.QuerySet):
    def selectable(self):            # THE definition of "can be added to a tour"
        return self.filter(is_active=True)

class Officer(models.Model):
    prp_id             = CharField(max_length=20, unique=True, db_index=True)
    name_bn, name_en   = CharField(max_length=200)
    designation_bn/_en = CharField(max_length=200)
    officer_class      = PositiveSmallIntegerField(default=1)
    prp_status         = CharField(max_length=20)      # last-seen PRP status
    mobile, telephone  = CharField(max_length=30, blank=True)
    gender             = CharField(max_length=20, blank=True)
    wing_id/branch_id/section_id/office_id             = IntegerField(null=True, blank=True)
    wing_bn/_en, branch_bn/_en, section_bn/_en, office_bn/_en = CharField(200, blank=True)
    is_active          = BooleanField(default=True)    # available for NEW selection
    first_synced_at    = DateTimeField(auto_now_add=True)
    last_synced_at     = DateTimeField()
    deactivated_at     = DateTimeField(null=True, blank=True)
    deactivated_reason = CharField(blank=True)   # inactive | class_changed | incomplete | absent
```

`deactivated_reason` tells the operator *why* someone dropped off the list
(went Inactive · lost class 1 · PRP cleared his designation/office · vanished
from the payload) instead of leaving it a mystery.

---

## 3. `ForeignTourOfficer` — history is frozen (`travel/0004`)

```python
officer     = FK(Officer, null=True, blank=True, on_delete=PROTECT,
                 related_name='tour_assignments')
is_external = BooleanField(default=False)      # typed by hand, not from PRP
# snapshot, written at save time — what the GO actually said:
officer_id  → RENAMED prp_id        (see below)
name        → RENAMED name_bn        + NEW name_en
designation → RENAMED designation_bn + NEW designation_en
```

* The **snapshot is the display source**, so a past GO renders exactly as
  recorded even after the officer's designation changes or he leaves.
* The rename also fixes an existing violation of CRITICAL RULE #2 (bilingual
  pair on every user-visible field). `tour_list`'s officer search
  (`officers__name__icontains`) is updated to hit both columns.
* `on_delete=PROTECT` + never-delete-on-sync means a saved row can never be
  orphaned.
* **[shipped]** `officer_id` had to be renamed to `prp_id`: an FK named
  `officer` claims the `officer_id` attribute on the model, so the two would
  have collided. `prp_id` is the clearer name anyway.
* Legacy rows keep their text with a null FK; the first sync links any whose
  `prp_id` matches a roster `prp_id` (the one existing local row, `110100091`,
  matches a keep-set officer, so this path is exercised immediately).

---

## 4. Sync — `python manage.py sync_officers`

`apps/officer/management/commands/sync_officers.py`, flags
`--dry-run · --file PATH · --username/--password (env fallback) · --limit · --force`.

1. Token → `employeeInformations`.
2. Keep `class == 1 and status == 'Active' and designation and officeDetails`.
3. **Upsert by `prp_id`** — refresh every field, `is_active=True`,
   `last_synced_at=now`, clear `deactivated_*` (reactivation is automatic).
4. **Retire**: any `Officer` in our DB *not* in the keep-set →
   `is_active=False`, `deactivated_at=now`, `deactivated_reason=…`.
   **Never deleted.** Saved tour rows are untouched.
5. Link unlinked `ForeignTourOfficer.officer_id` → `prp_id`.
6. Summary: created / updated / unchanged / reactivated / retired (by reason) /
   skipped (not-class-1 · inactive · incomplete · duplicate · blank-name).

**Wipe-guard.** If the keep-set is empty, or smaller than 50 % of the currently
active roster, abort with an error instead of retiring everyone — a bad API
response must not empty the picker. `--force` overrides.

**Refactor**: `get_token()` + `fetch_json()` move out of `import_mp_api.py` into
`utils/prp_api.py`; both commands use them (no behaviour change).

---

## 5. Roster page — `/officer/` under the বিদেশ ভ্রমণ menu

Read-only list: search by **name (bn/en) / PRP ID / designation**, wing filter
(+ "other"), status filter **active / retired / all**, 50 per page, last-sync
timestamp, and a **Sync** button. Retired rows show their reason and stay
visible — that is where you check "why can't I find him any more".

* `apps/officer/views.py` → `officer_list`, `officer_sync_run`
  (POST, gated by the `_can_run_sync` pattern from `apps/mp/views.py`:
  superadmin, or `can_edit` on this submenu; runs `call_command` and reports
  the counts through `messages`).
* `config/urls.py` gains `path('officer/', include('apps.officer.urls', namespace='officer'))`.
* Menu: `fixtures/initial/officer_menu.json` (submenu pk 802 under menu 8,
  `officer:officer_list`, ordering 30) **+** migration
  `accounts/0006_officer_submenu` so the live DB gets it without a fixture load.

---

## 6. Tour create/edit form

**Officer formset → officer picker.** Same markup as `{% mp_picker %}`, so
`static/js/mp_picker.js` + `mp_picker.css` are reused **unchanged** (that JS is
generic — it keys off `.mp-picker` and `data-party`/`data-type`).

* `apps/officer/templatetags/officer_picker_tags.py` → `{% officer_picker form.officers %}`
  → `templates/partials/_officer_picker.html`.
* Search string = name bn+en · PRP ID · designation bn+en · office · wing.
* **[shipped] Type-to-search, not a list.** Two rounds of user feedback:
  (1) the wing chips were removed — 22 of the 227 have no wing, so the label fell
  back to the office name and the row rendered 25+ buttons; (2) the standing
  scrolling list was removed — with 227 officers the user wants to type and pick.
  Final: search box → suggestion dropdown (max 12, ↑/↓/Enter/Esc) → chips.
  The roster still ships as hidden checkboxes so the POSTed field and its
  validation are unchanged; only visibility is JS-driven. This is the one place
  the plan's "no new JS/CSS" claim no longer holds — `static/css/officer_picker.css`
  and `static/js/officer_picker.js` were added (prefix `.of-`), leaving the MP
  picker's `.mp-picker` assets untouched.
* Queryset = `Officer.objects.selectable()` **plus any officer already attached
  to this tour** (`Q(is_active=True) | Q(pk__in=attached)`), so editing an old
  tour can never silently drop a retired officer. Retired ones render
  pre-checked with a **নিষ্ক্রিয়** badge. Uncheck + save removes it for good —
  and it cannot be re-added, which is exactly the requested behaviour.
* Save reconciles add/drop like MP participants and copies the bilingual
  snapshot from `Officer`.
* Empty-state (before the first sync): a note + link to the roster's Sync button.

**External officers** (user decision: keep an escape hatch for people outside
the Secretariat — a ministry or embassy officer on the same GO). A collapsed
*"PRP তালিকায় নেই এমন কর্মকর্তা"* accordion under the picker keeps the existing
`OfficerFormSet`, restricted to `tour.officers.filter(officer__isnull=True)` and
saving with `is_external=True`. The two sets are **disjoint** (FK set vs FK
null), so picker-reconcile and formset-save never fight over the same row.
`remarks_bn/en` stay on the external form only (0 rows use them today).

---

## 7. Surfaces to update

`travel/tour_detail.html` + `travel/print/tour_detail.html` (bilingual snapshot,
wing/designation, external badge) · `travel/tour_list.html` search (both name
columns) · `apps/travel/views.py` `_tour_form` + `tour_list` · the now-unused
`officer_add`/`officer_remove` endpoints are removed rather than left dangling.
Reports do not reference officers, so nothing there changes.

## 8. Verification — all passed (2026-08-22, running Docker stack)

| Check | Result |
|---|---|
| `migrate` + `check` | clean (accounts 0006, officer 0001, travel 0004) |
| `sync_officers --dry-run` → real sync | 227 created, legacy tour row auto-linked |
| Re-run sync (idempotency) | `created 0 · unchanged 227` — no duplicates |
| Roster page: search / wing / status filters | 200; PRP-ID + name search hit |
| Tour form picker | hidden store of **227** checkboxes, **0** visible list rows, search + suggestion box present; MP picker untouched |
| Retired officer attached to a tour | on the edit page: present, `checked`, `data-retired` → renders as an amber chip |
| Same officer on a NEW tour | store holds 226, he is absent |
| `officer_picker.css` / `.js` via nginx | both HTTP 200 after `collectstatic` |
| Create tour: 2 roster + 1 external officer | 3 rows — 2 linked & snapshotted, 1 `is_external` |
| **Retirement simulation** | still on the saved tour with a নিষ্ক্রিয় badge; **absent** from a new tour's picker; absent from `status=active`, present in `status=all` |
| Edit: uncheck the retired officer | removed; the external row survives untouched |
| Sync after retirement | reactivated 1 (he was back in the API); external row untouched |
| `ProtectedError` on deleting an attached officer | blocked as designed |
| Tour-list search by PRP ID / roster name / external name | all three hit |
| Wipe-guard: 50-of-227 payload, and 0-of-227 | both refused, roster left at 227 |
| Genuine single retirement (226-of-227 payload) | `retired [absent]: 1`, others untouched |
| Detail + print templates | show both officers, with External / Retired badges |
| Multi-line `{# #}` comment guard | none found |
