from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Officer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('prp_id', models.CharField(db_index=True, max_length=20, unique=True,
                                            verbose_name='PRP ID')),
                ('name_bn', models.CharField(max_length=200)),
                ('name_en', models.CharField(max_length=200)),
                ('designation_bn', models.CharField(blank=True, max_length=200)),
                ('designation_en', models.CharField(blank=True, max_length=200)),
                ('officer_class', models.PositiveSmallIntegerField(default=1)),
                ('prp_status', models.CharField(blank=True, max_length=20)),
                ('mobile', models.CharField(blank=True, max_length=30)),
                ('telephone', models.CharField(blank=True, max_length=30)),
                ('gender', models.CharField(blank=True, max_length=20)),
                ('wing_id', models.IntegerField(blank=True, null=True)),
                ('wing_bn', models.CharField(blank=True, max_length=200)),
                ('wing_en', models.CharField(blank=True, max_length=200)),
                ('branch_id', models.IntegerField(blank=True, null=True)),
                ('branch_bn', models.CharField(blank=True, max_length=200)),
                ('branch_en', models.CharField(blank=True, max_length=200)),
                ('section_id', models.IntegerField(blank=True, null=True)),
                ('section_bn', models.CharField(blank=True, max_length=200)),
                ('section_en', models.CharField(blank=True, max_length=200)),
                ('office_id', models.IntegerField(blank=True, null=True)),
                ('office_bn', models.CharField(blank=True, max_length=200)),
                ('office_en', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('first_synced_at', models.DateTimeField(auto_now_add=True)),
                ('last_synced_at', models.DateTimeField(blank=True, null=True)),
                ('deactivated_at', models.DateTimeField(blank=True, null=True)),
                ('deactivated_reason', models.CharField(blank=True, max_length=20, choices=[
                    ('inactive', 'PRP-তে নিষ্ক্রিয় / Inactive in PRP'),
                    ('class_changed', 'ক্লাস-১ নয় / No longer Class 1'),
                    ('incomplete', 'পদবী/দপ্তর নেই / Designation or office missing'),
                    ('absent', 'PRP তালিকায় নেই / Absent from PRP payload'),
                ])),
            ],
            options={
                'verbose_name': 'Officer',
                'ordering': ['name_bn', 'prp_id'],
            },
        ),
    ]
