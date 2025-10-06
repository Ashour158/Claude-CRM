# Generated migration for sharing app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SharingRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='Human-readable rule name', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Rule description')),
                ('object_type', models.CharField(choices=[('lead', 'Lead'), ('deal', 'Deal'), ('account', 'Account'), ('contact', 'Contact'), ('activity', 'Activity')], db_index=True, help_text='Type of object this rule applies to', max_length=50)),
                ('predicate', models.JSONField(help_text="JSON predicate defining rule conditions. Format: {'field': 'status', 'operator': 'eq', 'value': 'qualified'}")),
                ('access_level', models.CharField(choices=[('read_only', 'Read Only'), ('read_write', 'Read/Write')], default='read_only', help_text='Access level granted by this rule', max_length=20)),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Whether this rule is currently active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(help_text='Company this rule belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='sharing_rules', to='core.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_sharing_rules', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sharing_rule',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RecordShare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('object_type', models.CharField(choices=[('lead', 'Lead'), ('deal', 'Deal'), ('account', 'Account'), ('contact', 'Contact'), ('activity', 'Activity')], db_index=True, help_text='Type of object being shared', max_length=50)),
                ('object_id', models.UUIDField(db_index=True, help_text='ID of the specific record being shared')),
                ('access_level', models.CharField(choices=[('read_only', 'Read Only'), ('read_write', 'Read/Write')], default='read_only', help_text='Access level granted', max_length=20)),
                ('reason', models.TextField(blank=True, help_text='Reason for sharing')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(help_text='Company this share belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='record_shares', to='core.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_record_shares', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(help_text='User being granted access', on_delete=django.db.models.deletion.CASCADE, related_name='record_shares', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'record_share',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='sharingrule',
            index=models.Index(fields=['company', 'object_type', 'is_active'], name='sharing_rul_company_9e5e6c_idx'),
        ),
        migrations.AddIndex(
            model_name='recordshare',
            index=models.Index(fields=['company', 'object_type', 'object_id'], name='record_shar_company_8a5c9d_idx'),
        ),
        migrations.AddIndex(
            model_name='recordshare',
            index=models.Index(fields=['company', 'user'], name='record_shar_company_7b6d4e_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='recordshare',
            unique_together={('company', 'object_type', 'object_id', 'user')},
        ),
    ]
