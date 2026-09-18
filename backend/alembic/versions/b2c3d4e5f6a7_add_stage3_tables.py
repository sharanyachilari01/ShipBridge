"""Add stage 3 tables (recovery_recommendations, recovery_decisions, recovery_impact_snapshots)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-19 01:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create recovery_recommendations table
    op.create_table(
        'recovery_recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.String(length=100), nullable=False),
        sa.Column('analysis_id', sa.String(length=100), nullable=True),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('selected_opportunity_id', sa.Integer(), nullable=True),
        sa.Column('recommendation_status', sa.String(length=50), server_default='PENDING_REVIEW', nullable=False),
        sa.Column('recommendation_score', sa.Float(), nullable=True),
        sa.Column('recommendation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['selected_opportunity_id'], ['recovery_opportunity_table.opportunity_id']),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment_table.shipment_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_recommendations_analysis_id'), 'recovery_recommendations', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_recovery_recommendations_id'), 'recovery_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_recovery_recommendations_recommendation_id'), 'recovery_recommendations', ['recommendation_id'], unique=True)
    op.create_index(op.f('ix_recovery_recommendations_recommendation_status'), 'recovery_recommendations', ['recommendation_status'], unique=False)
    op.create_index(op.f('ix_recovery_recommendations_shipment_id'), 'recovery_recommendations', ['shipment_id'], unique=False)

    # 2. Create recovery_decisions table
    op.create_table(
        'recovery_decisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.String(length=100), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('dispatcher_name', sa.String(length=100), nullable=False),
        sa.Column('decision_note', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recovery_recommendations.recommendation_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_decisions_id'), 'recovery_decisions', ['id'], unique=False)
    op.create_index(op.f('ix_recovery_decisions_recommendation_id'), 'recovery_decisions', ['recommendation_id'], unique=False)

    # 3. Create recovery_impact_snapshots table
    op.create_table(
        'recovery_impact_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('selected_opportunity_id', sa.Integer(), nullable=True),
        sa.Column('baseline_recovery_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('selected_recovery_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('estimated_cost_savings', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('baseline_delivery_time', sa.DateTime(), nullable=True),
        sa.Column('selected_delivery_time', sa.DateTime(), nullable=True),
        sa.Column('delivery_time_change_minutes', sa.Integer(), nullable=True),
        sa.Column('deadline_margin_minutes', sa.Integer(), nullable=True),
        sa.Column('additional_distance_km', sa.Float(), nullable=True),
        sa.Column('capacity_utilization_after', sa.Float(), nullable=True),
        sa.Column('number_of_transfers', sa.Integer(), nullable=True),
        sa.Column('impact_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['selected_opportunity_id'], ['recovery_opportunity_table.opportunity_id']),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment_table.shipment_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_impact_snapshots_id'), 'recovery_impact_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_recovery_impact_snapshots_shipment_id'), 'recovery_impact_snapshots', ['shipment_id'], unique=False)


def downgrade() -> None:
    op.drop_table('recovery_impact_snapshots')
    op.drop_table('recovery_decisions')
    op.drop_table('recovery_recommendations')
