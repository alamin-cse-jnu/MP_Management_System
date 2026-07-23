from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0005_education_rollreg_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='mp',
            name='self_education_bn',
            field=models.TextField(blank=True, verbose_name='স্ব-শিক্ষা (বাংলায়)'),
        ),
        migrations.AddField(
            model_name='mp',
            name='self_education_en',
            field=models.TextField(blank=True, verbose_name='Self-education (English)'),
        ),
    ]
