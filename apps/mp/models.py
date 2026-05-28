from django.conf import settings
from django.db import models


class MP(models.Model):
    MEMBER_TYPE_CHOICES = [
        ('direct',   'সরাসরি নির্বাচিত'),
        ('reserved', 'সংরক্ষিত আসন (মহিলা)'),
    ]

    # ── SYSTEM ──────────────────────────────────────────────────────────────────
    mp_id       = models.CharField(max_length=20, unique=True, verbose_name='এমপি আইডি')
    parliament  = models.ForeignKey(
        'parliament.Parliament', on_delete=models.PROTECT,
        related_name='members', verbose_name='সংসদ'
    )
    member_type = models.CharField(
        max_length=20, choices=MEMBER_TYPE_CHOICES, default='direct',
        verbose_name='সদস্যের ধরন'
    )

    # ── SECTION 1: GENERAL ──────────────────────────────────────────────────────
    name_bn          = models.CharField(max_length=200, verbose_name='নাম (বাংলায়)')
    name_en          = models.CharField(max_length=200, verbose_name='Name (English)')
    father_name_bn   = models.CharField(max_length=200, blank=True, verbose_name='পিতার নাম (বাংলায়)')
    father_name_en   = models.CharField(max_length=200, blank=True, verbose_name="Father's Name")
    mother_name_bn   = models.CharField(max_length=200, blank=True, verbose_name='মাতার নাম (বাংলায়)')
    mother_name_en   = models.CharField(max_length=200, blank=True, verbose_name="Mother's Name")
    dob              = models.DateField(null=True, blank=True, verbose_name='জন্ম তারিখ')
    birth_district   = models.ForeignKey(
        'master.District', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='born_mps', verbose_name='জন্মস্থান (জেলা)'
    )
    home_district    = models.ForeignKey(
        'master.District', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='home_mps', verbose_name='নিজ জেলা'
    )
    nationality      = models.CharField(max_length=100, default='বাংলাদেশী', verbose_name='জাতীয়তা')
    nid              = models.CharField(
        max_length=30, unique=True, null=True, blank=True,
        verbose_name='জাতীয় পরিচয়পত্র নং'
    )
    gender           = models.ForeignKey(
        'master.Gender', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='লিঙ্গ'
    )
    marital_status   = models.ForeignKey(
        'master.MaritalStatus', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='বৈবাহিক অবস্থা'
    )
    blood_group      = models.ForeignKey(
        'master.BloodGroup', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='রক্তের গ্রুপ'
    )
    religion         = models.ForeignKey(
        'master.Religion', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='ধর্ম'
    )

    professional_qualifications = models.ManyToManyField(
        'master.ProfessionalQualification', blank=True, verbose_name='পেশাদার যোগ্যতা'
    )
    professions_current = models.ManyToManyField(
        'master.Profession', blank=True, related_name='mps_current',
        verbose_name='পেশা (বর্তমান)'
    )
    professions_previous = models.ManyToManyField(
        'master.Profession', blank=True, related_name='mps_previous',
        verbose_name='পেশা (পূর্বের)'
    )

    tin                  = models.CharField(max_length=30, blank=True, verbose_name='টিআইএন')
    is_freedom_fighter   = models.BooleanField(default=False, verbose_name='মুক্তিযোদ্ধা')
    is_ff_child          = models.BooleanField(default=False, verbose_name='মুক্তিযোদ্ধার সন্তান')
    is_ff_grandchild     = models.BooleanField(default=False, verbose_name='মুক্তিযোদ্ধার নাতি-নাতনি')

    passport_number      = models.CharField(max_length=30, blank=True, verbose_name='পাসপোর্ট নং')
    passport_issue_date  = models.DateField(null=True, blank=True, verbose_name='ইস্যুর তারিখ')
    passport_expiry_date = models.DateField(null=True, blank=True, verbose_name='মেয়াদোত্তীর্ণের তারিখ')
    passport_issue_place = models.CharField(max_length=200, blank=True, verbose_name='ইস্যুর স্থান')

    photo            = models.ImageField(upload_to='mp_photos/', null=True, blank=True, verbose_name='ছবি')
    hobbies_bn       = models.TextField(blank=True, verbose_name='শখ (বাংলায়)')
    hobbies_en       = models.TextField(blank=True, verbose_name='Hobbies (English)')
    other_info_bn    = models.TextField(blank=True, verbose_name='অন্যান্য তথ্য (বাংলায়)')
    other_info_en    = models.TextField(blank=True, verbose_name='Other Info (English)')

    # ── META ────────────────────────────────────────────────────────────────────
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mp_created'
    )
    updated_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mp_updated'
    )
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['mp_id']
        verbose_name = 'সংসদ সদস্য'

    def __str__(self):
        return f"{self.name_bn} ({self.mp_id})"

    @property
    def current_election(self):
        return self.election_infos.filter(parliament=self.parliament).first()

    @property
    def profile_score(self):
        checks = [
            bool(self.photo),
            bool(self.dob),
            bool(self.gender_id),
            bool(self.religion_id),
            bool(self.home_district_id),
            bool(self.nid),
            bool(self.father_name_bn),
            bool(self.mother_name_bn),
            bool(self.blood_group_id),
            bool(self.marital_status_id),
        ]
        return round(sum(checks) / len(checks) * 100)


