# ref-form-mapping.md — PDF Form ↔ System Field Mapping
# Source: MP-Form.pdf (Bangladesh Parliament Secretariat / BAIT Division)
#
# PURPOSE: Every data-entry screen must present fields in the SAME ORDER
# as the printed form so staff can transcribe without hunting.
# Deviations are marked ★ with reason.

---

## FORM SECTIONS — MASTER ORDER

| Form Section | Bangla Title | System Screen / Tab |
|---|---|---|
| 1 | সাধারণ তথ্য | MP Form → Tab 1: General |
| 2 | নির্বাচন সংক্রান্ত তথ্য | MP Form → Tab 2: Election |
| 3 | স্বামী/স্ত্রী সংক্রান্ত তথ্য | MP Form → Tab 3: Spouse |
| 4 | সন্তান/সন্তানদের তথ্য | MP Form → Tab 4: Children |
| 5 | শিক্ষাগত যোগ্যতা | MP Form → Tab 5: Education |
| 6 | যোগাযোগের ঠিকানা | MP Form → Tab 6: Address |
| 7 | বিদেশি ভাষায় দক্ষতা | MP Form → Tab 7: Languages |
| 8 | ব্যাংক হিসাব সংক্রান্ত তথ্য | MP Form → Tab 8: Bank |
| 9 | কোভিড-১৯ টিকা সংক্রান্ত তথ্য | MP Form → Tab 9: COVID |
| 10 | মন্ত্রণালয়ের দায়িত্ব (প্রযোজ্য ক্ষেত্রে) | Ministry Module (also Tab 10) |
| 11 | স্থায়ী কমিটির দায়িত্ব (প্রযোজ্য ক্ষেত্রে) | Committee Module (also Tab 11) |
| 12 | পূর্ববর্তী সংসদ ইতিহাস | MP Form → Tab 12: History |
| 13 | সংগঠন | MP Form → Tab 13: Organizations |
| 14 | পুরস্কার | MP Form → Tab 14: Awards |
| 15 | সমাজ সেবা | MP Form → Tab 15: Social Service |
| 16 | বিশেষ পদের দায়িত্ব | MP Form → Tab 16: Special Positions |
| 17 | পুস্তক ও প্রকাশনা | MP Form → Tab 17: Publications |
| 18 | বিদেশ ভ্রমণ/বৈদেশিক প্রশিক্ষণ | Travel Module (also Tab 18) |
| 19 | শখ | MP Form → Tab 19: Hobbies (part of General) |
| 20 | অন্যান্য | MP Form → Tab 20: Other Info (part of General) |

> Tabs 19 & 20 are single free-text fields — fold them into Tab 1 General at the bottom.

---

## SECTION 1 — সাধারণ তথ্য (General)

Field order exactly as form (left-to-right, top-to-bottom):

