"""
Update MySQL schema for recovery_opportunity_table.
"""
from app.database import engine
from sqlalchemy import text

cols_to_add = [
    ("analysis_id", "VARCHAR(100) NULL"),
    ("candidate_route_id", "INT NULL"),
    ("recovery_type", "VARCHAR(50) NULL"),
    ("pickup_hub_id", "INT NULL"),
    ("drop_hub_id", "INT NULL"),
    ("transfer_hub_id", "INT NULL"),
    ("second_vehicle_id", "INT NULL"),
    ("second_route_id", "INT NULL"),
    ("available_weight_kg", "DECIMAL(10, 2) NULL"),
    ("remaining_weight_kg", "DECIMAL(10, 2) NULL"),
    ("available_volume_m3", "DECIMAL(10, 2) NULL"),
    ("remaining_volume_m3", "DECIMAL(10, 2) NULL"),
    ("route_overlap_km", "FLOAT NULL"),
    ("detour_distance_km", "FLOAT NULL"),
    ("additional_time_hours", "FLOAT NULL"),
    ("estimated_delivery_time", "DATETIME NULL"),
    ("transfer_cost", "DECIMAL(10, 2) NULL"),
    ("additional_transport_cost", "DECIMAL(10, 2) NULL"),
    ("estimated_total_cost", "DECIMAL(10, 2) NULL"),
    ("deadline_feasible", "TINYINT(1) NULL"),
    ("deadline_margin_minutes", "INT NULL"),
    ("deadline_risk", "VARCHAR(20) NULL"),
    ("number_of_transfers", "INT NULL"),
    ("transfer_complexity", "VARCHAR(20) NULL"),
    ("piggyback_score", "FLOAT NULL"),
    ("score_distance", "FLOAT NULL"),
    ("score_time", "FLOAT NULL"),
    ("score_cost", "FLOAT NULL"),
    ("score_deadline", "FLOAT NULL"),
    ("score_capacity", "FLOAT NULL"),
    ("score_route", "FLOAT NULL"),
    ("score_transfer", "FLOAT NULL"),
    ("feasible", "TINYINT(1) DEFAULT 1 NOT NULL"),
    ("rejection_reason", "VARCHAR(255) NULL"),
    ("explanation", "TEXT NULL"),
    ("concerns_json", "TEXT NULL"),
    ("`rank`", "INT NULL"),
]

with engine.begin() as conn:
    existing = [r[0] for r in conn.execute(text("DESCRIBE recovery_opportunity_table")).fetchall()]
    for col_name, col_def in cols_to_add:
        clean_name = col_name.replace("`", "")
        if clean_name not in existing:
            sql = f"ALTER TABLE recovery_opportunity_table ADD COLUMN {col_name} {col_def}"
            print(f"Executing: {sql}")
            conn.execute(text(sql))

print("Schema update completed successfully.")
