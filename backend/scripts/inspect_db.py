import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text
from app.database import engine

def inspect_all():
    with engine.connect() as conn:
        res = conn.execute(text("SHOW TABLES;")).fetchall()
        tables = [r[0] for r in res]
        print("ALL TABLES IN SHIPBRIDGE DB:", tables)
        for tbl in tables:
            print(f"\n=== TABLE: {tbl} ===")
            cols = conn.execute(text(f"DESCRIBE `{tbl}`;")).fetchall()
            for col in cols:
                print(f"  {col[0]:<30} | {col[1]:<20} | Null:{col[2]:<4} | Key:{col[3]:<4} | Default:{col[4]}")

if __name__ == "__main__":
    inspect_all()
