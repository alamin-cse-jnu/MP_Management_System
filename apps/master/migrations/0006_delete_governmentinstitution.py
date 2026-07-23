from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0005_officerdesignation'),
        # The InstitutionAssignment FK to GovernmentInstitution must be gone first.
        ('institution', '0003_institution_freetext'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GovernmentInstitution',
        ),
    ]