| # | Form Label (bn) | Form Label (en) | System Field | Notes |
|---|---|---|---|---|
| 1 | নাম (বাংলায়) | — | `mp.name_bn` | |
| 2 | নাম (ইংরেজি বড় অক্ষর) | — | `mp.name_en` | |
| 3 | পিতার নাম (বাংলায়) | — | `mp.father_name_bn` | |
| 4 | পিতার নাম (ইংরেজি বড় অক্ষর) | — | `mp.father_name_en` | |
| 5 | মাতার নাম (বাংলায়) | — | `mp.mother_name_bn` | |
| 6 | মাতার নাম (ইংরেজি বড় অক্ষর) | — | `mp.mother_name_en` | |
| 7L | জন্ম তারিখ | Date of Birth | `mp.dob` | Same row |
| 7R | জাতীয় পরিচয়পত্র নং | NID | `mp.nid` | Same row |
| 8L | জন্মস্থান (জেলা) | Birth District | `mp.birth_district` FK | Same row |
| 8R | লিঙ্গ | Gender | `mp.gender` FK | Same row; choices: পুরুষ/মহিলা/অন্যান্য |
| 9L | নিজ জেলা | Home District | `mp.home_district` FK | Same row |
| 9R | বৈবাহিক অবস্থা | Marital Status | `mp.marital_status` FK | Same row |
| 10L | জাতীয়তা | Nationality | `mp.nationality` | Same row; default: Bangladeshi |
| 10R | ধর্ম | Religion | `mp.religion` FK | Same row |
| 11L | রক্তের গ্রুপ | Blood Group | `mp.blood_group` FK | Same row |
| 11R | পেশা (বর্তমান) | Current Profession | `mp.professions_current` M2M | Same row ★ multi-select |
| 12L | পেশা (পূর্বের) | Previous Profession | `mp.professions_previous` M2M | Same row ★ multi-select |
| 12R | টিআইএন | TIN | `mp.tin` | Same row |
| — | ★ পেশাদার যোগ্যতা | Professional Qual. | `mp.professional_qualifications` M2M | ★ NOT in form. Place after row 12. Doctor/Engineer/Lawyer etc. Added for reporting. |
| 13 | পাসপোর্ট নং | Passport No. | `mp.passport_number` | Two-column block: Passport left, Freedom Fighter right |
| 13 | ইস্যুর তারিখ | Issue Date | `mp.passport_issue_date` | |
| 13 | ইস্যুর স্থান | Issue Place | `mp.passport_issue_place` | |
| 13 | মেয়াদোত্তীর্ণের তারিখ | Expiry Date | `mp.passport_expiry_date` | |
| 13R | মুক্তিযোদ্ধা | Freedom Fighter | `mp.is_freedom_fighter` bool | Checkbox |
| 13R | মুক্তিযোদ্ধার সন্তান | FF Child | `mp.is_ff_child` bool | Checkbox |
| 13R | মুক্তিযোদ্ধার নাতি-নাতনি | FF Grandchild | `mp.is_ff_grandchild` bool | Checkbox |
| — | শখ | Hobbies | `mp.hobbies_bn` / `mp.hobbies_en` | Form Section 19 — place at bottom of Tab 1 |
| — | অন্যান্য | Other Info | `mp.other_info_bn` / `mp.other_info_en` | Form Section 20 — place at bottom of Tab 1 |

**UI layout rule for Section 1:** Use 2-column grid for rows 7–13 to match the form's paired layout.

---

## SECTION 2 — নির্বাচন সংক্রান্ত তথ্য (Election)

| # | Form Label | System Field | Notes |
|---|---|---|---|
| 1L | নির্বাচনী এলাকার নাম ও নম্বর | `election.constituency` FK | |
| 1R | সংসদ নম্বর | `election.parliament` FK | Pre-filled: 13th |
| 2L | নির্বাচনের তারিখ | `election.election_date` | |
| 2R | শপথের তারিখ | `election.oath_date` | |
| 3L | গেজেটের তারিখ | `election.gazette_date` | |
| 3R | কতবার নির্বাচিত | `election.times_elected` | |
| 4L | দলগত পরিচয় | `election.party` FK | |
| 4R | সংসদ সদস্যের ধরন | `mp.member_type` | choices: সরাসরি / সংরক্ষিত |
| ★ | মনোনয়নের তারিখ | `election.nomination_date` | ★ System addition; not in form |
| ★ | GO নম্বর / GO তারিখ | `election.go_number`, `election.go_date` | ★ System addition; not in form |

---

## SECTION 3 — স্বামী/স্ত্রী (Spouse)

| # | Form Label | System Field | Notes |
|---|---|---|---|
| 1L | নাম (বাংলায়) | `spouse.name_bn` | |
| 1R | নাম (ইংরেজি বড় অক্ষর) | `spouse.name_en` | |
| 2L | জন্ম তারিখ | `spouse.dob` | |
| 2R | জাতীয় পরিচয়পত্র নং | `spouse.nid` | |
| 3L | বিবাহের তারিখ | `spouse.marriage_date` | |
| 3R | টিআইএন | `spouse.tin` | |
| 4L | পেশা | `spouse.profession` FK | |
| 4M | নিজ জেলা | `spouse.home_district` FK | |
| 4R | লিঙ্গ | `spouse.gender` FK | |
| 5 | চাকরি হলে প্রতিষ্ঠান ও পদবী | `spouse.employer_details` | ★ Single text field. Add to model. |

> ★ Add `employer_details_bn` / `employer_details_en` CharField(blank=True) to Spouse model.

---

## SECTION 4 — সন্তান (Children)

