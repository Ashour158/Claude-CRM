# Generated migration for vector search index

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Add your last migration here
    ]

    operations = [
        # Enable pgvector extension
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        ),
        
        # Create vector search index table
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS vector_search_index (
                doc_id VARCHAR(255) PRIMARY KEY,
                vector vector(768),
                metadata JSONB DEFAULT '{}',
                indexed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS vector_search_index;"
        ),
        
        # Create index for vector similarity search
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_vector_search_cosine 
            ON vector_search_index 
            USING ivfflat (vector vector_cosine_ops)
            WITH (lists = 100);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_vector_search_cosine;"
        ),
        
        # Create index on metadata
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_vector_search_metadata 
            ON vector_search_index 
            USING gin (metadata);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_vector_search_metadata;"
        ),
        
        # Create index on indexed_at
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_vector_search_indexed_at 
            ON vector_search_index (indexed_at);
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_vector_search_indexed_at;"
        ),
    ]
