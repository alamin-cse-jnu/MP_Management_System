# ref-models.md — MP Model & Operational Module Models

---

## MP MODEL — apps/mp/models.py

```python
class MP(Model):
    # ── SYSTEM ──────────────────────────────────────────
    mp_id                = CharField(max_length=20, unique=True)  # 013000101
    parliament           = FK(Parliament)
    member_type          = CharField(choices=[('direct','Direct'),('reserved','Reserved')])

    # ── SECTION 1: GENERAL ──────────────────────────────
    name_bn / name_en
    father_name_bn / father_name_en
    mother_name_bn / mother_name_en
    dob                  # DateField
    birth_district       = FK(District, related_name='born_mps')
    home_district        = FK(District, related_name='home_mps')
    nationality          = CharField(default='Bangladeshi')
    nid                  = CharField(unique=True)
    gender               = FK(Gender)
    marital_status       = FK(MaritalStatus)
    blood_group          = FK(BloodGroup)
    religion             = FK(Religion)

    # PROFESSION — M2M (multi-select, Select2)
    professional_qualifications = M2M(ProfessionalQualification)
    professions_current         = M2M(Profession, related_name='mps_current')
    professions_previous        = M2M(Profession, related_name='mps_previous')

    tin                  = CharField()

    # FREEDOM FIGHTER
    is_freedom_fighter   = BooleanField(default=False)
    is_ff_child          = BooleanField(default=False)
    is_ff_grandchild     = BooleanField(default=False)

    # PASSPORT
    passport_number / passport_issue_date / passport_expiry_date / passport_issue_place

    photo                = ImageField()
    hobbies_bn / hobbies_en    = TextField()
    other_info_bn / other_info_en = TextField()

    # META (all models)
    created_at / updated_at / created_by / updated_by
    is_active            = BooleanField(default=True)
```

---

## SECTION 2 — Election Info

```python
class ElectionInfo(Model):
    mp / parliament
    constituency      = FK(Constituency)
    party             = FK(PoliticalParty)
    election_date / gazette_date / oath_date
    go_number / go_date / nomination_date
    times_elected     = IntegerField()
```

---

## SECTION 3 — Spouse

```python
class Spouse(Model):
    mp
    name_bn / name_en / dob / nid / marriage_date / tin
    profession            = FK(Profession)
    home_district         = FK(District)
    gender                = FK(Gender)
    employer_details_bn   = CharField(max_length=500, blank=True)
    employer_details_en   = CharField(max_length=500, blank=True)
    # ↑ From PDF form: "পেশা চাকরি হলে প্রতিষ্ঠানের নাম ও পদবী উল্লেখ করবেন"
    #   Institution name + designation if spouse is employed
```

---

## SECTION 4 — Children

```python
class Child(Model):
    mp / serial
    name_bn / name_en / dob / nid_or_birth_reg
    profession        = FK(Profession)
    gender            = FK(Gender)
```

---

## SECTION 5 — Education
See `docs/ref-education.md` for the full spec.

---

## SECTION 6 — Address
See `docs/ref-conventions.md` — ADDRESS FIELDS.

---

## SECTION 7 — Foreign Language Skills

```python
class ForeignLanguageSkill(Model):
    mp / ordering
    language     = FK(ForeignLanguage)
    proficiency  = FK(LanguageProficiency)
```

---

## SECTION 8 — Bank Account

```python
class BankAccount(Model):
    mp / account_number
    bank_name_bn / bank_name_en
    branch_name_bn / branch_name_en
    routing_number / account_type
```

---

## SECTION 9 — Covid Vaccination

```python
class CovidVaccination(Model):
    mp / dose_number / date / certificate_number
    vaccine_name  = FK(VaccineName)
    center_name   = CharField()      # free text
```

---

## SECTION 12 — Previous Parliamentary History
See `docs/ref-conventions.md` — PREVIOUS PARLIAMENTARY HISTORY.

---

## SECTIONS 13–17

```python
class Organization(Model):      # Section 13
    mp / name_bn / name_en / role_bn / role_en / from_date / to_date

class Award(Model):             # Section 14
    mp / name_bn / name_en / year / awarded_by_bn / awarded_by_en

class SocialService(Model):     # Section 15
    mp / description_bn / description_en

class SpecialPositionHistory(Model):   # Section 16
    mp / parliament
    role          = FK(SpecialRoleType)
    from_date / to_date

class Publication(Model):       # Section 17
    mp / title_bn / title_en / pub_year
    publisher_bn / publisher_en / pub_type
```

---

## MINISTRY MODULE — apps/ministry/

```python
class MinistryAssignment(Model):
    mp            = FK(MP)
    parliament    = FK(Parliament)
    ministry      = FK(Ministry)
    minister_type = FK(MinisterType)   # মন্ত্রী / প্রতিমন্ত্রী / উপমন্ত্রী
    start_date    = DateField()
    end_date      = DateField(null=True)
    go_number / go_date
    is_active     = BooleanField(default=True)
    remarks_bn / remarks_en
```