For each child (up to 4 in form, system allows unlimited with pagination):

| # | Form Label | System Field | Notes |
|---|---|---|---|
| 1L | নাম (বাংলায়) | `child.name_bn` | |
| 1R | জন্ম তারিখ | `child.dob` | Same row |
| 2L | নাম (ইংরেজি বড় অক্ষর) | `child.name_en` | |
| 2R | পেশা | `child.profession` FK | Same row |
| 3L | জাতীয় পরিচয়পত্র/জন্ম নিবন্ধন নম্বর | `child.nid_or_birth_reg` | |
| 3R | লিঙ্গ | `child.gender` FK | |

**Display order in inline table:** serial | name_bn | name_en | dob | gender | profession | nid_or_birth_reg

---

## SECTION 5 — শিক্ষাগত যোগ্যতা (Education)

Form table columns (exact order):

| Form Column | System Field | Notes |
|---|---|---|
| পরীক্ষা/ডিগ্রির নাম | `education.degree_title` FK (DegreeName) | Maps to degree_title |
| বিষয় | `education.major_subject` FK (EducationSubject) | |
| পাসের সন | `education.passing_year` | |
| সিজিপিএ/বিভাগ | Dynamic result field | Shown based on result_type (HTMX) |
| শিক্ষাবোর্ড/বিশ্ববিদ্যালয় | `education.institution` FK | |

**Entry form field order (HTMX steps):**

```
1. শিক্ষার স্তর (Education Level)      ← extra: not in form column, needed for HTMX cascade
        ↓ HTMX
2. গ্রুপ (Group)                        ← extra: Science/Arts etc.
        ↓ HTMX
3. পরীক্ষা/ডিগ্রির নাম (Degree Title)  ← Form column 1
4. বিষয় (Subject)                      ← Form column 2
5. প্রতিষ্ঠান (Institution/Board)      ← Form column 5 (moved up for HTMX dependency)
6. পাসের সন (Passing Year)             ← Form column 3
7. ফলাফলের ধরন (Result Type)           ← extra: needed to show right result field
        ↓ HTMX
8. ফলাফল (Result)                      ← Form column 4 (dynamic)
```

**List/summary table column order** must match form exactly:
`ডিগ্রি | বিষয় | পাসের সন | ফলাফল | প্রতিষ্ঠান`

---

## SECTION 6 — যোগাযোগের ঠিকানা (Address)

Form has 3 address types. Field order per address:

| # | Form Label (bn) | Form Label (en) | System Field | Note |
|---|---|---|---|---|
| 1 | বাড়ি নং | House No. | `address_detail_bn` (free text) | Free text captures 1–4 |
| 2 | রাস্তা/ব্লক/গ্রাম | Road/Block/Village | `address_detail_bn` (free text) | |
| 3 | উপজেলা/থানা | Police Station/Upozila | `address.upazila` FK | Dropdown |
| 4 | ডাকঘর | Post Office | `address_detail_bn` (free text) | |
| 5 | পোস্টাল কোড | Postal Code | `address.postal_code` ★ | ★ ADD to Address model |
| 6 | জেলা | District | `address.district` FK | Dropdown (HTMX) |
| 7 | বিভাগ | Division | `address.division` FK | Dropdown |
| 8 | পৌরসভা/ইউনিয়ন | Pouroshova/Union | `address.pouroshova_union` ★ | ★ ADD to Address model |
| — | টেলিফোন | Telephone | `address.telephone` | Present address only |
| — | মোবাইল | Mobile | `address.mobile` | Present address only |
| — | বিকল্প মোবাইল | Alternative Mobile | `address.alt_mobile` | Present address only |
| — | হোয়াটসঅ্যাপ নম্বর | WhatsApp No. | `address.whatsapp` | Present address only |
| — | ই-মেইল | Email | `address.email` | Present address only |

**★ Model additions required:**
```python
class Address(Model):
    # ... existing fields ...
    postal_code          = CharField(max_length=20, blank=True)
    pouroshova_union_bn  = CharField(max_length=200, blank=True)
    pouroshova_union_en  = CharField(max_length=200, blank=True)
```

