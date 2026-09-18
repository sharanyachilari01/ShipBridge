import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.database import SessionLocal
from app import models

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"]["connected"] is True
    assert data["database"]["type"] == "mysql"
    assert data["database"]["name"] == "shipbridge"
    assert "password" not in str(data)  # Security check: no credentials exposed


def test_get_hubs_endpoint():
    response = client.get("/api/hubs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 25
    cities = [h["city"] for h in data]
    assert "Bengaluru" in cities
    assert "Mumbai" in cities
    assert "Delhi" in cities
    assert "Chennai" in cities


def test_get_vehicles_endpoint():
    response = client.get("/api/vehicles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_get_shipments_endpoint():
    response = client.get("/api/shipments")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_admin_seed_reset():
    response = client.post("/api/admin/seed/reset")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_evaluations_endpoint():
    response = client.get("/api/v1/evaluations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    eval_item = data[0]
    assert "original_cost" in eval_item
    assert "recovery_cost" in eval_item
    assert "cost_saved" in eval_item
    assert "time_saved_hours" in eval_item
    assert "deadline_met" in eval_item
    assert "recovery_success_status" in eval_item
    assert "additional_distance_km" in eval_item


def test_get_exceptions_endpoint():
    response = client.get("/api/v1/exceptions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    exc_item = data[0]
    assert "exception_type" in exc_item
    assert "severity" in exc_item
    assert "detected_timestamp" in exc_item


def test_recovery_analyze_endpoint_valid():
    # Fetch a misplaced shipment ID dynamically
    misplaced_res = client.get("/api/v1/shipments/misplaced")
    assert misplaced_res.status_code == 200
    misplaced_list = misplaced_res.json()
    assert len(misplaced_list) > 0
    shipment_id = misplaced_list[0]["id"]

    response1 = client.post(f"/api/v1/recovery/analyze/{shipment_id}")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["eligible"] is True
    assert data1["shipment_id"] == shipment_id

    response2 = client.post(f"/api/recovery/analyze/{shipment_id}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["eligible"] is True


def test_recovery_analyze_endpoint_non_integer():
    response = client.post("/api/recovery/analyze/SHIPMENT_ID")
    assert response.status_code == 422
    err_detail = response.json()["detail"]
    assert any(e.get("type") == "int_parsing" for e in err_detail)


def test_recovery_analyze_endpoint_missing():
    response = client.post("/api/v1/recovery/analyze/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Shipment not found"


def test_recovery_analyze_endpoint_non_misplaced():
    # Fetch all shipments and find an ON_TRACK shipment
    shipments_res = client.get("/api/shipments")
    on_track = [s for s in shipments_res.json() if s["status"] == "ON_TRACK"]
    if on_track:
        shp_id = on_track[0]["id"]
        response = client.post(f"/api/v1/recovery/analyze/{shp_id}")
        assert response.status_code == 400
        assert response.json()["detail"] == "Shipment is not misplaced"


def test_get_misplaced_shipments_endpoints():
    res1 = client.get("/api/v1/shipments/misplaced")
    assert res1.status_code == 200
    data1 = res1.json()
    assert isinstance(data1, list)

    res2 = client.get("/api/shipments/misplaced")
    assert res2.status_code == 200
    data2 = res2.json()
    assert isinstance(data2, list)


def test_get_recovery_options_endpoints():
    misplaced_res = client.get("/api/v1/shipments/misplaced")
    misplaced_list = misplaced_res.json()
    assert len(misplaced_list) > 0
    shipment_id = misplaced_list[0]["id"]

    res1 = client.get(f"/api/v1/recovery/options/{shipment_id}")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "opportunities" in data1

    res2 = client.get(f"/api/recovery/options/{shipment_id}")
    assert res2.status_code == 200
    data2 = res2.json()
    assert "opportunities" in data2


def test_database_schema_compatibility_and_view():
    session = SessionLocal()
    try:
        # Verify query on recovery_opportunity_table
        rows1 = session.execute(text("SELECT shipment_id, vehicle_id, estimated_total_cost FROM recovery_opportunity_table")).fetchall()
        assert rows1 is not None

        # Verify query on recovery_opportunities view
        rows2 = session.execute(text("SELECT shipment_id, candidate_vehicle_id, recovery_type, piggyback_score, estimated_total_cost, deadline_feasible FROM recovery_opportunities")).fetchall()
        assert rows2 is not None
    finally:
        session.close()
