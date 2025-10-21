"""add_ai_cost_tracking_table

Revision ID: e881bbc2a67b
Revises: 002
Create Date: 2025-10-21 17:19:58.694129

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e881bbc2a67b'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_cost_tracking table
    op.create_table(
        'ai_cost_tracking',
        sa.Column('tracking_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incentive_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('operation_type', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('input_cost', sa.Numeric(10, 6), nullable=False),
        sa.Column('output_cost', sa.Numeric(10, 6), nullable=False),
        sa.Column('total_cost', sa.Numeric(10, 6), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('success', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['incentive_id'], ['incentives.incentive_id'], ondelete='CASCADE'),
    )
    
    # Create indexes for better query performance
    op.create_index('idx_ai_cost_tracking_incentive_id', 'ai_cost_tracking', ['incentive_id'])
    op.create_index('idx_ai_cost_tracking_operation_type', 'ai_cost_tracking', ['operation_type'])
    op.create_index('idx_ai_cost_tracking_created_at', 'ai_cost_tracking', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_ai_cost_tracking_created_at', table_name='ai_cost_tracking')
    op.drop_index('idx_ai_cost_tracking_operation_type', table_name='ai_cost_tracking')
    op.drop_index('idx_ai_cost_tracking_incentive_id', table_name='ai_cost_tracking')
    
    # Drop table
    op.drop_table('ai_cost_tracking')
