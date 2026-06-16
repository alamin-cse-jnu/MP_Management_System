from django.db import models


class Division(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'Division'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class District(models.Model):
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name='districts')
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'District'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Upazila(models.Model):
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name='upazilas')
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'Upazila'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Religion(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class BloodGroup(models.Model):
    name_bn = models.CharField(max_length=20)
    name_en = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_en']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class MaritalStatus(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Gender(models.Model):
    name_bn = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Profession(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    category_bn = models.CharField(max_length=100, blank=True)
    category_en = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class ProfessionalQualification(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    short_bn = models.CharField(max_length=50, blank=True)
    short_en = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class EducationLevel(models.Model):
    LEVEL_TYPE_CHOICES = [
        ('primary', 'Primary (PSC/JSC)'),
        ('secondary', 'Secondary (SSC)'),
        ('higher_sec', 'Higher Secondary (HSC)'),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor'),
        ('masters', 'Masters'),
        ('phd', 'PhD / Doctorate'),
        ('other', 'Other'),
    ]
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    level_type = models.CharField(max_length=20, choices=LEVEL_TYPE_CHOICES, default='other')
    degree_order = models.IntegerField(default=0, help_text='Higher = higher education. PSC=1 … PhD=6')
    ordering = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['degree_order', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class EducationGroup(models.Model):
    APPLICABLE_CHOICES = [
        ('secondary', 'Secondary (SSC)'),
        ('higher_sec', 'Higher Secondary (HSC)'),
        ('university', 'University'),
        ('all', 'All Levels'),
    ]
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    applicable_to = models.CharField(max_length=20, choices=APPLICABLE_CHOICES, default='all')
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class EducationSubject(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    group = models.ForeignKey(EducationGroup, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='subjects')
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class DegreeName(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50, blank=True)
    education_level = models.ForeignKey(EducationLevel, on_delete=models.PROTECT,
                                         related_name='degrees')
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class EducationInstitution(models.Model):
    INST_TYPE_CHOICES = [
        ('board', 'Education Board'),
        ('university', 'University'),
        ('foreign', 'Foreign University'),
        ('other', 'Other'),
    ]
    name_bn = models.CharField(max_length=300)
    name_en = models.CharField(max_length=300)
    short_name = models.CharField(max_length=50, blank=True)
    inst_type = models.CharField(max_length=20, choices=INST_TYPE_CHOICES, default='other')
    district = models.ForeignKey(District, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='education_institutions')
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class ResultType(models.Model):
    RESULT_FORMAT_CHOICES = [
        ('division', 'Division (1st/2nd/3rd/Fail)'),
        ('gpa', 'GPA (out of 5.00)'),
        ('cgpa', 'CGPA (out of 4.00)'),
        ('percentage', 'Percentage'),
        ('class', 'Class (1st Class / 2nd Class)'),
        ('pass_fail', 'Pass/Fail Only'),
        ('other', 'Other / Free Text'),
    ]
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    result_format = models.CharField(max_length=20, choices=RESULT_FORMAT_CHOICES, default='other')
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class DivisionResult(models.Model):
    """Old division-based result options e.g. 1st Division, 2nd Division."""
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class PoliticalParty(models.Model):
    name_bn = models.CharField(max_length=300)
    name_en = models.CharField(max_length=300)
    abbreviation = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'Political Party'
        verbose_name_plural = 'Political Parties'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Ministry(models.Model):
    name_bn = models.CharField(max_length=300)
    name_en = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'Ministry'
        verbose_name_plural = 'Ministries'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class MinisterType(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class StandingCommittee(models.Model):
    name_bn = models.CharField(max_length=300)
    name_en = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class CommitteePosition(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class GovernmentInstitution(models.Model):
    """Institutions for MP assignments e.g. BUP, BUET, Dhaka University Senate."""
    name_bn = models.CharField(max_length=300)
    name_en = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class InstitutionRole(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class Country(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class TravelType(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class TravelPurpose(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class ForeignLanguage(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class ProficiencyLevel(models.Model):
    name_bn = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class VaccineName(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class SpecialRoleType(models.Model):
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"


class PADesignation(models.Model):
    """Designation for MP's Personal Assistant / Private Secretary."""
    name_bn = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering', 'name_bn']
        verbose_name = 'PA/PS Designation'

    def __str__(self):
        return f"{self.name_bn} ({self.name_en})"
