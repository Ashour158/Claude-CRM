# Generated migration for search indexes

from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('crm', '0001_initial'),  # Assuming CRM has migrations
    ]

    operations = [
        # Enable pg_trgm extension for trigram matching
        TrigramExtension(),
        
        # Run SQL to create search indexes
        migrations.RunSQL(
            sql="""
            -- Trigram indexes for fuzzy matching on Accounts
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_name_trgm 
                ON crm_account USING gin (name gin_trgm_ops);
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_email_trgm 
                ON crm_account USING gin (email gin_trgm_ops);
            
            -- Trigram indexes for fuzzy matching on Contacts
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_fullname_trgm 
                ON crm_contact USING gin (full_name gin_trgm_ops);
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_email_trgm 
                ON crm_contact USING gin (email gin_trgm_ops);
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_phone_trgm 
                ON crm_contact USING gin (phone gin_trgm_ops);
            
            -- Trigram indexes for fuzzy matching on Leads
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_fullname_trgm 
                ON crm_lead USING gin (full_name gin_trgm_ops);
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_company_trgm 
                ON crm_lead USING gin (company_name gin_trgm_ops);
            
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_email_trgm 
                ON crm_lead USING gin (email gin_trgm_ops);
            
            -- Full-text search indexes for Accounts
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_fts 
                ON crm_account USING gin (
                    to_tsvector('english', 
                        coalesce(name, '') || ' ' || 
                        coalesce(email, '') || ' ' ||
                        coalesce(description, '') || ' ' ||
                        coalesce(industry, '')
                    )
                );
            
            -- Full-text search indexes for Contacts
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contacts_fts 
                ON crm_contact USING gin (
                    to_tsvector('english', 
                        coalesce(full_name, '') || ' ' || 
                        coalesce(email, '') || ' ' ||
                        coalesce(title, '') || ' ' ||
                        coalesce(department, '')
                    )
                );
            
            -- Full-text search indexes for Leads
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_fts 
                ON crm_lead USING gin (
                    to_tsvector('english', 
                        coalesce(full_name, '') || ' ' || 
                        coalesce(company_name, '') || ' ' ||
                        coalesce(email, '') || ' ' ||
                        coalesce(industry, '') || ' ' ||
                        coalesce(description, '')
                    )
                );
            
            -- Analyze tables for query optimization
            ANALYZE crm_account;
            ANALYZE crm_contact;
            ANALYZE crm_lead;
            """,
            reverse_sql="""
            -- Drop search indexes
            DROP INDEX CONCURRENTLY IF EXISTS idx_accounts_name_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_accounts_email_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_contacts_fullname_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_contacts_email_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_contacts_phone_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_leads_fullname_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_leads_company_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_leads_email_trgm;
            DROP INDEX CONCURRENTLY IF EXISTS idx_accounts_fts;
            DROP INDEX CONCURRENTLY IF EXISTS idx_contacts_fts;
            DROP INDEX CONCURRENTLY IF EXISTS idx_leads_fts;
            """
        ),
    ]
