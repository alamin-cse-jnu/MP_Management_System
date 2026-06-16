import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0004_padesignation'),
        ('office', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parliamentofficeaddress',
            name='secretary_name_bn',
        ),
        migrations.RemoveField(
            model_name='parliamentofficeaddress',
            name='secretary_name_en',
        ),
        migrations.RemoveField(
            model_name='parliamentofficeaddress',
            name='secretary_mobile',
        ),
        migrations.CreateModel(
            name='MPPAStaff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_bn', models.CharField(max_length=200)),
                ('name_en', models.CharField(blank=True, max_length=200)),
                ('mobile', models.CharField(blank=True, max_length=20)),
                ('ordering', models.IntegerField(default=0)),
                ('designation', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='staff_members',
                    to='master.padesignation',
                )),
                ('office', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pa_staff',
                    to='office.parliamentofficeaddress',
                )),
            ],
            options={
                'ordering': ['ordering', 'name_bn'],
            },
        ),
    ]
