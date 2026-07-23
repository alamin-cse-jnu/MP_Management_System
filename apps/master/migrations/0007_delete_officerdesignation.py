from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0006_delete_governmentinstitution'),
        # The ForeignTourOfficer FK to OfficerDesignation must be gone first.
        ('travel', '0003_officer_designation_freetext'),
    ]

    operations = [
        migrations.DeleteModel(
            name='OfficerDesignation',
        ),
    ]
