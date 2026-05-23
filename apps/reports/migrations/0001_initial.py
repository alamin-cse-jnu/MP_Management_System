from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_label', models.CharField(blank=True, max_length=50)),
                ('model_name', models.CharField(max_length=100, verbose_name='মডেল')),
                ('object_id', models.CharField(max_length=50, verbose_name='রেকর্ড আইডি')),
                ('object_repr', models.CharField(blank=True, max_length=300, verbose_name='রেকর্ড')),
                ('action', models.CharField(
                    choices=[('CREATE', 'তৈরি'), ('UPDATE', 'পরিবর্তন'), ('DELETE', 'মুছে ফেলা')],
                    max_length=10, verbose_name='কার্যক্রম'
                )),
                ('changes', models.JSONField(blank=True, default=dict, verbose_name='পরিবর্তন')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='সময়')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='আইপি')),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='ব্যবহারকারী',
                )),
            ],
            options={
                'verbose_name': 'Audit Log',
                'ordering': ['-timestamp'],
            },
        ),
    ]