Entry from: MP Profile → Ministry tab, OR Ministry Module list.

**Report — মন্ত্রিসভার তালিকা (grouped by minister_type__rank_order):**
```
[সকল] [মন্ত্রী] [প্রতিমন্ত্রী] [উপমন্ত্রী]
┌───┬───────────────┬────────────────────┬─────────────┐
│ # │ নাম           │ মন্ত্রণালয়         │ ধরণ        │
├───┼───────────────┴────────────────────┴─────────────┤
│   │ ══ মন্ত্রী ══                                    │
│ ১ │ ...           │ অর্থ               │ মন্ত্রী    │
│   │ ══ প্রতিমন্ত্রী ══                               │
│ ১ │ ...           │ শিক্ষা             │ প্রতিমন্ত্রী│
└───┴───────────────┴────────────────────┴─────────────┘
মোট: মন্ত্রী-X | প্রতিমন্ত্রী-X | উপমন্ত্রী-X
```

---

## COMMITTEE MODULE — apps/committee/

```python
class CommitteeAssignment(Model):
    mp         = FK(MP)
    parliament = FK(Parliament)
    committee  = FK(StandingCommittee)
    position   = FK(CommitteePosition)   # সভাপতি / সদস্য
    start_date / end_date / go_number / go_date
    is_active  = BooleanField(default=True)
    remarks_bn / remarks_en
```

**Key report — MP Committee Summary:**
```python
assignments = CommitteeAssignment.objects.filter(mp=mp, is_active=True)
summary = {
    'total'       : assignments.count(),
    'as_chairman' : assignments.filter(position__name_en__icontains='Chairman').count(),
    'as_member'   : assignments.filter(position__name_en__icontains='Member').count(),
}
```

**Output:**
```
মোঃ সেলিম ভুইয়া — কমিটি তথ্য (১৩তম সংসদ)
┌───┬────────────────────────────────────┬──────────┐
│ # │ কমিটির নাম                         │ পদবী    │
├───┼────────────────────────────────────┼──────────┤
│ ১ │ শিক্ষা মন্ত্রণালয় সম্পর্কিত...   │ সভাপতি  │
│ ২ │ অর্থ মন্ত্রণালয় সম্পর্কিত...     │ সদস্য   │
├───┴────────────────────────────────────┴──────────┤
│ মোট: ২ | সভাপতি: ১ | সদস্য: ১                   │
└──────────────────────────────────────────────────┘
```

---

## INSTITUTION MODULE — apps/institution/

```python
class InstitutionAssignment(Model):
    mp / parliament
    institution = FK(Institution)      # BUP, BUET
    role        = FK(InstitutionRole)  # সিনেট সদস্য
    start_date / end_date
    go_number   = CharField()          # e.g. 11.00.0000.000.803.34.0007.26.254
    go_date / nomination_date
    is_active   = BooleanField(default=True)
    remarks_bn / remarks_en
```

---

## FOREIGN TRAVEL MODULE — apps/travel/

```python
class ForeignTour(Model):
    # One GO = one tour; can have multiple MPs + multiple countries
    go_number   = CharField()    # e.g. 1.00.0000.000.610.31.0005.26.41
    go_date     = DateField()
    parliament  = FK(Parliament)
    tour_type   = FK(TravelType)     # Official / Personal / Legacy
    purpose     = FK(TravelPurpose)  # হজ্জ / সরকারি সফর
    purpose_detail_bn / purpose_detail_en
    created_by / created_at

class ForeignTourParticipant(Model):
    tour           = FK(ForeignTour)
    mp             = FK(MP)
    departure_date / return_date
    remarks_bn / remarks_en

class ForeignTourCountry(Model):
    tour     = FK(ForeignTour)
    country  = FK(Country)
    ordering = IntegerField()
```

List UI columns: GO Number | GO Date | Type | Purpose | MPs | Countries
Filter tabs: সব / অফিশিয়াল / ব্যক্তিগত / লিগ্যাসি

---

## OFFICE MODULE — apps/office/

```python
class ParliamentOfficeAddress(Model):
    # সংসদ অফিস ONLY — OneToOne with MP
    mp = OneToOneField(MP)
    room_number / building_bn / building_en
    address_bn = CharField(default='জাতীয় সংসদ ভবন, শের-ই-বাংলা নগর, ঢাকা-১২০৭')
    address_en = CharField(default='National Parliament House, Sher-e-Bangla Nagar, Dhaka-1207')
    telephone / extension / fax / official_email
    secretary_name_bn / secretary_name_en / secretary_mobile
    is_active = BooleanField(default=True)
```