**UI field order in form:**
```
বিভাগ:            [Dropdown ▼]
জেলা:             [Dropdown ▼]   ← HTMX filtered
উপজেলা/থানা:     [Dropdown ▼]   ← HTMX filtered
পৌরসভা/ইউনিয়ন:  [free text   ]  ← NEW field
বাড়ি/রাস্তা/গ্রাম/ডাকঘর: [free text   ]
পোস্টাল কোড:    [            ]  ← NEW field
--- Contact (Present only) ---
টেলিফোন / মোবাইল / বিকল্প মোবাইল / হোয়াটসঅ্যাপ / ই-মেইল
```

> Contact fields (telephone, mobile, WhatsApp, email) appear ONLY on Present Address tab.

---

## SECTION 7 — বিদেশি ভাষায় দক্ষতা (Foreign Languages)

Form table: ক্রমিক | ভাষার নাম (2 columns only — no proficiency in form)

| Form Column | System Field | Note |
|---|---|---|
| ক্রমিক | `foreignlanguageskill.ordering` | Auto |
| ভাষার নাম | `foreignlanguageskill.language` FK | |
| ★ দক্ষতার মাত্রা | `foreignlanguageskill.proficiency` FK | ★ System addition — improves the form |

**Display table column order:** ক্রমিক | ভাষা | দক্ষতা

---

## SECTION 8 — ব্যাংক হিসাব (Bank Account)

Form table columns:

| Form Column | System Field |
|---|---|
| হিসাব নম্বর | `bankaccount.account_number` |
| ব্যাংকের নাম | `bankaccount.bank_name_bn` / `bank_name_en` |
| শাখার নাম ও রাউটিং নম্বর | `bankaccount.branch_name_bn`, `routing_number` |
| হিসাবের ধরন | `bankaccount.account_type` |

Form also has 3 specimen signature boxes — system does NOT store signatures digitally.
Note on screen: "নমুনা স্বাক্ষর ফর্মে সংযুক্ত করুন" (Attach specimen signatures to physical form).

---

## SECTION 9 — কোভিড-১৯ টিকা (COVID Vaccination)

Form fields:
- সার্টিফিকেট নম্বর (Certificate No.) — `covidvaccination.certificate_number` (one per MP, not per dose)

Form table per dose:

| Form Column | System Field |
|---|---|
| টিকার ডোজ | `covidvaccination.dose_number` |
| তারিখ | `covidvaccination.date` |
| টিকা কেন্দ্র | `covidvaccination.center_name` |
| টিকার নাম | `covidvaccination.vaccine_name` FK |

> Form has up to 5 doses. System supports unlimited dose records.

---

## SECTION 10 — মন্ত্রণালয়ের দায়িত্ব (Ministry)

Form table column order:

| Form Column | System Field |
|---|---|
| মন্ত্রণালয়ের নাম | `ministryassignment.ministry` FK |
| মন্ত্রিত্বের ধরন | `ministryassignment.minister_type` FK |
| শুরুর তারিখ | `ministryassignment.start_date` |
| শেষ তারিখ | `ministryassignment.end_date` |
| সংসদ নম্বর | `ministryassignment.parliament` FK |

**★ System additions (not in form):** go_number, go_date, remarks — show after form columns.

---

## SECTION 11 — স্থায়ী কমিটির দায়িত্ব (Committee)

Form table column order:

| Form Column | System Field |
|---|---|
| সংসদ নম্বর | `committeeassignment.parliament` FK |
| স্থায়ী কমিটির নাম | `committeeassignment.committee` FK |
| পদবী | `committeeassignment.position` FK |
| শুরুর তারিখ | `committeeassignment.start_date` |
| শেষ তারিখ | `committeeassignment.end_date` |

**★ System additions:** go_number, go_date, remarks.

---

## SECTION 12 — পূর্ববর্তী সংসদ ইতিহাস (Parliamentary History)

Form table column order:

| Form Column | System Field |
|---|---|
| সংসদের নাম | `previousparliamentaryhistory.assembly_name_bn/en` (free text) |
| নির্বাচনী এলাকার নাম ও নম্বর | `previousparliamentaryhistory.constituency_bn/en` (free text) |
| কোন তারিখ হতে | `previousparliamentaryhistory.from_date` |
| কোন তারিখ পর্যন্ত | `previousparliamentaryhistory.to_date` |
| মন্তব্য | `previousparliamentaryhistory.remarks_bn/en` |

