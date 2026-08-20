# Technocrat Ministers — design & implementation plan

**Date:** 2026-08-20 · **Source:** `docs/technocrat.md` · **Phase:** 22

---

## Problem

The system holds 349 MPs (directly elected + women reserved). Bangladesh's
cabinet also contains **technocrat ministers** — appointed cabinet members who
are *not* Members of Parliament. They have:

- no constituency, no party, no election/oath/gazette date, no seat number
- **only** a ministry appointment (position + ministry + appointment date)

They are currently absent from the system, so the cabinet report and the
ministry module show an incomplete cabinet.

## Decision — reuse the `MP` model with a third `member_type`

`MP.member_type` gains `'technocrat'` alongside `'direct'` and `'reserved'`.
A technocrat is an `MP` row with **no `ElectionInfo` row at all** plus one
`MinistryAssignment` per ministry held.

### Why not a separate model

| | reuse `MP` (chosen) | new `Technocrat` model | `MinistryAssignment.mp` nullable |
|---|---|---|---|
| Ministry module, GO upload, cabinet report | unchanged | full duplicate | rework every `obj.mp.…` |
| Profile, photo, biodata PDF, audit log | free | rebuild | rebuild |
| Cost | ~12 mechanical exclusion filters | large | medium, nullable-FK churn |

`ElectionInfo.constituency` is already nullable and `ElectionInfo` itself is
optional (reserved seats rely on this), so "no constituency" needs **no schema
change**. `MinistryAssignment` already supports multiple rows per person, so a
technocrat holding two ministries needs no schema change either.

The one real cost — technocrats must not inflate MP counts — is contained by
routing every MP-population query through a single helper (below).

## Rule: "350 means 350"

`MP.objects.parliament_members()` (`apps/mp/models.py`) is the **only**
definition of "an actual member of parliament" = `.exclude(member_type='technocrat')`.
Every count/report/chart over the MP population uses it:

| File | Surface |
|---|---|
| `apps/accounts/views.py` `dashboard` | total / women / direct / with-photo tiles + party, division, gender, religion, times-elected charts |
| `apps/reports/views.py` `_mp_qs_base()` | all_mp, party, district/division, contact, family, qualification, women reports |
| `apps/reports/views.py` `report_index` | `total_mp`, `women_mp` stats |
| `apps/mp/views.py` `mp_list` | list defaults to MPs; technocrats reachable via the member-type filter |
| `apps/mp/views.py` | "MPs without photo" count |
| `apps/reports/views.py` custom report builder | MP universe |

Ministry / cabinet surfaces deliberately do **not** exclude them — that is the
whole point.

## MP ID convention

`mp_id` is manually entered and only uniqueness-validated. Assigned by the
Secretariat:

| mp_id | Name | Position | Ministries | Appointment |
|---|---|---|---|---|
| `013050101` | ড. খলিলুর রহমান / Dr. Khalilur Rahman | মন্ত্রী | পররাষ্ট্র | 2026-02-17 |
| `013050201` | মোঃ আমিনুল হক / Md. Aminul Haque | প্রতিমন্ত্রী | যুব ও ক্রীড়া | 2026-02-17 |
| `013050301` | মোহাম্মদ আমিন উর রশিদ / Mohammad Amin Ur Rashid | মন্ত্রী | মৎস্য ও প্রাণিসম্পদ **+** কৃষি | 2026-02-17 |

Amin Ur Rashid gets **two** `MinistryAssignment` rows sharing one appointment date.

## Scope decisions (confirmed with the user, 2026-08-20)

1. **PRP sync touches MPs only.** `import_mp_api` must never create, update or
   flag a technocrat — technocrats have no `prpId`. Enforced by an explicit
   exclude on the roster queries, not just by id-matching luck.
2. **MP picker** — technocrats are selectable for **foreign travel** and
   **institution** assignments (a technocrat minister can travel on a GO and can
   be nominated to an institution), and **not** for **standing committees**
   (committee membership requires being an MP).
3. **Biodata PDF** stays available for technocrats; election/constituency rows
   simply render empty because there is no `ElectionInfo`.

## Work items

1. **Model** — third `member_type` choice + `MPQuerySet.parliament_members()`;
   choices-only migration.
2. **Exclusions** — apply the helper at the 7 surfaces in the table above.
3. **Label fixes** — three places binary-branch `direct ? … : 'সংরক্ষিত (মহিলা)'`
   and would mislabel a technocrat:
   `apps/reports/templatetags/report_tags.py`, `apps/reports/views.py`
   (custom-report formatter), `templates/mp/mp_list.html` (badge).
   All switch to `get_member_type_display()`.
4. **MP create** — third option in `templates/mp/mp_create.html`.
5. **MP detail** — hide tab ২ (নির্বাচন) and tab ১১ (কমিটি) for technocrats;
   tab ১০ (মন্ত্রণালয়) is their primary tab.
6. **Pickers** — `MPChoiceField`/`MPMultipleChoiceField` gain
   `include_technocrats` (default `True`); committee forms/views pass `False`.
7. **Dashboard** — "টেকনোক্র্যাট মন্ত্রী" tile.
8. **Ministry list + cabinet report** — *ধরন* (এমপি / টেকনোক্র্যাট) column and filter.
9. **Seed** — idempotent `seed_technocrats` management command; resolves
   `Ministry` / `MinisterType` by bn-then-en name and **reports unresolved values
   rather than creating masters silently** (same policy as `api_sync.py`).
   Supports `--dry-run`.

## Verification

Isolated SQLite build + Django test client (the Phase 21 route — no local
PostgreSQL): MP counts unchanged, cabinet report gains 4 assignment rows,
technocrat detail page renders without the election tab, committee picker
excludes technocrats while travel/institution include them, PRP sync ignores
them. Then SFTP sync + `docker compose up -d` + `migrate`.
