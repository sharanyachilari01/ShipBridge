import pytest
from fastapi.testclient import TestClient
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