Form rows (pre-printed):
Provincial Assembly → National Council → 1st Parliament → 2nd → ... → 12th Parliament

**UI note:** Pre-populate 14 rows with assembly names as default labels (editable). Staff fills in the relevant ones.

---

## SECTION 13 — সংগঠন (Organizations)

Form: free description area.

**System inline table (matches model):**
`নাম | ভূমিকা | শুরুর তারিখ | শেষ তারিখ`

---

## SECTION 14 — পুরস্কার (Awards)

Form: free description area.

**System inline table:**
`পুরস্কারের নাম | সাল | প্রদানকারী সংস্থা`

---

## SECTION 15 — সমাজ সেবা (Social Service)

Form: free description area.
**System:** Single rich text / textarea field `description_bn` / `description_en`.

---

## SECTION 16 — বিশেষ পদ (Special Positions)

Form positions listed: PM / Speaker / Opposition Leader / Deputy Speaker / Chief Whip / Deputy Leader / Advisor / etc.

| Form Column | System Field |
|---|---|
| সংসদের নাম | `specialpositionhistory.parliament` FK |
| পদের নাম | `specialpositionhistory.role` FK (SpecialRoleType) |
| সময়কাল | `specialpositionhistory.from_date` → `to_date` |

---

## SECTION 17 — প্রকাশনা (Publications)

Form: free description area.

**System inline table:**
`শিরোনাম | প্রকাশক | প্রকাশের সাল | ধরন`

---

## SECTION 18 — বিদেশ ভ্রমণ (Foreign Travel)

Form table column order (simple — 3 columns):

| Form Column | System Model |
|---|---|
| দেশের নাম | `foreigntourcountry.country` FK |
| ভ্রমণের উদ্দেশ্য | `foreigntour.purpose` FK + `purpose_detail` |
| ভ্রমণের সময় | `foreigntourparticipant.departure_date` → `return_date` |

**★ System additions (not in form):** GO number, GO date, tour type, multiple participants per GO. These are back-office tracking fields. Show them in the dedicated Travel Module list; in the MP profile Tab 18 show a simplified read-only summary matching the form columns.

---

## SECTIONS 19 & 20 — শখ / অন্যান্য

Folded into Section 1 (General) Tab at the bottom:

| Form Section | Field | Placement |
|---|---|---|
| 19 — শখ | `mp.hobbies_bn` / `mp.hobbies_en` | Bottom of Tab 1, before submit |
| 20 — অন্যান্য | `mp.other_info_bn` / `mp.other_info_en` | Bottom of Tab 1, after hobbies |

---

## SYSTEM-ADDED FIELDS (not in form)

These appear in the UI but are clearly labeled as system/admin fields:

| Field | Location | Purpose |
|---|---|---|
| `mp.mp_id` | Top of Tab 1 | Parliament-assigned ID |
| `mp.professional_qualifications` | Tab 1, after profession | Doctor/Engineer reporting |
| `mp.photo` | Tab 1, top right | Photo upload |
| `election.nomination_date` | Tab 2 | Additional tracking |
| `election.go_number/go_date` | Tab 2 | GO reference |
| `address.postal_code` | Tab 6 | ★ FROM FORM (was missing) |
| `address.pouroshova_union` | Tab 6 | ★ FROM FORM (was missing) |
| `foreignlanguageskill.proficiency` | Tab 7 | System improvement |
| `ministryassignment.go_number/go_date` | Ministry | GO reference |
| `committeeassignment.go_number/go_date` | Committee | GO reference |
| `foreigntour.go_number/go_date/tour_type` | Travel | GO + classification |

---

## MISSING FROM CURRENT MODEL — ACTION REQUIRED

| # | What | Where | Fix |
|---|---|---|---|
| 1 | `postal_code` | Address model | Add `CharField(max_length=20, blank=True)` |
| 2 | `pouroshova_union_bn/en` | Address model | Add `CharField(max_length=200, blank=True)` |
| 3 | `employer_details_bn/en` | Spouse model | Add `CharField(max_length=500, blank=True)` (institution+position when employed) |
