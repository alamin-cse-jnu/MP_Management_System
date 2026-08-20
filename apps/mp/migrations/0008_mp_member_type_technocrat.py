"""Add the 'technocrat' member type.

Technocrat ministers are cabinet members appointed without a parliamentary
seat. They reuse the MP table (profile, ministry assignments, biodata) but must
never count towards the 350 seats — see MP.objects.parliament_members().

Choices-only change: no column alteration on PostgreSQL.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0007_remove_education_reg_no_remove_education_roll_no_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mp',
            name='member_type',
            field=models.CharField(
                choices=[
                    ('direct', 'সরাসরি নির্বাচিত'),
                    ('reserved', 'সংরক্ষিত আসন (মহিলা)'),
                    ('technocrat', 'টেকনোক্র্যাট মন্ত্রী'),
                ],
                default='direct', max_length=20, verbose_name='সদস্যের ধরন',
            ),
        ),
    ]