class ElectionInfo(models.Model):
    mp           = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='election_infos')
    parliament   = models.ForeignKey('parliament.Parliament', on_delete=models.PROTECT)
    constituency = models.ForeignKey(
        'parliament.Constituency', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='নির্বাচনী এলাকা'
    )
    party            = models.ForeignKey(
        'master.PoliticalParty', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='রাজনৈতিক দল'
    )
    election_date    = models.DateField(null=True, blank=True, verbose_name='নির্বাচনের তারিখ')
    gazette_date     = models.DateField(null=True, blank=True, verbose_name='গেজেটের তারিখ')
    oath_date        = models.DateField(null=True, blank=True, verbose_name='শপথের তারিখ')
    nomination_date  = models.DateField(null=True, blank=True, verbose_name='মনোনয়নের তারিখ')
    go_number        = models.CharField(max_length=100, blank=True, verbose_name='GO নম্বর')
    go_date          = models.DateField(null=True, blank=True, verbose_name='GO তারিখ')
    times_elected    = models.IntegerField(default=1, verbose_name='কতবার নির্বাচিত')

    class Meta:
        unique_together = [('mp', 'parliament')]
        verbose_name = 'নির্বাচন সংক্রান্ত তথ্য'

    def __str__(self):
        return f"{self.mp.name_bn} — {self.parliament}"


class Spouse(models.Model):
    mp               = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='spouses')
    name_bn          = models.CharField(max_length=200, verbose_name='নাম (বাংলায়)')
    name_en          = models.CharField(max_length=200, blank=True, verbose_name='Name (English)')
    dob              = models.DateField(null=True, blank=True, verbose_name='জন্ম তারিখ')
    nid              = models.CharField(max_length=30, blank=True, verbose_name='জাতীয় পরিচয়পত্র নং')
    marriage_date    = models.DateField(null=True, blank=True, verbose_name='বিবাহের তারিখ')
    tin              = models.CharField(max_length=30, blank=True, verbose_name='টিআইএন')
    profession       = models.ForeignKey(
        'master.Profession', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='পেশা'
    )
    home_district    = models.ForeignKey(
        'master.District', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='নিজ জেলা'
    )
    gender           = models.ForeignKey(
        'master.Gender', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='লিঙ্গ'
    )
    employer_details_bn = models.CharField(max_length=500, blank=True,
                                            verbose_name='প্রতিষ্ঠান ও পদবী (বাংলায়)')
    employer_details_en = models.CharField(max_length=500, blank=True,
                                            verbose_name='Institution & Designation')

    class Meta:
        ordering = ['id']
        verbose_name = 'স্বামী/স্ত্রী'

    def __str__(self):
        return self.name_bn


class Child(models.Model):
    mp               = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='children')
    serial           = models.IntegerField(default=1, verbose_name='ক্রম')
    name_bn          = models.CharField(max_length=200, verbose_name='নাম (বাংলায়)')
    name_en          = models.CharField(max_length=200, blank=True, verbose_name='Name (English)')
    dob              = models.DateField(null=True, blank=True, verbose_name='জন্ম তারিখ')
    nid_or_birth_reg = models.CharField(max_length=50, blank=True,
                                         verbose_name='এনআইডি / জন্ম নিবন্ধন')
    profession       = models.ForeignKey(
        'master.Profession', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='পেশা'
    )
    gender           = models.ForeignKey(
        'master.Gender', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='লিঙ্গ'
    )

    class Meta:
        ordering = ['serial']
        verbose_name = 'সন্তান'

    def __str__(self):
        return self.name_bn


