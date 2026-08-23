"""No Objection Certificate (অনাপত্তি সনদ) documents for MP foreign travel.

The Secretariat issues **two different documents** for one trip, not one
document in two languages (see docs/NOC for MP/):

* **English** — the certificate itself. Logo + right-hand contact letterhead,
  ``Sub:`` line, one "This is to certify that…" paragraph, signature block,
  addressee block.
* **Bangla** — the *forwarding letter* (পত্র) that issues it. Centred text-only
  letterhead, ``বিষয়:``, two numbered paragraphs, ``সংযুক্ত: অনাপত্তি সনদ।``, and a
  second block on the same page carrying the **অনুলিপি** distribution list.

They also carry independent memo numbers, so each is its own ``NOC`` row.

``body_html`` is the whole document, authored in CKEditor. It is generated from
an ``NOCTemplate`` and then edited freely, so **the HTML is what prints** while
the columns beside it (memo_no, issue_date, mp, …) are what the list, search and
auto-numbering read. ``regenerate`` rebuilds the HTML from the template.
"""

from django.conf import settings
from django.db import models

LANGUAGE_BN = 'bn'
LANGUAGE_EN = 'en'
LANGUAGE_CHOICES = [
    (LANGUAGE_BN, 'বাংলা পত্র / Bangla forwarding letter'),
    (LANGUAGE_EN, 'ইংরেজি সনদ / English certificate'),
]


class NOCLetterhead(models.Model):
    """The letterhead + numbering prefix, so they change without a deploy.

    Only the newest ``is_active`` row is used; ``current()`` is the single
    accessor. Kept as a table rather than settings constants because the wing,
    section, phone numbers and the Speaker/Acting-Speaker title all change with
    postings.
    """
    org_bn     = models.CharField(max_length=200, default='বাংলাদেশ জাতীয় সংসদ সচিবালয়',
                                  verbose_name='প্রতিষ্ঠান (বাংলায়)')
    org_en     = models.CharField(max_length=200, default='BANGLADESH PARLIAMENT SECRETARIAT',
                                  verbose_name='Organisation (English)')
    wing_bn    = models.CharField(max_length=200, blank=True, default='আইপিএ এন্ড এস অনুবিভাগ',
                                  verbose_name='অনুবিভাগ (বাংলায়)')
    wing_en    = models.CharField(max_length=200, blank=True, default='IPA and S Wing',
                                  verbose_name='Wing (English)')
    section_bn = models.CharField(max_length=200, blank=True, default='আইপিএ শাখা-২',
                                  verbose_name='শাখা (বাংলায়)')
    section_en = models.CharField(max_length=200, blank=True, default='IPA Section-2',
                                  verbose_name='Section (English)')
    address_bn = models.CharField(max_length=200, blank=True, default='সংসদ-ভবন, ঢাকা',
                                  verbose_name='ঠিকানা (বাংলায়)')
    address_en = models.CharField(max_length=200, blank=True, default='PARLIAMENT HOUSE, DHAKA.',
                                  verbose_name='Address (English)')

    website   = models.CharField(max_length=200, blank=True, default='www.parliament.gov.bd',
                                 verbose_name='ওয়েবসাইট')
    telephone = models.CharField(max_length=100, blank=True, default='9110140/8171426',
                                 verbose_name='টেলিফোন')
    fax       = models.CharField(max_length=100, blank=True, default='88-02-9119186/9113767',
                                 verbose_name='ফ্যাক্স')
    email     = models.CharField(max_length=200, blank=True, default='ipa2branch@gmail.com',
                                 verbose_name='ই-মেইল')

    # "11.00.0000.000.610.37.0002" — the year and serial are appended per NOC.
    memo_prefix = models.CharField(max_length=200, default='11.00.0000.000.610.37.0002',
                                   verbose_name='স্মারক নম্বরের প্রথমাংশ')

    # Flips between Speaker and Acting Speaker with who is presiding, so it must
    # never be hardcoded in a template body.
    speaker_title_bn = models.CharField(max_length=200, default='মাননীয় ভারপ্রাপ্ত স্পীকার',
                                        verbose_name='স্পীকারের পদবী (বাংলায়)')
    speaker_title_en = models.CharField(max_length=200, default="Hon'ble Acting Speaker",
                                        verbose_name='Speaker title (English)')

    is_active  = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-updated_at']
        verbose_name = 'NOC লেটারহেড'

    def __str__(self):
        return f'{self.org_bn} — {self.section_bn}'

    @classmethod
    def current(cls):
        """The letterhead in force. Creates the default row on first use."""
        obj = cls.objects.filter(is_active=True).order_by('-updated_at').first()
        if obj is None:
            obj = cls.objects.create()
        return obj


