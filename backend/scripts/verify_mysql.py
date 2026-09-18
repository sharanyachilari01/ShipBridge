#!/usr/bin/env python3
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text
from app.database import engine, MYSQL_DATABASE, MYSQL_HOST, MYSQL_PORT, MYSQL_USER


def verify_mysql():
    print("=" * 60)
    print("      SHIPBRIDGE MYSQL DATABASE VERIFICATION SCRIPT")
    print("=" * 60)

    print(f"Target Database : {MYSQL_DATABASE}")
    print(f"Host:Port       : {MYSQL_HOST}:{MYSQL_PORT}")
    print(f"User            : {MYSQL_USER}")

    try:
        with engine.connect() as conn:
            # 1. Verify Database Name
            db_name = conn.execute(text("SELECT DATABASE();")).scalar()
            print(f"\n[✓] Connected successfully to MySQL!")
            print(f"[✓] Active Database Name: {db_name}")

            if db_name.lower() != MYSQL_DATABASE.lower():
                print(f"[X] ERROR: Connected database '{db_name}' does not match expected '{MYSQL_DATABASE}'!")
                sys.exit(1)

            # 2. Check Tables
            tables = [t[0] for t in conn.execute(text("SHOW TABLES;")).fetchall()]
            print(f"\n[✓] Total Tables Found: {len(tables)}")

            print("\n" + "-" * 45)
            print(f"{'TABLE NAME':<32} | {'ROW COUNT':<10}")
            print("-" * 45)

            table_counts = {}
            for t_name in sorted(tables):
                count = conn.execute(text(f"SELECT COUNT(*) FROM `{t_name}`;")).scalar()
                table_counts[t_name] = count
                print(f"{t_name:<32} | {count:<10}")

            print("-" * 45)

            # Verification checks
            assert "hub_table" in table_counts and table_counts["hub_table"] >= 25, "Expected at least 25 hubs in hub_table!"
            assert "shipment_table" in table_counts and table_counts["shipment_table"] >= 5, "Expected seeded shipments in shipment_table!"
            assert "vehicle_table" in table_counts and table_counts["vehicle_table"] >= 5, "Expected seeded vehicles in vehicle_table!"
            assert "shipment_exception_table" in table_counts, "Expected shipment_exception_table to exist!"

            print("\n[SUCCESS] MySQL Database verification passed cleanly with zero errors!\n")

    except Exception as e:
        print(f"\n[X] DATABASE VERIFICATION FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    verify_mysql()
