from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0003_add_is_active_to_divisionresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='PADesignation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_bn', models.CharField(max_length=200)),
                ('name_en', models.CharField(max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('ordering', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name': 'PA/PS Designation',
                'ordering': ['ordering', 'name_bn'],
            },
        ),
    ]
