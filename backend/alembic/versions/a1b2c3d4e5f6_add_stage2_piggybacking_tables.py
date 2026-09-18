"""Add stage 2 piggybacking analysis tables and columns

Revision ID: a1b2c3d4e5f6
Revises: 96a8506ee61d
Create Date: 2026-09-19 00:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '96a8506ee61d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create piggyback_analysis_runs table if not exists
    op.create_table(
        'piggyback_analysis_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('analysis_id', sa.String(length=100), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('candidates_found_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('feasible_candidates_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('summary_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipment_table.shipment_id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_piggyback_analysis_runs_analysis_id'), 'piggyback_analysis_runs', ['analysis_id'], unique=True)
    op.create_index(op.f('ix_piggyback_analysis_runs_id'), 'piggyback_analysis_runs', ['id'], unique=False)
    op.create_index(op.f('ix_piggyback_analysis_runs_shipment_id'), 'piggyback_analysis_runs', ['shipment_id'], unique=False)

    # 2. Add columns to recovery_opportunity_table if missing
    for col in [
        sa.Column('analysis_id', sa.String(length=100), nullable=True),
        sa.Column('candidate_route_id', sa.Integer(), nullable=True),
        sa.Column('recovery_type', sa.String(length=50), nullable=True),
        sa.Column('pickup_hub_id', sa.Integer(), nullable=True),
        sa.Column('drop_hub_id', sa.Integer(), nullable=True),
        sa.Column('transfer_hub_id', sa.Integer(), nullable=True),
        sa.Column('second_vehicle_id', sa.Integer(), nullable=True),
        sa.Column('second_route_id', sa.Integer(), nullable=True),
        sa.Column('available_weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('remaining_weight_kg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('available_volume_m3', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('remaining_volume_m3', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('route_overlap_km', sa.Float(), nullable=True),
        sa.Column('detour_distance_km', sa.Float(), nullable=True),
        sa.Column('additional_time_hours', sa.Float(), nullable=True),
        sa.Column('estimated_delivery_time', sa.DateTime(), nullable=True),
        sa.Column('transfer_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('additional_transport_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('estimated_total_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('deadline_feasible', sa.Boolean(), nullable=True),
        sa.Column('deadline_margin_minutes', sa.Integer(), nullable=True),
        sa.Column('deadline_risk', sa.String(length=20), nullable=True),
        sa.Column('number_of_transfers', sa.Integer(), nullable=True),
        sa.Column('transfer_complexity', sa.String(length=20), nullable=True),
        sa.Column('piggyback_score', sa.Float(), nullable=True),
        sa.Column('score_distance', sa.Float(), nullable=True),
        sa.Column('score_time', sa.Float(), nullable=True),
        sa.Column('score_cost', sa.Float(), nullable=True),
        sa.Column('score_deadline', sa.Float(), nullable=True),
        sa.Column('score_capacity', sa.Float(), nullable=True),
        sa.Column('score_route', sa.Float(), nullable=True),
        sa.Column('score_transfer', sa.Float(), nullable=True),
        sa.Column('feasible', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('rejection_reason', sa.String(length=100), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('concerns_json', sa.Text(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
    ]:
        try:
            op.add_column('recovery_opportunity_table', col)
        except Exception:
            pass


def downgrade() -> None:
    op.drop_table('piggyback_analysis_runs')
