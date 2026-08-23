from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0009_spouse_child_mobile'),
    ]

    operations = [
        migrations.AddField(
            model_name='spouse',
            name='passport_number',
            field=models.CharField(blank=True, max_length=30, verbose_name='পাসপোর্ট নং'),
        ),
    ]
