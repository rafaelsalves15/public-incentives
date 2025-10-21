"""Restructure to 3 tables following enunciado

Revision ID: 002
Revises: 001
Create Date: 2025-10-21 12:00:00.000000

Changes:
1. Create incentives_metadata table
2. Migrate data from incentives to incentives_metadata
3. Remove extra columns from incentives table
4. Update companies table with proper schema

This follows the exact specification from the enunciado:
- incentives: ONLY 10 fields specified
- incentives_metadata: raw_csv_data + AI processing metadata
- companies: free schema as per utility
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create incentives_metadata table
    op.create_table(
        'incentives_metadata',
        sa.Column('metadata_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incentive_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('raw_csv_data', postgresql.JSON, nullable=False),
        sa.Column('ai_processing_status', sa.String(50), server_default='pending'),
        sa.Column('ai_processing_date', sa.DateTime),
        sa.Column('fields_completed_by_ai', postgresql.JSON),
        sa.Column('ai_processing_error', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['incentive_id'], ['incentives.incentive_id'], ondelete='CASCADE')
    )
    
    # Create indexes for metadata
    op.create_index('idx_metadata_incentive', 'incentives_metadata', ['incentive_id'])
    op.create_index('idx_metadata_status', 'incentives_metadata', ['ai_processing_status'])
    
    # 2. Migrate data from incentives to incentives_metadata
    op.execute("""
        INSERT INTO incentives_metadata (
            metadata_id,
            incentive_id,
            raw_csv_data,
            ai_processing_status,
            ai_processing_date,
            fields_completed_by_ai,
            ai_processing_error,
            created_at,
            updated_at
        )
        SELECT 
            gen_random_uuid(),
            incentive_id,
            raw_csv_data,
            ai_processing_status,
            ai_processing_date,
            fields_completed_by_ai,
            ai_processing_error,
            created_at,
            updated_at
        FROM incentives
        WHERE raw_csv_data IS NOT NULL
    """)
    
    # 3. Remove migrated columns from incentives table
    op.drop_column('incentives', 'raw_csv_data')
    op.drop_column('incentives', 'ai_processing_status')
    op.drop_column('incentives', 'ai_processing_date')
    op.drop_column('incentives', 'fields_completed_by_ai')
    op.drop_column('incentives', 'ai_processing_error')
    op.drop_column('incentives', 'created_at')
    op.drop_column('incentives', 'updated_at')
    
    # 4. Update companies table - add cae_primary_code
    op.add_column('companies', sa.Column('cae_primary_code', sa.String(10)))
    op.create_index('idx_companies_cae', 'companies', ['cae_primary_code'])
    
    # 5. Update companies table - rename updated_at column if needed
    # (it should already exist from previous migration, so this is just to ensure consistency)


def downgrade() -> None:
    # Reverse the migration
    
    # 1. Add columns back to incentives
    op.add_column('incentives', sa.Column('raw_csv_data', postgresql.JSON))
    op.add_column('incentives', sa.Column('ai_processing_status', sa.String(50), server_default='pending'))
    op.add_column('incentives', sa.Column('ai_processing_date', sa.DateTime))
    op.add_column('incentives', sa.Column('fields_completed_by_ai', postgresql.JSON))
    op.add_column('incentives', sa.Column('ai_processing_error', sa.Text))
    op.add_column('incentives', sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('incentives', sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # 2. Migrate data back from metadata to incentives
    op.execute("""
        UPDATE incentives i
        SET 
            raw_csv_data = m.raw_csv_data,
            ai_processing_status = m.ai_processing_status,
            ai_processing_date = m.ai_processing_date,
            fields_completed_by_ai = m.fields_completed_by_ai,
            ai_processing_error = m.ai_processing_error,
            created_at = m.created_at,
            updated_at = m.updated_at
        FROM incentives_metadata m
        WHERE i.incentive_id = m.incentive_id
    """)
    
    # 3. Drop indexes
    op.drop_index('idx_metadata_status', 'incentives_metadata')
    op.drop_index('idx_metadata_incentive', 'incentives_metadata')
    
    # 4. Drop metadata table
    op.drop_table('incentives_metadata')
    
    # 5. Remove cae_primary_code from companies
    op.drop_index('idx_companies_cae', 'companies')
    op.drop_column('companies', 'cae_primary_code')

