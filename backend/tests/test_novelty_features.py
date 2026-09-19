import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import models

client = TestClient(app)

def test_at_risk_alerts_endpoint():
    response = client.get("/api/alerts/at-risk")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    first_alert = data[0]
    assert "alert_id" in first_alert
    assert "shipment_id" in first_alert
    assert "risk_level" in first_alert
    assert "reasons" in first_alert
    assert len(first_alert["reasons"]) > 0


def test_sh009_multi_option_recovery():
    db = SessionLocal()
    try:
        opps = db.query(models.RecoveryOpportunity).filter(
            models.RecoveryOpportunity.shipment_id == 9,
            models.RecoveryOpportunity.feasible == True
        ).all()
        assert len(opps) >= 3
        types = {o.recovery_type for o in opps}
        assert "DIRECT_PIGGYBACK" in types or 0 in {o.number_of_transfers for o in opps}
    finally:
        db.close()


def test_sh013_no_feasible_option():
    db = SessionLocal()
    try:
        opps = db.query(models.RecoveryOpportunity).filter(
            models.RecoveryOpportunity.shipment_id == 13,
            models.RecoveryOpportunity.feasible == True
        ).all()
        assert len(opps) == 0
        
        all_opps = db.query(models.RecoveryOpportunity).filter(
            models.RecoveryOpportunity.shipment_id == 13
        ).all()
        assert len(all_opps) >= 1
        assert all_opps[0].feasible == False
        assert "Srinagar" in all_opps[0].explanation or "corridor" in all_opps[0].explanation
    finally:
        db.close()


def test_dispatcher_alternative_approval():
    rec_res = client.post("/api/recovery/recommend/9")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    rec_id = rec_data["recommendation_id"]
    
    opp_id = rec_data["recommended_option"]["opportunity_id"] if rec_data.get("recommended_option") else 1
    if rec_data.get("alternative_options") and len(rec_data["alternative_options"]) > 0:
        opp_id = rec_data["alternative_options"][0]["opportunity_id"]

    app_res = client.post(
        f"/api/recovery/recommendations/{rec_id}/approve",
        json={
            "dispatcher_name": "Senior Dispatcher",
            "decision_note": "Approved selected route piggyback",
            "selected_opportunity_id": opp_id
        }
    )
    assert app_res.status_code == 200
    app_data = app_res.json()
    assert app_data["status"] == "APPROVED"
    assert app_data["shipment_status"] == "RECOVERY_APPROVED"
    assert app_data["selected_opportunity_id"] == opp_id


def test_what_if_simulation_hub_closure():
    sim_res = client.post(
        "/api/recovery/simulate/9",
        json={
            "transfer_hub_unavailable": "HUB-LKO"
        }
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["shipment_id"] == 9
    assert "simulated_options" in sim_data
    # Check that any option involving HUB-LKO is filtered or marked infeasible
    infeasible_reasons = [c["rejection_reasons"] for c in sim_data["newly_infeasible_candidates"]]
    hub_closed_reasons = [r for sub in infeasible_reasons for r in sub if "unavailable due to simulated hub closure" in r]
    assert len(hub_closed_reasons) >= 1
