from django.core.exceptions import ValidationError
from django.db import models

from apps.master.models import CommitteePosition, StandingCommittee, SubCommittee
from apps.mp.models import MP
from apps.parliament.models import Parliament
from utils.go_files import validate_go_file


class CommitteeAssignment(models.Model):
    """One seat on one committee.

    A standing committee can run several sub-committees, and this one row type
    carries both levels: **`sub_committee` empty means the seat is on the main
    committee; set, it means the seat is on that sub-committee.** `committee`
    always holds the parent either way, so every existing filter, report and
    count over `committee` keeps meaning what it meant — it simply also reaches
    the sub-committee rows.

    A sub-committee is staffed *from the parent committee's members*, so
    `clean()` refuses a sub seat for an MP who does not already hold an active
    main seat on that committee in the same parliament.
    """

    mp         = models.ForeignKey(MP, on_delete=models.CASCADE, related_name='committee_assignments')
    parliament = models.ForeignKey(Parliament, on_delete=models.PROTECT, related_name='committee_assignments')
    committee  = models.ForeignKey(StandingCommittee, on_delete=models.PROTECT, related_name='assignments')
    sub_committee = models.ForeignKey(SubCommittee, on_delete=models.PROTECT, null=True, blank=True,
                                      related_name='assignments',
                                      verbose_name='উপ-কমিটি')
    position   = models.ForeignKey(CommitteePosition, on_delete=models.PROTECT, related_name='assignments')
    start_date = models.DateField()
    end_date   = models.DateField(null=True, blank=True)
    go_number  = models.CharField(max_length=100, blank=True)
    go_date    = models.DateField(null=True, blank=True)
    go_file    = models.FileField(upload_to='go/committee/', blank=True, null=True,
                                  validators=[validate_go_file])
    is_active  = models.BooleanField(default=True)
    remarks_bn = models.TextField(blank=True)
    remarks_en = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['committee__name_bn', 'sub_committee__name_bn']

    def __str__(self):
        if self.sub_committee_id:
            return f"{self.mp.name_bn} — {self.committee.name_bn} › {self.sub_committee.name_bn}"
        return f"{self.mp.name_bn} — {self.committee.name_bn}"

    # ── Guards ────────────────────────────────────────────────────────────────
    # A sub-committee seat is only meaningful under its own parent and only for
    # someone already on that parent. Both are checked here rather than in the
    # form, because entry runs from BOTH the module and the MP profile and a
    # guard on one write path is no guard at all.

    def clean(self):
        super().clean()
        if self.sub_committee_id:
            if self.sub_committee.committee_id != self.committee_id:
                raise ValidationError({'sub_committee': (
                    'এই উপ-কমিটি নির্বাচিত স্থায়ী কমিটির অধীনে নয়। / '
                    'This sub-committee does not belong to the selected standing committee.'
                )})
            # Non-field on purpose: `mp` is not a form field on the MP-profile
            # write path (the member is fixed by the URL), and an error keyed on
            # a field the form does not have raises ValueError inside
            # ModelForm._post_clean instead of showing the operator anything.
            if self.mp_id and self.parliament_id and not self.mp_is_main_member(
                    self.mp_id, self.parliament_id, self.committee_id, exclude_pk=self.pk):
                raise ValidationError((
                    'উপ-কমিটির সদস্য মূল কমিটির সদস্যদের মধ্য থেকে হতে হবে — '
                    'আগে মূল কমিটিতে যোগ করুন। / A sub-committee member must already sit on '
                    'the main committee — add the main-committee seat first.'
                ))
        # Duplicate seat. Checked only when this save actually *creates* the
        # collision — an edit that leaves the (member, parliament, committee,
        # sub-committee) tuple alone goes through even if prod already carries a
        # duplicate pair, because locking those rows would be a new way of being
        # stuck (the same call master-data dedupe makes).
        identity = (self.mp_id, self.parliament_id, self.committee_id, self.sub_committee_id)
        changed  = True
        if self.pk:
            old = CommitteeAssignment.objects.filter(pk=self.pk).values_list(
                'mp_id', 'parliament_id', 'committee_id', 'sub_committee_id').first()
            changed = old is not None and tuple(old) != identity
        if changed and self.is_active and all(identity[:3]):
            dup = CommitteeAssignment.objects.filter(
                mp_id=self.mp_id, parliament_id=self.parliament_id,
                committee_id=self.committee_id, sub_committee_id=self.sub_committee_id,
                is_active=True)
            if self.pk:
                dup = dup.exclude(pk=self.pk)
            if dup.exists():
                raise ValidationError(
                    'এই সদস্যের এই কমিটিতে একটি সক্রিয় নিয়োগ ইতিমধ্যে আছে। / '
                    'This member already holds an active seat on this committee.'
                )

    @staticmethod
    def mp_is_main_member(mp_id, parliament_id, committee_id, exclude_pk=None):
        """Does this MP hold an active MAIN seat on that committee?"""
        qs = CommitteeAssignment.objects.filter(
            mp_id=mp_id, parliament_id=parliament_id, committee_id=committee_id,
            sub_committee__isnull=True, is_active=True)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return qs.exists()