class Education(models.Model):
    mp                   = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='educations')
    education_level      = models.ForeignKey(
        'master.EducationLevel', on_delete=models.PROTECT, null=True, blank=True,
        verbose_name='শিক্ষার স্তর'
    )
    degree_title         = models.ForeignKey(
        'master.DegreeName', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='পরীক্ষা/ডিগ্রির নাম'
    )
    group                = models.ForeignKey(
        'master.EducationGroup', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='গ্রুপ'
    )
    major_subject        = models.ForeignKey(
        'master.EducationSubject', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='বিষয়'
    )
    institution          = models.ForeignKey(
        'master.EducationInstitution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student_educations', verbose_name='প্রতিষ্ঠান'
    )
    institution_other_bn = models.CharField(max_length=300, blank=True,
                                             verbose_name='অন্য প্রতিষ্ঠান (বাংলায়)')
    institution_other_en = models.CharField(max_length=300, blank=True,
                                             verbose_name='Other Institution')
    board_affiliation    = models.ForeignKey(
        'master.EducationInstitution', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='affiliated_educations', verbose_name='শিক্ষাবোর্ড/বিশ্ববিদ্যালয়'
    )
    passing_year         = models.IntegerField(null=True, blank=True, verbose_name='পাসের সন')
    result_type          = models.ForeignKey(
        'master.ResultType', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='ফলাফলের ধরন'
    )
    division_result      = models.ForeignKey(
        'master.DivisionResult', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='বিভাগ'
    )
    gpa_value            = models.DecimalField(max_digits=4, decimal_places=2,
                                               null=True, blank=True, verbose_name='জিপিএ/সিজিপিএ')
    gpa_out_of           = models.DecimalField(max_digits=4, decimal_places=2,
                                               null=True, blank=True, verbose_name='মোট')
    percentage           = models.DecimalField(max_digits=5, decimal_places=2,
                                               null=True, blank=True, verbose_name='শতকরা (%)')
    class_result         = models.CharField(max_length=50, blank=True, verbose_name='শ্রেণী')
    result_text          = models.CharField(max_length=100, blank=True, verbose_name='ফলাফল')
    ordering             = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = 'শিক্ষাগত যোগ্যতা'

    def __str__(self):
        lvl = str(self.degree_title or self.education_level or '—')
        return f"{lvl} — {self.mp.name_bn}"

    @property
    def result_display(self):
        if not self.result_type:
            return self.result_text or '—'
        fmt = self.result_type.result_format
        if fmt == 'division' and self.division_result:
            return self.division_result.name_bn
        if fmt in ('gpa', 'cgpa') and self.gpa_value is not None:
            return f"{self.gpa_value} / {self.gpa_out_of or '—'}"
        if fmt == 'percentage' and self.percentage is not None:
            return f"{self.percentage}%"
        if fmt == 'class':
            return self.class_result or '—'
        return self.result_text or '—'


class Address(models.Model):
    ADDRESS_TYPES = [
        ('present',   'বর্তমান ঠিকানা'),
        ('permanent', 'স্থায়ী ঠিকানা'),
        ('dhaka',     'ঢাকাস্থ ঠিকানা'),
    ]

    mp           = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES,
                                    verbose_name='ঠিকানার ধরন')
    division     = models.ForeignKey(
        'master.Division', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='বিভাগ'
    )
    district     = models.ForeignKey(
        'master.District', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='জেলা'
    )
    upazila      = models.ForeignKey(
        'master.Upazila', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='উপজেলা/থানা'
    )
    pouroshova_union_bn = models.CharField(max_length=200, blank=True,
                                            verbose_name='পৌরসভা/ইউনিয়ন (বাংলায়)')
    pouroshova_union_en = models.CharField(max_length=200, blank=True,
                                            verbose_name='Pouroshova/Union')
    address_detail_bn   = models.TextField(blank=True,
                                            verbose_name='বাড়ি/রাস্তা/গ্রাম/ডাকঘর (বাংলায়)')
    address_detail_en   = models.TextField(blank=True, verbose_name='Address Details')
    postal_code         = models.CharField(max_length=20, blank=True, verbose_name='পোস্টাল কোড')

    # Contact — present address only
    telephone  = models.CharField(max_length=30, blank=True, verbose_name='টেলিফোন')
    mobile     = models.CharField(max_length=30, blank=True, verbose_name='মোবাইল')
    alt_mobile = models.CharField(max_length=30, blank=True, verbose_name='বিকল্প মোবাইল')
    whatsapp   = models.CharField(max_length=30, blank=True, verbose_name='হোয়াটসঅ্যাপ')
    email      = models.EmailField(blank=True, verbose_name='ই-মেইল')

    class Meta:
        unique_together = [('mp', 'address_type')]
        ordering = ['address_type']
        verbose_name = 'ঠিকানা'

    def __str__(self):
        return f"{self.get_address_type_display()} — {self.mp.name_bn}"


