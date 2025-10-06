# Generated manually for WorkflowApproval model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkflowApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('workflow_run_id', models.UUIDField(help_text='Reference to workflow execution')),
                ('action_run_id', models.UUIDField(help_text='Reference to specific action run')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('approved', 'Approved'),
                        ('denied', 'Denied'),
                        ('escalated', 'Escalated'),
                        ('expired', 'Expired'),
                    ],
                    default='pending',
                    max_length=20
                )),
                ('approver_role', models.CharField(help_text='Role required to approve this action', max_length=100)),
                ('escalate_role', models.CharField(blank=True, help_text='Role to escalate to after timeout', max_length=100)),
                ('expires_at', models.DateTimeField(help_text='When this approval expires and should escalate')),
                ('resolved_at', models.DateTimeField(blank=True, help_text='When the approval was resolved (approved/denied)', null=True)),
                ('actor_id', models.UUIDField(blank=True, help_text='User who approved/denied the request', null=True)),
                ('metadata', models.JSONField(default=dict, help_text='Additional approval metadata (comments, reasons, etc.)')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workflowapproval_set', to='core.company')),
            ],
            options={
                'db_table': 'workflow_approval',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='workflowapproval',
            index=models.Index(fields=['workflow_run_id'], name='workflow_ap_workflo_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowapproval',
            index=models.Index(fields=['action_run_id'], name='workflow_ap_action__idx'),
        ),
        migrations.AddIndex(
            model_name='workflowapproval',
            index=models.Index(fields=['status'], name='workflow_ap_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workflowapproval',
            index=models.Index(fields=['expires_at'], name='workflow_ap_expires_idx'),
        ),
    ]
