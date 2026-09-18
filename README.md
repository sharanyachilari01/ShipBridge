# ShipBridge — Intelligent Shipment Recovery & Piggybacking (MySQL Edition)

ShipBridge is a full-stack logistics-manager command center for national supply chain logistics networks. It monitors intercity freight corridors, detects misplaced shipments, and recommends explainable "piggybacking" recovery plans on active transport routes to avoid expensive, high-emission dedicated recovery dispatches.

---

## Tech Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Backend**: Python 3.13+, FastAPI, SQLAlchemy, Alembic, PyMySQL
- **Database**: MySQL 8.0+ / 9.0+ (`shipbridge` database)
- **Maps**: React Leaflet with OpenStreetMap tiles (No API key required)
- **Charts**: Recharts

---

## Environment Configuration

Environment configuration is managed strictly via `backend/.env`.

1. Copy the environment template:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` with your MySQL server credentials:
   ```env
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_DATABASE=shipbridge
   MYSQL_USER=your_user
   MYSQL_PASSWORD=your_password
   ```

*(Note: `backend/.env` is ignored by Git to protect sensitive credentials.)*

---

## Quick Start Guide (macOS / Linux)

### 1. Database Setup & Alembic Migrations

Ensure your MySQL server is running and the database `shipbridge` exists:

```sql
CREATE DATABASE IF NOT EXISTS shipbridge;
```

Navigate to `backend` and run Alembic database migrations:

```bash
cd backend

# Create virtual environment & install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations against MySQL
alembic upgrade head
```

---

### 2. Seed Synthetic Demo Network (India Logistics Network)

To populate 26 major Indian logistics hubs, active freight corridors, vehicles, telemetry, and synthetic demo shipments:

```bash
python -c "from app.database import SessionLocal; from app.seed import seed_database; db = SessionLocal(); seed_database(db); db.close()"
```

Or trigger re-seeding via API:
```bash
curl -X POST http://127.0.0.1:8000/api/admin/seed/reset
```

---

### 3. Verify MySQL Database Installation

Run the verification script to validate MySQL connection, database name, Alembic migrations, tables, and row counts:

```bash
python scripts/verify_mysql.py
```

---

### 4. Run Backend Tests

Execute the Pytest test suite:

```bash
pytest -o pythonpath=. tests/
```

---

### 5. Start Backend FastAPI Server

```bash
uvicorn app.main:app --reload --port 8000
```

Check API health at: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

### 6. Start Frontend React Application

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Core Navigation Tabs & Features

1. **Map**: Interactive OpenStreetMap centered on India displaying 26 major Logistics Hubs, 3D Isometric Dark Cargo Truck markers, Misplaced Shipment alerts (Red), and interactive Legend.
2. **Recovery Queue**: Misplaced shipment queue with explainable piggyback recommendation cards and 1-click recovery confirmation.
3. **Planner**: Side-by-side trade-off matrix comparing Traditional Dedicated Recovery Truck vs Piggyback Recovery.
4. **Impact**: Visual analytics tracking total cost savings, carbon offset (kg CO2), and recovery success rates.
5. **Add Shipment**: Form to register new shipments and test misplacement simulation.
# ShipBridge