# ── SECTION 7: FOREIGN LANGUAGE SKILLS ───────────────────────────────────────

class ForeignLanguageSkill(models.Model):
    mp          = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='language_skills')
    language    = models.ForeignKey(
        'master.ForeignLanguage', on_delete=models.PROTECT, verbose_name='ভাষা')
    proficiency = models.ForeignKey(
        'master.ProficiencyLevel', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='দক্ষতার মাত্রা')
    ordering    = models.IntegerField(default=0, verbose_name='ক্রম')

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = 'বিদেশি ভাষার দক্ষতা'

    def __str__(self):
        return f"{self.language} — {self.mp.name_bn}"


# ── SECTION 8: BANK ACCOUNT ───────────────────────────────────────────────────

class BankAccount(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('savings', 'সঞ্চয়ী (Savings)'),
        ('current', 'চলতি (Current)'),
        ('other',   'অন্যান্য (Other)'),
    ]
    mp             = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=50, verbose_name='হিসাব নম্বর')
    bank_name_bn   = models.CharField(max_length=200, verbose_name='ব্যাংকের নাম (বাংলায়)')
    bank_name_en   = models.CharField(max_length=200, blank=True, verbose_name='Bank Name')
    branch_name_bn = models.CharField(max_length=200, blank=True, verbose_name='শাখার নাম (বাংলায়)')
    branch_name_en = models.CharField(max_length=200, blank=True, verbose_name='Branch Name')
    routing_number = models.CharField(max_length=30, blank=True, verbose_name='রাউটিং নম্বর')
    account_type   = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES,
                                       default='savings', verbose_name='হিসাবের ধরন')

    class Meta:
        ordering = ['id']
        verbose_name = 'ব্যাংক হিসাব'

    def __str__(self):
        return f"{self.bank_name_bn} — {self.mp.name_bn}"


# ── SECTION 9: COVID VACCINATION ─────────────────────────────────────────────

class CovidVaccination(models.Model):
    mp                 = models.ForeignKey(MP, on_delete=models.CASCADE,
                                           related_name='covid_vaccinations')
    dose_number        = models.IntegerField(verbose_name='ডোজ নম্বর')
    date               = models.DateField(null=True, blank=True, verbose_name='তারিখ')
    vaccine_name       = models.ForeignKey(
        'master.VaccineName', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='টিকার নাম')
    center_name        = models.CharField(max_length=300, blank=True, verbose_name='টিকা কেন্দ্র')
    certificate_number = models.CharField(max_length=100, blank=True,
                                           verbose_name='সার্টিফিকেট নম্বর')

    class Meta:
        ordering = ['dose_number']
        verbose_name = 'কোভিড টিকা'

    def __str__(self):
        return f"ডোজ {self.dose_number} — {self.mp.name_bn}"


# ── SECTION 12: PREVIOUS PARLIAMENTARY HISTORY ───────────────────────────────

class PreviousParliamentaryHistory(models.Model):
    mp               = models.ForeignKey(MP, on_delete=models.CASCADE,
                                          related_name='parliamentary_histories')
    assembly_name_bn = models.CharField(max_length=200, blank=True,
                                         verbose_name='সংসদের নাম (বাংলায়)')
    assembly_name_en = models.CharField(max_length=200, blank=True, verbose_name='Assembly Name')
    constituency_bn  = models.CharField(max_length=300, blank=True,
                                         verbose_name='নির্বাচনী এলাকা (বাংলায়)')
    constituency_en  = models.CharField(max_length=300, blank=True, verbose_name='Constituency')
    from_date        = models.DateField(null=True, blank=True, verbose_name='শুরুর তারিখ')
    to_date          = models.DateField(null=True, blank=True, verbose_name='শেষ তারিখ')
    remarks_bn       = models.CharField(max_length=500, blank=True, verbose_name='মন্তব্য (বাংলায়)')
    remarks_en       = models.CharField(max_length=500, blank=True, verbose_name='Remarks')
    ordering         = models.IntegerField(default=0, verbose_name='ক্রম')

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = 'পূর্ববর্তী সংসদ ইতিহাস'

    def __str__(self):
        return f"{self.assembly_name_bn or '—'} — {self.mp.name_bn}"


