"""Initial schema with AI processing support

Revision ID: 001
Revises: 
Create Date: 2025-10-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create incentives table
    op.create_table(
        'incentives',
        sa.Column('incentive_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('ai_description', postgresql.JSON),  # JSON field for structured data
        sa.Column('document_urls', postgresql.JSON),
        sa.Column('publication_date', sa.DateTime),
        sa.Column('start_date', sa.DateTime),
        sa.Column('end_date', sa.DateTime),
        sa.Column('total_budget', sa.Numeric(15, 2)),
        sa.Column('source_link', sa.String(1000)),
        sa.Column('raw_csv_data', postgresql.JSON),  # All CSV fields for matching
        
        # AI Processing metadata
        sa.Column('ai_processing_status', sa.String(50), server_default='pending'),
        sa.Column('ai_processing_date', sa.DateTime),
        sa.Column('fields_completed_by_ai', postgresql.JSON),
        sa.Column('ai_processing_error', sa.Text),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('company_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_name', sa.String(500), nullable=False),
        sa.Column('cae_primary_label', sa.String(500)),
        sa.Column('trade_description_native', sa.Text),
        sa.Column('website', sa.String(500)),
        sa.Column('activity_sector', sa.String(200)),
        sa.Column('company_size', sa.String(50)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create incentive_company_matches table
    op.create_table(
        'incentive_company_matches',
        sa.Column('match_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incentive_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('match_score', sa.Numeric(5, 4)),
        sa.Column('match_reasons', postgresql.JSON),
        sa.Column('ranking_position', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['incentive_id'], ['incentives.incentive_id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'])
    )
    
    # Create indexes for better performance
    op.create_index('idx_incentives_status', 'incentives', ['ai_processing_status'])
    op.create_index('idx_incentives_dates', 'incentives', ['start_date', 'end_date'])
    op.create_index('idx_companies_name', 'companies', ['company_name'])
    op.create_index('idx_companies_sector', 'companies', ['activity_sector'])
    op.create_index('idx_matches_incentive', 'incentive_company_matches', ['incentive_id'])
    op.create_index('idx_matches_company', 'incentive_company_matches', ['company_id'])
    op.create_index('idx_matches_score', 'incentive_company_matches', ['match_score'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_matches_score', 'incentive_company_matches')
    op.drop_index('idx_matches_company', 'incentive_company_matches')
    op.drop_index('idx_matches_incentive', 'incentive_company_matches')
    op.drop_index('idx_companies_sector', 'companies')
    op.drop_index('idx_companies_name', 'companies')
    op.drop_index('idx_incentives_dates', 'incentives')
    op.drop_index('idx_incentives_status', 'incentives')
    
    # Drop tables
    op.drop_table('incentive_company_matches')
    op.drop_table('companies')
    op.drop_table('incentives')

