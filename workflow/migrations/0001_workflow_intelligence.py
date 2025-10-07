# Generated migration for workflow intelligence models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '__first__'),
    ]

    operations = [
        # Add version and graph_spec to ProcessTemplate
        migrations.AddField(
            model_name='processtemplate',
            name='version',
            field=models.CharField(default='1.0.0', help_text='Template version', max_length=50),
        ),
        migrations.AddField(
            model_name='processtemplate',
            name='graph_spec',
            field=models.JSONField(default=dict, help_text='Graph specification for workflow visualization'),
        ),
        
        # Create ActionCatalog model
        migrations.CreateModel(
            name='ActionCatalog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('action_type', models.CharField(max_length=100)),
                ('is_idempotent', models.BooleanField(default=False, help_text='Action can be safely retried without side effects')),
                ('latency_class', models.CharField(choices=[('instant', 'Instant (< 100ms)'), ('fast', 'Fast (< 1s)'), ('medium', 'Medium (1-5s)'), ('slow', 'Slow (5-30s)'), ('very_slow', 'Very Slow (> 30s)')], default='medium', help_text='Expected execution latency', max_length=20)),
                ('side_effects', models.JSONField(default=list, help_text='List of side effects this action produces')),
                ('input_schema', models.JSONField(default=dict, help_text='JSON schema for action inputs')),
                ('output_schema', models.JSONField(default=dict, help_text='JSON schema for action outputs')),
                ('execution_count', models.IntegerField(default=0)),
                ('avg_execution_time_ms', models.IntegerField(blank=True, null=True)),
                ('success_rate', models.FloatField(default=1.0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_global', models.BooleanField(default=False, help_text='Available to all companies')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='action_catalogs', to='core.company')),
            ],
            options={
                'db_table': 'action_catalog',
                'ordering': ['name'],
            },
        ),
        
        # Create WorkflowSuggestion model
        migrations.CreateModel(
            name='WorkflowSuggestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('source', models.CharField(choices=[('historical', 'Historical Mining'), ('llm', 'LLM Auto-Suggest'), ('pattern', 'Pattern Recognition'), ('user', 'User Created')], default='historical', max_length=20)),
                ('workflow_template', models.JSONField(default=dict, help_text='Suggested workflow configuration')),
                ('confidence_score', models.FloatField(default=0.0, help_text='Confidence score (0-1)')),
                ('supporting_data', models.JSONField(default=dict, help_text='Historical data supporting this suggestion')),
                ('pattern_frequency', models.IntegerField(default=0, help_text='How often this pattern occurred')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('implemented', 'Implemented')], default='pending', max_length=20)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('review_notes', models.TextField(blank=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_suggestions', to='core.company')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_suggestions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'workflow_suggestion',
                'ordering': ['-confidence_score', '-created_at'],
            },
        ),
        
        # Create WorkflowSimulation model
        migrations.CreateModel(
            name='WorkflowSimulation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('input_data', models.JSONField(default=dict, help_text='Input data for simulation')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('execution_path', models.JSONField(default=list, help_text='Simulated execution path')),
                ('branch_explorations', models.JSONField(default=list, help_text='All explored branches')),
                ('approval_chain', models.JSONField(default=list, help_text='Simulated approval chain')),
                ('predicted_duration_ms', models.IntegerField(blank=True, null=True)),
                ('validation_errors', models.JSONField(default=list, help_text='Validation errors found during simulation')),
                ('warnings', models.JSONField(default=list, help_text='Warnings generated during simulation')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_simulations', to='core.company')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_simulations', to=settings.AUTH_USER_MODEL)),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='simulations', to='workflow.workflow')),
            ],
            options={
                'db_table': 'workflow_simulation',
                'ordering': ['-started_at'],
            },
        ),
        
        # Create WorkflowSLA model
        migrations.CreateModel(
            name='WorkflowSLA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('target_duration_seconds', models.IntegerField(help_text='Target completion time in seconds')),
                ('warning_threshold_seconds', models.IntegerField(help_text='Warning threshold in seconds')),
                ('critical_threshold_seconds', models.IntegerField(help_text='Critical threshold in seconds')),
                ('slo_window_hours', models.IntegerField(default=24, help_text='SLO evaluation window in hours')),
                ('slo_target_percentage', models.FloatField(default=99.0, help_text='Target percentage of requests meeting SLA')),
                ('is_active', models.BooleanField(default=True)),
                ('total_executions', models.IntegerField(default=0)),
                ('breached_executions', models.IntegerField(default=0)),
                ('current_slo_percentage', models.FloatField(default=100.0)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflow_slas', to='core.company')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slas', to='workflow.workflow')),
            ],
            options={
                'db_table': 'workflow_sla',
                'ordering': ['workflow', 'name'],
            },
        ),
        
        # Create SLABreach model
        migrations.CreateModel(
            name='SLABreach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('severity', models.CharField(choices=[('warning', 'Warning'), ('critical', 'Critical')], max_length=20)),
                ('actual_duration_seconds', models.IntegerField()),
                ('target_duration_seconds', models.IntegerField()),
                ('breach_margin_seconds', models.IntegerField(help_text='How much the SLA was exceeded')),
                ('alert_sent', models.BooleanField(default=False)),
                ('alert_sent_at', models.DateTimeField(blank=True, null=True)),
                ('alert_recipients', models.JSONField(default=list, help_text='List of users/emails notified')),
                ('acknowledged', models.BooleanField(default=False)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('detected_at', models.DateTimeField(auto_now_add=True)),
                ('acknowledged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_breaches', to=settings.AUTH_USER_MODEL)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sla_breaches', to='core.company')),
                ('sla', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='breaches', to='workflow.workflowsla')),
                ('workflow_execution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sla_breaches', to='workflow.workflowexecution')),
            ],
            options={
                'db_table': 'sla_breach',
                'ordering': ['-detected_at'],
            },
        ),
    ]
