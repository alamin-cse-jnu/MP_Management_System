from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0008_mp_member_type_technocrat'),
    ]

    operations = [
        migrations.AddField(
            model_name='spouse',
            name='mobile',
            field=models.CharField(blank=True, max_length=30, verbose_name='মোবাইল নম্বর'),
        ),
        migrations.AddField(
            model_name='child',
            name='mobile',
            field=models.CharField(blank=True, max_length=30, verbose_name='মোবাইল নম্বর'),
        ),
    ]
