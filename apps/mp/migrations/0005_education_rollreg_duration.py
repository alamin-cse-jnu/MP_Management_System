from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0004_mpsyncconflict'),
    ]

    operations = [
        migrations.AddField(
            model_name='education',
            name='roll_no',
            field=models.CharField(blank=True, max_length=50, verbose_name='রোল নম্বর'),
        ),
        migrations.AddField(
            model_name='education',
            name='reg_no',
            field=models.CharField(blank=True, max_length=50, verbose_name='রেজিস্ট্রেশন নম্বর'),
        ),
        migrations.AddField(
            model_name='education',
            name='course_duration',
            field=models.CharField(blank=True, max_length=50, verbose_name='কোর্সের মেয়াদ'),
        ),
    ]