# ── SECTION 13: ORGANIZATIONS ────────────────────────────────────────────────

class Organization(models.Model):
    mp        = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='organizations')
    name_bn   = models.CharField(max_length=300, verbose_name='সংগঠনের নাম (বাংলায়)')
    name_en   = models.CharField(max_length=300, blank=True, verbose_name='Organization Name')
    role_bn   = models.CharField(max_length=200, blank=True, verbose_name='ভূমিকা (বাংলায়)')
    role_en   = models.CharField(max_length=200, blank=True, verbose_name='Role')
    from_date = models.DateField(null=True, blank=True, verbose_name='শুরুর তারিখ')
    to_date   = models.DateField(null=True, blank=True, verbose_name='শেষ তারিখ')
    ordering  = models.IntegerField(default=0, verbose_name='ক্রম')

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = 'সংগঠন'

    def __str__(self):
        return f"{self.name_bn} — {self.mp.name_bn}"


# ── SECTION 14: AWARDS ────────────────────────────────────────────────────────

class Award(models.Model):
    mp            = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='awards')
    name_bn       = models.CharField(max_length=300, verbose_name='পুরস্কারের নাম (বাংলায়)')
    name_en       = models.CharField(max_length=300, blank=True, verbose_name='Award Name')
    year          = models.IntegerField(null=True, blank=True, verbose_name='সাল')
    awarded_by_bn = models.CharField(max_length=300, blank=True,
                                      verbose_name='প্রদানকারী সংস্থা (বাংলায়)')
    awarded_by_en = models.CharField(max_length=300, blank=True, verbose_name='Awarded By')
    ordering      = models.IntegerField(default=0, verbose_name='ক্রম')

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = 'পুরস্কার'

    def __str__(self):
        return f"{self.name_bn} — {self.mp.name_bn}"


# ── SECTION 15: SOCIAL SERVICE ────────────────────────────────────────────────

class SocialService(models.Model):
    mp             = models.OneToOneField(MP, on_delete=models.CASCADE,
                                          related_name='social_service')
    description_bn = models.TextField(blank=True, verbose_name='সমাজ সেবা (বাংলায়)')
    description_en = models.TextField(blank=True, verbose_name='Social Service (English)')

    class Meta:
        verbose_name = 'সমাজ সেবা'

    def __str__(self):
        return f"সমাজ সেবা — {self.mp.name_bn}"


# ── SECTION 16: SPECIAL POSITION HISTORY ─────────────────────────────────────

class SpecialPositionHistory(models.Model):
    mp         = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='special_positions')
    parliament = models.ForeignKey(
        'parliament.Parliament', on_delete=models.PROTECT, verbose_name='সংসদ')
    role       = models.ForeignKey(
        'master.SpecialRoleType', on_delete=models.PROTECT, verbose_name='পদের নাম')
    from_date  = models.DateField(null=True, blank=True, verbose_name='শুরুর তারিখ')
    to_date    = models.DateField(null=True, blank=True, verbose_name='শেষ তারিখ')

    class Meta:
        ordering = ['from_date']
        verbose_name = 'বিশেষ পদ'

    def __str__(self):
        return f"{self.role} — {self.mp.name_bn}"


# ── SECTION 17: PUBLICATIONS ─────────────────────────────────────────────────

class Publication(models.Model):
    PUB_TYPE_CHOICES = [
        ('book',     'বই (Book)'),
        ('article',  'প্রবন্ধ (Article)'),
        ('research', 'গবেষণাপত্র (Research)'),
        ('other',    'অন্যান্য (Other)'),
    ]
    mp           = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='publications')
    title_bn     = models.CharField(max_length=300, verbose_name='শিরোনাম (বাংলায়)')
    title_en     = models.CharField(max_length=300, blank=True, verbose_name='Title (English)')
    pub_year     = models.IntegerField(null=True, blank=True, verbose_name='প্রকাশের সাল')
    publisher_bn = models.CharField(max_length=300, blank=True, verbose_name='প্রকাশক (বাংলায়)')
    publisher_en = models.CharField(max_length=300, blank=True, verbose_name='Publisher')
    pub_type     = models.CharField(max_length=20, choices=PUB_TYPE_CHOICES,
                                     default='book', verbose_name='ধরন')
    ordering     = models.IntegerField(default=0, verbose_name='ক্রম')

    class Meta:
        ordering = ['ordering', 'id']
        verbose_name = 'প্রকাশনা'

    def __str__(self):
        return f"{self.title_bn} — {self.mp.name_bn}"
