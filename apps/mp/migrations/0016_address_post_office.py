# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mp', '0015_backfill_travel_sort_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='post_office_bn',
            field=models.CharField(blank=True, max_length=200,
                                   verbose_name='ডাকঘর (বাংলায়)'),
        ),
        migrations.AddField(
            model_name='address',
            name='post_office_en',
            field=models.CharField(blank=True, max_length=200,
                                   verbose_name='Post Office'),
        ),
    ]