class NOCTemplate(models.Model):
    """Standard wording for one language, with ``{placeholder}`` slots.

    Filled by plain string substitution in ``apps/noc/generation.py`` — never by
    the Django template engine, so a DB-stored template can't execute tags.
    """
    name_bn   = models.CharField(max_length=200, verbose_name='নাম (বাংলায়)')
    name_en   = models.CharField(max_length=200, blank=True, verbose_name='Name (English)')
    language  = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_EN,
                                 verbose_name='ভাষা')
    body_html = models.TextField(verbose_name='দলিলের বিন্যাস (HTML)')
    is_default = models.BooleanField(default=False, verbose_name='ডিফল্ট')
    is_active  = models.BooleanField(default=True)
    ordering   = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['language', 'ordering', 'name_bn']
        verbose_name = 'NOC টেমপ্লেট'

    def __str__(self):
        return f'{self.name_bn} ({self.get_language_display()})'

    @classmethod
    def default_for(cls, language):
        qs = cls.objects.filter(language=language, is_active=True)
        return qs.filter(is_default=True).first() or qs.first()


class NOC(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_FINAL = 'final'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'খসড়া / Draft'),
        (STATUS_FINAL, 'চূড়ান্ত / Final'),
    ]

    tour = models.ForeignKey('travel.ForeignTour', on_delete=models.PROTECT,
                             null=True, blank=True, related_name='nocs',
                             verbose_name='বিদেশ ভ্রমণ GO')
    mp   = models.ForeignKey('mp.MP', on_delete=models.PROTECT, related_name='nocs',
                             verbose_name='সংসদ সদস্য')
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_EN,
                                verbose_name='ভাষা')
    template = models.ForeignKey(NOCTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='documents', verbose_name='টেমপ্লেট')

    memo_no    = models.CharField(max_length=200, verbose_name='স্মারক নম্বর')
    # Kept apart from memo_no so the next number can be suggested even after
    # someone hand-edits the printed string.
    serial_no  = models.IntegerField(null=True, blank=True, verbose_name='ক্রমিক')
    issue_date = models.DateField(verbose_name='তারিখ')

    # Sample-2 (English) prints "…accompanied by his spouse Mrs. X (Passport No-…)".
    spouse = models.ForeignKey('mp.Spouse', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='nocs', verbose_name='সঙ্গী স্বামী/স্ত্রী')

    # Signatory comes from the PRP officer roster and is SNAPSHOTTED, exactly as
    # ForeignTourOfficer does, so an old NOC still reads correctly after the
    # officer is transferred or retires.
    signatory = models.ForeignKey('officer.Officer', on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='signed_nocs',
                                  verbose_name='স্বাক্ষরকারী')
    signatory_name_bn        = models.CharField(max_length=200, blank=True)
    signatory_name_en        = models.CharField(max_length=200, blank=True)
    signatory_designation_bn = models.CharField(max_length=200, blank=True)
    signatory_designation_en = models.CharField(max_length=200, blank=True)
    signatory_phone  = models.CharField(max_length=50, blank=True)
    signatory_mobile = models.CharField(max_length=50, blank=True)
    signatory_email  = models.CharField(max_length=200, blank=True)

    body_html = models.TextField(blank=True, verbose_name='দলিল')
    status    = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT,
                                 verbose_name='অবস্থা')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='created_nocs')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='updated_nocs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-id']
        verbose_name = 'অনাপত্তি সনদ (NOC)'
        indexes = [models.Index(fields=['memo_no']), models.Index(fields=['issue_date'])]

    def __str__(self):
        return f'{self.memo_no} — {self.mp.name_bn}'

    @property
    def is_bangla(self):
        return self.language == LANGUAGE_BN

    @property
    def signatory_is_retired(self):
        """True when the linked officer has dropped out of the PRP keep-set."""
        return bool(self.signatory_id) and not self.signatory.is_active

    def snapshot_signatory(self, officer):
        """Freeze a roster Officer onto this row (mirrors ForeignTourOfficer)."""
        self.signatory = officer
        self.signatory_name_bn = officer.display_name_bn if officer else ''
        self.signatory_name_en = officer.display_name_en if officer else ''
        self.signatory_designation_bn = officer.designation_bn if officer else ''
        self.signatory_designation_en = officer.designation_en if officer else ''
        self.signatory_phone = officer.telephone if officer else ''
        self.signatory_mobile = officer.mobile if officer else ''
        self.signatory_email = ''
