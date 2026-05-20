# ref-conventions.md — Coding & Design Conventions

---

## BILINGUAL CONVENTION

Every model storing user-visible data has both `_bn` and `_en` fields.

```python
# Reference model pattern
class Ministry(Model):
    name_bn = CharField(max_length=300)  # মহিলা ও শিশু বিষয়ক মন্ত্রণালয়
    name_en = CharField(max_length=300)  # Ministry of Women and Children Affairs

# MP input field pattern
class MP(Model):
    name_bn = CharField(max_length=200)  # ড. মুহাম্মদ ওসমান ফারুক
    name_en = CharField(max_length=200)  # DR. MUHAMMAD OSMAN FARRUK
```

**Template tag — `templatetags/lang_tags.py`:**
```python
@register.filter
def tr(obj, field='name'):
    lang = get_language()   # reads session language
    bn_val = getattr(obj, f'{field}_bn', None)
    en_val = getattr(obj, f'{field}_en', None)
    if lang == 'en':
        return en_val or bn_val
    return bn_val or en_val
```

**Dropdown display — always bilingual:**
```
কিশোরগঞ্জ (Kishoreganj)
মহিলা ও শিশু বিষয়ক মন্ত্রণালয় (Ministry of Women and Children Affairs)
```

**Language toggle:** `request.session['LANGUAGE'] = 'bn' | 'en'`

---

## BENGALI NUMERAL UTILITY — `utils/bn_numerals.py`

```python
BN_DIGITS = {
    '0':'০','1':'১','2':'২','3':'৩','4':'৪',
    '5':'৫','6':'৬','7':'৭','8':'৮','9':'৯'
}

def to_bn(n):
    return ''.join(BN_DIGITS.get(d, d) for d in str(n))

def to_en(n):
    rev = {v: k for k, v in BN_DIGITS.items()}
    return ''.join(rev.get(c, c) for c in str(n))
```

---

## CONSTITUENCY — SIMPLE ADMIN INPUT

```
Admin types:   1 Panchagarh-1        (English)
               ১ পঞ্চগড়-১            (Bangla)
Shown in dropdown:
               ১ পঞ্চগড়-১ (1 Panchagarh-1)
```

```python
# apps/parliament/models.py
class Constituency(Model):
    display_bn  = CharField(max_length=100)   # ১ পঞ্চগড়-১    ← admin enters
    display_en  = CharField(max_length=100)   # 1 Panchagarh-1 ← admin enters
    is_active   = BooleanField(default=True)
    ordering    = IntegerField(default=0)

    def __str__(self):
        return f"{self.display_bn} ({self.display_en})"

    class Meta:
        ordering = ['ordering', 'display_en']
```

No auto-generation. Admin enters both values. Full CRUD in Master Data.

---

## MP ID — PARLIAMENT FORMAT

```
Format  : 013000101
Meaning : 013 = 13th Parliament | 0001 = Constituency | 01 = sequence
Example : 013000101 → 13th Parliament, Constituency 1
          013030101 → 13th Parliament, Women seat 301

Rule    : Entered manually on the MP entry form
          Validated unique on save
          No auto-generation by the system
```

```python
class MP(Model):
    mp_id = CharField(
        max_length=20,
        unique=True,
        help_text='Parliament-assigned ID e.g. 013000101'
    )
```

---

## ADDRESS FIELDS

Three address types: **Present / Permanent / Dhaka**

```python
class Address(Model):
    ADDRESS_TYPES = [
        ('present',   'বর্তমান ঠিকানা / Present'),
        ('permanent', 'স্থায়ী ঠিকানা / Permanent'),
        ('dhaka',     'ঢাকাস্থ ঠিকানা / Dhaka'),
    ]
    mp           = FK(MP)
    address_type = CharField(choices=ADDRESS_TYPES)

    # THREE DROPDOWNS (cascading via HTMX)
    division     = FK(Division)    # Dropdown
    district     = FK(District)    # Dropdown — filtered by division
    upazila      = FK(Upazila)     # Dropdown — filtered by district

    # ONE FREE TEXT FIELD — house no, road, village, post office
    address_detail_bn = TextField(blank=True)
    address_detail_en = TextField(blank=True)

    # FROM PDF FORM — fields that were missing in original design
    postal_code          = CharField(max_length=20, blank=True)
    pouroshova_union_bn  = CharField(max_length=200, blank=True)
    pouroshova_union_en  = CharField(max_length=200, blank=True)

    # CONTACT — Present address only (leave blank for Permanent/Dhaka)
    telephone    = CharField(blank=True)
    mobile       = CharField(blank=True)
    alt_mobile   = CharField(blank=True)
    whatsapp     = CharField(blank=True)
    email        = EmailField(blank=True)
```

