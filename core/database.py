# core/database.py
# Enterprise-grade database optimization

from django.db import models, connection
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """
    Database optimization utilities for enterprise performance
    """
    
    @staticmethod
    def create_enterprise_indexes():
        """Create enterprise-grade database indexes"""
        
        indexes = [
            # Core tables indexes
            {
                'table': 'users',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_users_email ON users(email);',
                    'CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);',
                    'CREATE INDEX CONCURRENTLY idx_users_is_active ON users(is_active);',
                    'CREATE INDEX CONCURRENTLY idx_users_last_login ON users(last_login);',
                ]
            },
            {
                'table': 'companies',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_companies_code ON companies(code);',
                    'CREATE INDEX CONCURRENTLY idx_companies_is_active ON companies(is_active);',
                    'CREATE INDEX CONCURRENTLY idx_companies_created_at ON companies(created_at);',
                ]
            },
            {
                'table': 'user_company_access',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_user_company_access_user_company ON user_company_access(user_id, company_id);',
                    'CREATE INDEX CONCURRENTLY idx_user_company_access_is_active ON user_company_access(is_active);',
                    'CREATE INDEX CONCURRENTLY idx_user_company_access_role ON user_company_access(role);',
                ]
            },
            # CRM tables indexes
            {
                'table': 'accounts',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_accounts_company ON accounts(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_owner ON accounts(owner_id);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_type ON accounts(type);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_industry ON accounts(industry);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_is_active ON accounts(is_active);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_created_at ON accounts(created_at);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_name ON accounts(name);',
                    'CREATE INDEX CONCURRENTLY idx_accounts_email ON accounts(email);',
                ]
            },
            {
                'table': 'contacts',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_contacts_company ON contacts(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_account ON contacts(account_id);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_owner ON contacts(owner_id);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_email ON contacts(email);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_phone ON contacts(phone);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_is_primary ON contacts(is_primary);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_is_active ON contacts(is_active);',
                    'CREATE INDEX CONCURRENTLY idx_contacts_created_at ON contacts(created_at);',
                ]
            },
            {
                'table': 'leads',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_leads_company ON leads(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_leads_owner ON leads(owner_id);',
                    'CREATE INDEX CONCURRENTLY idx_leads_status ON leads(status);',
                    'CREATE INDEX CONCURRENTLY idx_leads_rating ON leads(rating);',
                    'CREATE INDEX CONCURRENTLY idx_leads_lead_score ON leads(lead_score);',
                    'CREATE INDEX CONCURRENTLY idx_leads_source ON leads(source);',
                    'CREATE INDEX CONCURRENTLY idx_leads_is_qualified ON leads(is_qualified);',
                    'CREATE INDEX CONCURRENTLY idx_leads_created_at ON leads(created_at);',
                ]
            },
            {
                'table': 'deals',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_deals_company ON deals(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_deals_account ON deals(account_id);',
                    'CREATE INDEX CONCURRENTLY idx_deals_owner ON deals(owner_id);',
                    'CREATE INDEX CONCURRENTLY idx_deals_stage ON deals(stage_id);',
                    'CREATE INDEX CONCURRENTLY idx_deals_status ON deals(status);',
                    'CREATE INDEX CONCURRENTLY idx_deals_amount ON deals(amount);',
                    'CREATE INDEX CONCURRENTLY idx_deals_close_date ON deals(close_date);',
                    'CREATE INDEX CONCURRENTLY idx_deals_created_at ON deals(created_at);',
                ]
            },
            {
                'table': 'activities',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_activities_company ON activities(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_activities_owner ON activities(owner_id);',
                    'CREATE INDEX CONCURRENTLY idx_activities_activity_type ON activities(activity_type);',
                    'CREATE INDEX CONCURRENTLY idx_activities_activity_date ON activities(activity_date);',
                    'CREATE INDEX CONCURRENTLY idx_activities_status ON activities(status);',
                    'CREATE INDEX CONCURRENTLY idx_activities_related_to ON activities(related_to_type, related_to_id);',
                ]
            },
            {
                'table': 'tasks',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_tasks_company ON tasks(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_tasks_assigned_to ON tasks(assigned_to_id);',
                    'CREATE INDEX CONCURRENTLY idx_tasks_due_date ON tasks(due_date);',
                    'CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status);',
                    'CREATE INDEX CONCURRENTLY idx_tasks_priority ON tasks(priority);',
                    'CREATE INDEX CONCURRENTLY idx_tasks_created_at ON tasks(created_at);',
                ]
            },
            {
                'table': 'products',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_products_company ON products(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_products_category ON products(category_id);',
                    'CREATE INDEX CONCURRENTLY idx_products_product_code ON products(product_code);',
                    'CREATE INDEX CONCURRENTLY idx_products_name ON products(name);',
                    'CREATE INDEX CONCURRENTLY idx_products_product_type ON products(product_type);',
                    'CREATE INDEX CONCURRENTLY idx_products_is_active ON products(is_active);',
                    'CREATE INDEX CONCURRENTLY idx_products_track_inventory ON products(track_inventory);',
                ]
            },
            {
                'table': 'territories',
                'indexes': [
                    'CREATE INDEX CONCURRENTLY idx_territories_company ON territories(company_id);',
                    'CREATE INDEX CONCURRENTLY idx_territories_manager ON territories(manager_id);',
                    'CREATE INDEX CONCURRENTLY idx_territories_parent ON territories(parent_id);',
                    'CREATE INDEX CONCURRENTLY idx_territories_type ON territories(type);',
                    'CREATE INDEX CONCURRENTLY idx_territories_is_active ON territories(is_active);',
                ]
            },
        ]
        
        with connection.cursor() as cursor:
            for table_config in indexes:
                table_name = table_config['table']
                logger.info(f"Creating indexes for {table_name}...")
                
                for index_sql in table_config['indexes']:
                    try:
                        cursor.execute(index_sql)
                        logger.info(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")
    
    @staticmethod
    def create_partial_indexes():
        """Create partial indexes for better performance"""
        
        partial_indexes = [
            # Active records only
            'CREATE INDEX CONCURRENTLY idx_accounts_active ON accounts(id) WHERE is_active = true;',
            'CREATE INDEX CONCURRENTLY idx_contacts_active ON contacts(id) WHERE is_active = true;',
            'CREATE INDEX CONCURRENTLY idx_leads_active ON leads(id) WHERE is_active = true;',
            'CREATE INDEX CONCURRENTLY idx_deals_open ON deals(id) WHERE status = \'open\';',
            'CREATE INDEX CONCURRENTLY idx_tasks_pending ON tasks(id) WHERE status IN (\'pending\', \'in_progress\');',
            
            # Recent records
            'CREATE INDEX CONCURRENTLY idx_activities_recent ON activities(id) WHERE activity_date >= NOW() - INTERVAL \'30 days\';',
            'CREATE INDEX CONCURRENTLY idx_deals_recent ON deals(id) WHERE created_at >= NOW() - INTERVAL \'90 days\';',
            
            # High-value deals
            'CREATE INDEX CONCURRENTLY idx_deals_high_value ON deals(id) WHERE amount > 10000;',
            
            # Overdue tasks
            'CREATE INDEX CONCURRENTLY idx_tasks_overdue ON tasks(id) WHERE due_date < NOW() AND status IN (\'pending\', \'in_progress\');',
        ]
        
        with connection.cursor() as cursor:
            for index_sql in partial_indexes:
                try:
                    cursor.execute(index_sql)
                    logger.info(f"Created partial index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create partial index: {e}")
    
    @staticmethod
    def create_materialized_views():
        """Create materialized views for complex queries"""
        
        views = [
            {
                'name': 'mv_account_stats',
                'sql': '''
                    CREATE MATERIALIZED VIEW mv_account_stats AS
                    SELECT 
                        a.company_id,
                        a.id as account_id,
                        a.name as account_name,
                        COUNT(DISTINCT c.id) as contacts_count,
                        COUNT(DISTINCT d.id) as deals_count,
                        COALESCE(SUM(d.amount), 0) as total_deal_value,
                        COALESCE(SUM(CASE WHEN d.status = 'open' THEN d.amount ELSE 0 END), 0) as open_deal_value
                    FROM accounts a
                    LEFT JOIN contacts c ON a.id = c.account_id AND c.is_active = true
                    LEFT JOIN deals d ON a.id = d.account_id
                    WHERE a.is_active = true
                    GROUP BY a.company_id, a.id, a.name;
                '''
            },
            {
                'name': 'mv_lead_conversion_stats',
                'sql': '''
                    CREATE MATERIALIZED VIEW mv_lead_conversion_stats AS
                    SELECT 
                        l.company_id,
                        l.source,
                        COUNT(*) as total_leads,
                        COUNT(CASE WHEN l.is_qualified = true THEN 1 END) as qualified_leads,
                        COUNT(CASE WHEN l.converted_at IS NOT NULL THEN 1 END) as converted_leads,
                        ROUND(
                            COUNT(CASE WHEN l.converted_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2
                        ) as conversion_rate
                    FROM leads l
                    WHERE l.is_active = true
                    GROUP BY l.company_id, l.source;
                '''
            },
            {
                'name': 'mv_sales_pipeline',
                'sql': '''
                    CREATE MATERIALIZED VIEW mv_sales_pipeline AS
                    SELECT 
                        d.company_id,
                        d.stage_id,
                        ps.name as stage_name,
                        ps.probability,
                        COUNT(*) as deals_count,
                        SUM(d.amount) as total_amount,
                        SUM(d.amount * ps.probability / 100) as weighted_amount
                    FROM deals d
                    JOIN pipeline_stages ps ON d.stage_id = ps.id
                    WHERE d.status = 'open' AND d.is_active = true
                    GROUP BY d.company_id, d.stage_id, ps.name, ps.probability;
                '''
            },
        ]
        
        with connection.cursor() as cursor:
            for view_config in views:
                try:
                    # Drop if exists
                    cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view_config['name']};")
                    # Create materialized view
                    cursor.execute(view_config['sql'])
                    logger.info(f"Created materialized view: {view_config['name']}")
                except Exception as e:
                    logger.warning(f"Failed to create materialized view {view_config['name']}: {e}")
    
    @staticmethod
    def create_database_functions():
        """Create database functions for complex operations"""
        
        functions = [
            {
                'name': 'get_company_stats',
                'sql': '''
                    CREATE OR REPLACE FUNCTION get_company_stats(company_uuid UUID)
                    RETURNS JSON AS $$
                    DECLARE
                        result JSON;
                    BEGIN
                        SELECT json_build_object(
                            'accounts_count', (SELECT COUNT(*) FROM accounts WHERE company_id = company_uuid AND is_active = true),
                            'contacts_count', (SELECT COUNT(*) FROM contacts WHERE company_id = company_uuid AND is_active = true),
                            'leads_count', (SELECT COUNT(*) FROM leads WHERE company_id = company_uuid AND is_active = true),
                            'deals_count', (SELECT COUNT(*) FROM deals WHERE company_id = company_uuid AND is_active = true),
                            'total_deal_value', (SELECT COALESCE(SUM(amount), 0) FROM deals WHERE company_id = company_uuid AND is_active = true),
                            'open_deal_value', (SELECT COALESCE(SUM(amount), 0) FROM deals WHERE company_id = company_uuid AND status = 'open' AND is_active = true)
                        ) INTO result;
                        RETURN result;
                    END;
                    $$ LANGUAGE plpgsql;
                '''
            },
            {
                'name': 'get_lead_score',
                'sql': '''
                    CREATE OR REPLACE FUNCTION get_lead_score(
                        lead_source TEXT,
                        lead_rating TEXT,
                        lead_company_size INTEGER,
                        lead_budget DECIMAL
                    ) RETURNS INTEGER AS $$
                    DECLARE
                        score INTEGER := 0;
                    BEGIN
                        -- Source scoring
                        CASE lead_source
                            WHEN 'Website' THEN score := score + 30;
                            WHEN 'Referral' THEN score := score + 40;
                            WHEN 'Cold Call' THEN score := score + 10;
                            WHEN 'Email' THEN score := score + 20;
                            ELSE score := score + 5;
                        END CASE;
                        
                        -- Rating scoring
                        CASE lead_rating
                            WHEN 'hot' THEN score := score + 30;
                            WHEN 'warm' THEN score := score + 20;
                            WHEN 'cold' THEN score := score + 10;
                            ELSE score := score + 5;
                        END CASE;
                        
                        -- Company size scoring
                        IF lead_company_size > 1000 THEN
                            score := score + 20;
                        ELSIF lead_company_size > 100 THEN
                            score := score + 15;
                        ELSIF lead_company_size > 10 THEN
                            score := score + 10;
                        ELSE
                            score := score + 5;
                        END IF;
                        
                        -- Budget scoring
                        IF lead_budget > 100000 THEN
                            score := score + 20;
                        ELSIF lead_budget > 10000 THEN
                            score := score + 15;
                        ELSIF lead_budget > 1000 THEN
                            score := score + 10;
                        ELSE
                            score := score + 5;
                        END IF;
                        
                        RETURN LEAST(score, 100);
                    END;
                    $$ LANGUAGE plpgsql;
                '''
            },
        ]
        
        with connection.cursor() as cursor:
            for func_config in functions:
                try:
                    cursor.execute(func_config['sql'])
                    logger.info(f"Created function: {func_config['name']}")
                except Exception as e:
                    logger.warning(f"Failed to create function {func_config['name']}: {e}")
    
    @staticmethod
    def optimize_database_settings():
        """Optimize database settings for enterprise performance"""
        
        optimizations = [
            # Connection settings
            "ALTER SYSTEM SET max_connections = 200;",
            "ALTER SYSTEM SET shared_buffers = '256MB';",
            "ALTER SYSTEM SET effective_cache_size = '1GB';",
            "ALTER SYSTEM SET maintenance_work_mem = '64MB';",
            "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
            "ALTER SYSTEM SET wal_buffers = '16MB';",
            "ALTER SYSTEM SET default_statistics_target = 100;",
            
            # Query optimization
            "ALTER SYSTEM SET random_page_cost = 1.1;",
            "ALTER SYSTEM SET effective_io_concurrency = 200;",
            "ALTER SYSTEM SET work_mem = '4MB';",
            
            # Logging for monitoring
            "ALTER SYSTEM SET log_min_duration_statement = 1000;",
            "ALTER SYSTEM SET log_checkpoints = on;",
            "ALTER SYSTEM SET log_connections = on;",
            "ALTER SYSTEM SET log_disconnections = on;",
            "ALTER SYSTEM SET log_lock_waits = on;",
        ]
        
        with connection.cursor() as cursor:
            for optimization in optimizations:
                try:
                    cursor.execute(optimization)
                    logger.info(f"Applied optimization: {optimization}")
                except Exception as e:
                    logger.warning(f"Failed to apply optimization: {e}")
    
    @staticmethod
    def analyze_tables():
        """Analyze tables for query optimization"""
        
        tables = [
            'users', 'companies', 'user_company_access',
            'accounts', 'contacts', 'leads', 'deals',
            'activities', 'tasks', 'events',
            'products', 'product_categories',
            'territories', 'territory_rules',
            'pipeline_stages'
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    cursor.execute(f"ANALYZE {table};")
                    logger.info(f"Analyzed table: {table}")
                except Exception as e:
                    logger.warning(f"Failed to analyze table {table}: {e}")


class DatabaseManagementCommand(BaseCommand):
    """Django management command for database optimization"""
    
    help = 'Optimize database for enterprise performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--indexes',
            action='store_true',
            help='Create enterprise indexes'
        )
        parser.add_argument(
            '--partial-indexes',
            action='store_true',
            help='Create partial indexes'
        )
        parser.add_argument(
            '--views',
            action='store_true',
            help='Create materialized views'
        )
        parser.add_argument(
            '--functions',
            action='store_true',
            help='Create database functions'
        )
        parser.add_argument(
            '--optimize',
            action='store_true',
            help='Optimize database settings'
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze tables'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations'
        )
    
    def handle(self, *args, **options):
        if options['all'] or options['indexes']:
            self.stdout.write('Creating enterprise indexes...')
            DatabaseOptimizer.create_enterprise_indexes()
        
        if options['all'] or options['partial_indexes']:
            self.stdout.write('Creating partial indexes...')
            DatabaseOptimizer.create_partial_indexes()
        
        if options['all'] or options['views']:
            self.stdout.write('Creating materialized views...')
            DatabaseOptimizer.create_materialized_views()
        
        if options['all'] or options['functions']:
            self.stdout.write('Creating database functions...')
            DatabaseOptimizer.create_database_functions()
        
        if options['all'] or options['optimize']:
            self.stdout.write('Optimizing database settings...')
            DatabaseOptimizer.optimize_database_settings()
        
        if options['all'] or options['analyze']:
            self.stdout.write('Analyzing tables...')
            DatabaseOptimizer.analyze_tables()
        
        self.stdout.write(
            self.style.SUCCESS('Database optimization completed!')
        )
