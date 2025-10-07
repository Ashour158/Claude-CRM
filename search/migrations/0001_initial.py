# Generated migration file for search app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.contrib.postgres.fields import ArrayField


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query', models.TextField(db_index=True)),
                ('query_hash', models.CharField(db_index=True, help_text='Hash of normalized query', max_length=64)),
                ('entity_types', ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None)),
                ('results', models.JSONField(help_text='Cached search results')),
                ('result_count', models.IntegerField(default=0)),
                ('filters', models.JSONField(blank=True, help_text='Applied filters', null=True)),
                ('execution_time_ms', models.IntegerField(help_text='Query execution time in milliseconds')),
                ('hit_count', models.IntegerField(default=0, help_text='Number of times this cache was hit')),
                ('last_hit', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'search_cache',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QueryExpansion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('term', models.CharField(db_index=True, help_text='Original term', max_length=255)),
                ('expansions', ArrayField(base_field=models.CharField(max_length=255), help_text='List of synonyms and expanded forms', size=None)),
                ('term_type', models.CharField(choices=[('synonym', 'Synonym'), ('acronym', 'Acronym'), ('abbreviation', 'Abbreviation')], default='synonym', max_length=20)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('priority', models.IntegerField(default=0, help_text='Higher priority terms are applied first')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'search_query_expansion',
                'ordering': ['-priority', 'term'],
                'unique_together': {('company', 'term', 'term_type')},
            },
        ),
        migrations.CreateModel(
            name='SearchMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('query', models.TextField()),
                ('entity_type', models.CharField(blank=True, max_length=50)),
                ('result_count', models.IntegerField(default=0)),
                ('clicked_result_ids', ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, help_text='IDs of results user clicked on', size=None)),
                ('clicked_result_rank', ArrayField(base_field=models.IntegerField(), blank=True, default=list, help_text='Ranks of clicked results', size=None)),
                ('execution_time_ms', models.IntegerField()),
                ('cache_hit', models.BooleanField(default=False)),
                ('facets_applied', models.JSONField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.company')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='search_metrics', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'search_metrics',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RelationshipGraph',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_type', models.CharField(db_index=True, max_length=50)),
                ('source_id', models.CharField(db_index=True, max_length=50)),
                ('target_type', models.CharField(db_index=True, max_length=50)),
                ('target_id', models.CharField(db_index=True, max_length=50)),
                ('relationship_type', models.CharField(choices=[('converted_to', 'Converted To'), ('associated_with', 'Associated With'), ('owned_by', 'Owned By'), ('belongs_to', 'Belongs To'), ('related_to', 'Related To')], max_length=50)),
                ('weight', models.FloatField(default=1.0, help_text='Relationship strength')),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'search_relationship_graph',
                'ordering': ['-created_at'],
                'unique_together': {('source_type', 'source_id', 'target_type', 'target_id', 'relationship_type')},
            },
        ),
        migrations.AddIndex(
            model_name='searchcache',
            index=models.Index(fields=['company', 'query_hash'], name='search_cach_company_idx'),
        ),
        migrations.AddIndex(
            model_name='searchcache',
            index=models.Index(fields=['company', 'expires_at'], name='search_cach_company_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='queryexpansion',
            index=models.Index(fields=['company', 'term'], name='search_quer_company_term_idx'),
        ),
        migrations.AddIndex(
            model_name='queryexpansion',
            index=models.Index(fields=['company', 'is_active'], name='search_quer_company_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='searchmetric',
            index=models.Index(fields=['company', 'user', '-created_at'], name='search_metr_company_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='searchmetric',
            index=models.Index(fields=['company', 'entity_type', '-created_at'], name='search_metr_company_entity_created_idx'),
        ),
        migrations.AddIndex(
            model_name='relationshipgraph',
            index=models.Index(fields=['source_type', 'source_id'], name='search_rela_source_idx'),
        ),
        migrations.AddIndex(
            model_name='relationshipgraph',
            index=models.Index(fields=['target_type', 'target_id'], name='search_rela_target_idx'),
        ),
        migrations.AddIndex(
            model_name='relationshipgraph',
            index=models.Index(fields=['relationship_type'], name='search_rela_relation_idx'),
        ),
    ]
