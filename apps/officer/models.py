"""
Parliament Secretariat officer roster, synced from the PRP employee API.

Only **Class-1, Active** employees **that carry both a designation and an
office** are kept (see docs/officer-sync-plan.md). Rows are never deleted: an
officer who drops out of that set is flipped to ``is_active=False`` with a
``deactivated_reason``, so tours he is already on keep working while he can no
longer be searched or added to a new tour.
"""

from django.db import models


class OfficerQuerySet(models.QuerySet):
    def selectable(self):
        """THE definition of "can be added to a tour" — mirrors MP.parliament_members()."""
        return self.filter(is_active=True)

    def retired(self):
        return self.filter(is_active=False)


class Officer(models.Model):
    # Why the officer is no longer selectable (blank while active).
    REASON_INACTIVE  = 'inactive'        # PRP status flipped to Inactive
    REASON_CLASS     = 'class_changed'   # no longer class 1
    REASON_INCOMPLETE = 'incomplete'     # PRP cleared his designation / office
    REASON_ABSENT    = 'absent'          # dropped out of the payload entirely
    REASON_CHOICES = [
        (REASON_INACTIVE,   'PRP-তে নিষ্ক্রিয় / Inactive in PRP'),
        (REASON_CLASS,      'ক্লাস-১ নয় / No longer Class 1'),
        (REASON_INCOMPLETE, 'পদবী/দপ্তর নেই / Designation or office missing'),
        (REASON_ABSENT,     'PRP তালিকায় নেই / Absent from PRP payload'),
    ]

    prp_id         = models.CharField('PRP ID', max_length=20, unique=True, db_index=True)
    name_bn        = models.CharField(max_length=200)
    name_en        = models.CharField(max_length=200)
    designation_bn = models.CharField(max_length=200, blank=True)
    designation_en = models.CharField(max_length=200, blank=True)
    officer_class  = models.PositiveSmallIntegerField(default=1)
    prp_status     = models.CharField(max_length=20, blank=True)
    mobile         = models.CharField(max_length=30, blank=True)
    telephone      = models.CharField(max_length=30, blank=True)
    gender         = models.CharField(max_length=20, blank=True)

    # Office block — PRP fills these only partially (wing/branch/section are
    # frequently absent; only office* is always present), so all are optional.
    wing_id      = models.IntegerField(null=True, blank=True)
    wing_bn      = models.CharField(max_length=200, blank=True)
    wing_en      = models.CharField(max_length=200, blank=True)
    branch_id    = models.IntegerField(null=True, blank=True)
    branch_bn    = models.CharField(max_length=200, blank=True)
    branch_en    = models.CharField(max_length=200, blank=True)
    section_id   = models.IntegerField(null=True, blank=True)
    section_bn   = models.CharField(max_length=200, blank=True)
    section_en   = models.CharField(max_length=200, blank=True)
    office_id    = models.IntegerField(null=True, blank=True)
    office_bn    = models.CharField(max_length=200, blank=True)
    office_en    = models.CharField(max_length=200, blank=True)

    is_active          = models.BooleanField(default=True)
    first_synced_at    = models.DateTimeField(auto_now_add=True)
    last_synced_at     = models.DateTimeField(null=True, blank=True)
    deactivated_at     = models.DateTimeField(null=True, blank=True)
    deactivated_reason = models.CharField(max_length=20, blank=True, choices=REASON_CHOICES)

    objects = OfficerQuerySet.as_manager()

    class Meta:
        ordering = ['name_bn', 'prp_id']
        verbose_name = 'Officer'

    def __str__(self):
        return f"{self.name_bn or self.name_en} ({self.prp_id})"

    # ── display helpers ──────────────────────────────────────────────────────
    @property
    def display_name_bn(self):
        return self.name_bn or self.name_en

    @property
    def display_name_en(self):
        return self.name_en or self.name_bn

    @property
    def wing_label_bn(self):
        return self.wing_bn or self.office_bn or ''

    @property
    def wing_label_en(self):
        return self.wing_en or self.office_en or ''

    def office_line(self, is_en=False):
        """Wing › Branch › Section, skipping the parts PRP left empty."""
        if is_en:
            parts = [self.wing_en, self.branch_en, self.section_en or self.office_en]
        else:
            parts = [self.wing_bn, self.branch_bn, self.section_bn or self.office_bn]
        return ' › '.join(p for p in parts if p)

    # `|tr:"office_line"` picks one of these by active language.
    @property
    def office_line_bn(self):
        return self.office_line(False)

    @property
    def office_line_en(self):
        return self.office_line(True)
