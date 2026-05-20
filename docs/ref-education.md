# ref-education.md — Education Sub-System (Detailed Design)

---

## THE CHALLENGE

- Old result system: Division-based (1st Division, 2nd Division, 3rd Division)
- New result system: GPA/CGPA (e.g. GPA 5.00, CGPA 3.85/4.00)
- SSC/HSC have groups: Science / Business Studies / Arts / Vocational
- University has degree names: BSc, MBBS, LLB, MA, MBA, MSc etc.
- Admin must freely add any degree, subject, board, university
- Result field changes dynamically based on ResultType selected

---

## MASTER MODELS — apps/master/

All have full CRUD in Master Data UI.

```python
class EducationLevel(Model):
    name_bn      = CharField()
    name_en      = CharField()
    level_type   = CharField(choices=[...])
    degree_order = IntegerField(default=0)
    # Higher number = higher education level
    # Example: SSC=1, HSC=2, Diploma=3, Bachelor=4, Masters=5, PhD=6
    # Admin sets this when creating/editing Education Levels
    ordering     = IntegerField()
    is_active    = BooleanField(default=True)

class EducationGroup(Model):
    """SSC/HSC: Science / Business Studies / Arts / Vocational
       University: Science / Arts / Business / Medicine / Engineering / Law"""
    name_bn       = CharField()   # বিজ্ঞান
    name_en       = CharField()   # Science
    applicable_to = CharField(choices=[
        ('secondary',  'SSC Level'),
        ('higher_sec', 'HSC Level'),
        ('university', 'University Level'),
        ('all',        'All Levels'),
    ])
    is_active     = BooleanField(default=True)

class EducationSubject(Model):
    """Fine-grained subject — Physics, Economics, Law, Medicine etc."""
    name_bn   = CharField()   # পদার্থবিজ্ঞান
    name_en   = CharField()   # Physics
    group     = FK(EducationGroup, null=True, blank=True)
    is_active = BooleanField(default=True)

class DegreeName(Model):
    """BSc, BA, BBA, MBBS, LLB, MSc, MA, MBA, LLM, PhD etc. Admin adds freely."""
    name_bn         = CharField()   # ব্যাচেলর অব সায়েন্স
    name_en         = CharField()   # Bachelor of Science
    short_name      = CharField()   # BSc
    education_level = FK(EducationLevel)
    is_active       = BooleanField(default=True)

class EducationInstitution(Model):
    """Schools, Colleges, Universities, Boards. Admin adds freely."""
    name_bn    = CharField()   # ঢাকা বিশ্ববিদ্যালয়
    name_en    = CharField()   # University of Dhaka
    short_name = CharField(blank=True)   # DU
    inst_type  = CharField(choices=[
        ('board',      'Education Board'),   # for SSC/HSC
        ('university', 'University'),
        ('foreign',    'Foreign University'),
        ('other',      'Other'),
    ])
    district   = FK('District', null=True, blank=True)
    is_active  = BooleanField(default=True)

class ResultType(Model):
    """Which result format applies. Admin configures."""
    name_bn       = CharField()   # বিভাগ ভিত্তিক
    name_en       = CharField()   # Division Based
    result_format = CharField(choices=[
        ('division',   'Division (1st/2nd/3rd/Fail)'),
        ('gpa',        'GPA (out of 5.00)'),
        ('cgpa',       'CGPA (out of 4.00)'),
        ('percentage', 'Percentage'),
        ('class',      'Class (1st Class / 2nd Class)'),
        ('pass_fail',  'Pass/Fail Only'),
        ('other',      'Other / Free Text'),
    ])
    is_active     = BooleanField(default=True)

class DivisionResult(Model):
    """Old division-based result options."""
    name_bn  = CharField()   # প্রথম বিভাগ
    name_en  = CharField()   # 1st Division
    ordering = IntegerField()
    # Options: Distinction, 1st Division, 2nd Division, 3rd Division, Fail
```

---

## MP EDUCATION RECORD — apps/mp/models.py

```python
class Education(Model):
    mp              = FK(MP, related_name='educations')

    education_level = FK(EducationLevel)
    degree_title    = FK(DegreeName)
    # Field named degree_title (not degree_name) — matches form label

    group           = FK(EducationGroup)
    major_subject   = FK(EducationSubject)

    institution     = FK(EducationInstitution)
    institution_other_bn = CharField(blank=True)   # free text if not in list
    institution_other_en = CharField(blank=True)

    board_affiliation = FK(EducationInstitution,
                           null=True,
                           related_name='affiliated_educations')
    # Separate FK to same Institution table filtered by type='board'
    # Examples: University of Dhaka, National University, BTEB, Dhaka Board

    passing_year    = IntegerField()
    result_type     = FK(ResultType)

    # Division-based (old)
    division_result = FK(DivisionResult, null=True, blank=True)

    # GPA/CGPA-based (new)
    gpa_value       = DecimalField(max_digits=4, decimal_places=2, null=True)
    gpa_out_of      = DecimalField(max_digits=4, decimal_places=2, null=True)
    # e.g. 5.00/5.00  OR  3.85/4.00

    # Percentage
    percentage      = DecimalField(max_digits=5, decimal_places=2, null=True)

    # Class (university)
    class_result    = CharField(blank=True)   # '1st Class', '2nd Class'

    # Free text fallback
    result_text     = CharField(blank=True)

    @property
    def result_display(self):
        fmt = self.result_type.result_format if self.result_type else 'other'
        if fmt == 'division' and self.division_result:
            return self.division_result.name_bn
        elif fmt in ('gpa', 'cgpa') and self.gpa_value:
            return f"{self.gpa_value} (out of {self.gpa_out_of})"
        elif fmt == 'percentage' and self.percentage:
            return f"{self.percentage}%"
        elif fmt == 'class':
            return self.class_result
        return self.result_text

    class Meta:
        ordering = ['ordering']
```

---

## EDUCATION FORM — DYNAMIC STEPS (HTMX)

```
1. Education Level  → [SSC ▼]
        ↓ HTMX
2. Group            → [Science ▼]          (hidden if level=PSC/JSC/PhD)
        ↓ HTMX
3. Degree Name      → [SSC ▼]              (filtered by level)
4. Subject          → [Physics ▼]          (filtered by group)
5. Institution      → [Dhaka Board ▼]      (filtered by inst_type)
   OR free text     → [                  ] (if not in list)
6. Passing Year     → [2005]
7. Result Type      → [GPA (out of 5.00) ▼]
        ↓ HTMX shows ONLY the relevant result field
8. Result           → [5.00] out of [5.00]
   OR Division      → [1st Division ▼]
   OR Percentage    → [75.50]%
   OR Class         → [1st Class]
   OR Free text     → [                  ]
```

---

## REPORT QUERIES USING degree_order

```python
# MPs with highest education (sorted)
MP.objects.annotate(
    highest_degree=Max('educations__education_level__degree_order')
).order_by('-highest_degree')

# MPs who completed at least Bachelor (degree_order >= 4)
MP.objects.filter(
    educations__education_level__degree_order__gte=4
).distinct()

# MPs with Masters or above, with subject
MP.objects.filter(
    educations__education_level__degree_order__gte=5
).select_related('educations__major_subject')
```