**UI field order (matches PDF form exactly):**
```
বিভাগ:            [ঢাকা বিভাগ (Dhaka Division)  ▼]   ← Dropdown
জেলা:             [ঢাকা (Dhaka)                 ▼]   ← Dropdown (HTMX filtered)
উপজেলা/থানা:     [মিরপুর (Mirpur)              ▼]   ← Dropdown (HTMX filtered)
পৌরসভা/ইউনিয়ন:  [                              ]   ← free text (bn/en)
বাড়ি/রাস্তা/গ্রাম/ডাকঘর: [বাড়ি-৫, রোড-৩...    ]   ← free text (bn/en)
পোস্টাল কোড:    [                              ]
--- Contact fields (Present address only) ---
টেলিফোন / মোবাইল / বিকল্প মোবাইল / হোয়াটসঅ্যাপ / ই-মেইল
```

---

## PREVIOUS PARLIAMENTARY HISTORY — FREE TEXT

Old constituency names/numbers differ from current parliament.
No FK to Constituency — admin enters free text from the original form.

```python
class PreviousParliamentaryHistory(Model):
    mp               = FK(MP, related_name='parliament_history')
    assembly_name_bn = CharField()   # অষ্টম জাতীয় সংসদ  (free text)
    assembly_name_en = CharField()   # 8th National Parliament
    # Examples: Provincial Assembly, National Council, 1st–12th Parliament
    constituency_bn  = CharField()   # ১৬৪ কিশোরগঞ্জ-৩  (as it was then)
    constituency_en  = CharField()   # 164 Kishoreganj-3
    from_date        = DateField(null=True, blank=True)
    to_date          = DateField(null=True, blank=True)
    remarks_bn       = TextField(blank=True)
    remarks_en       = TextField(blank=True)
    ordering         = IntegerField(default=0)

    class Meta:
        ordering = ['ordering']
```

---

## PROFESSIONAL QUALIFICATION vs PROFESSION — KEY DISTINCTION

```
PROFESSIONAL QUALIFICATION  = Formal degree/certification held
                              Doctor, Engineer, Lawyer, CA, Architect etc.
                              Multi-select — an MP can be Doctor AND MBA holder
                              Used for FINDING/REPORTING: "all Doctor MPs"

PROFESSION (Current)        = Actual current occupation
                              Politician, Businessman, Teacher etc.
                              Multi-select dropdown

PROFESSION (Previous)       = Occupation before becoming MP
                              Multi-select dropdown
```

```python
# apps/master/models.py
class ProfessionalQualification(Model):
    name_bn   = CharField()   # চিকিৎসক
    name_en   = CharField()   # Doctor / Physician
    short_bn  = CharField()   # ডাক্তার
    short_en  = CharField()   # Dr.
    is_active = BooleanField(default=True)

class Profession(Model):
    name_bn     = CharField()   # রাজনীতিবিদ
    name_en     = CharField()   # Politician
    category_bn = CharField()   # for optgroup in dropdown
    category_en = CharField()
    is_active   = BooleanField(default=True)

# On MP model — M2M fields
class MP(Model):
    professional_qualifications = ManyToManyField(
        'master.ProfessionalQualification', blank=True
    )
    professions_current = ManyToManyField(
        'master.Profession', blank=True, related_name='mps_current'
    )
    professions_previous = ManyToManyField(
        'master.Profession', blank=True, related_name='mps_previous'
    )
```

**Report queries:**
```python
MP.objects.filter(professional_qualifications__name_en='Doctor')
MP.objects.filter(professional_qualifications__name_en='Engineer')
MP.objects.filter(
    professional_qualifications__name_en='Doctor'
).filter(professions_current__name_en='Businessman')
```

---

## CASCADING DROPDOWNS (HTMX)

**Chain map:**
```
Division → District → Upazila               Address (all 3 types)
Parliament → Constituency                   Election Info
EducationLevel → Group → Subject            Education form
EducationLevel → DegreeName                 Education form
EducationLevel → Institution (by type)      Education form
ResultType → [dynamic result field]         Education form (show/hide)
Ministry → MinisterType                     Ministry assignment
Committee → CommitteePosition               Committee assignment
Institution → InstitutionRole               Institution assignment
TravelType → TravelPurpose                  Foreign travel
```

**HTML pattern:**
```html
<select name="division_id"
        hx-get="{% url 'master:district_options' %}"
        hx-target="#id_district"
        hx-trigger="change">
```

**View pattern:**
```python
# master/views.py
def district_options(request):
    qs = District.objects.filter(
        division_id=request.GET.get('division_id'), is_active=True
    ).order_by('name_bn')
    return render(request, 'partials/options.html', {'items': qs})
```
