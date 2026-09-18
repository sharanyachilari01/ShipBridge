"""
Comprehensive test suite for Stage 2 Piggybacking & Recovery Opportunity Engine.
"""

from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session

from app import models, seed
from app.database import SessionLocal
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG
from app.piggybacking_engine.distance_calculator import haversine_km, calculate_detour_distance_km
from app.piggybacking_engine.candidate_finder import CandidateFinder
from app.piggybacking_engine.models import (
    CandidateVehicleDomain,
    CandidateHubDomain,
    CandidateRouteDomain,
    Location,
    PiggybackOptionDomain,
)
from app.piggybacking_engine.schedule_calculator import ScheduleCalculator
from app.piggybacking_engine.cost_calculator import CostCalculator
from app.piggybacking_engine.feasibility import FeasibilityChecker
from app.piggybacking_engine.scoring import OptionScorer
from app.piggybacking_engine.explanations import generate_explanation_and_concerns
from app.piggybacking_engine.engine import PiggybackingEngine


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_haversine_distance():
    # Bengaluru (12.9716, 77.5946) to Chennai (13.0827, 80.2707) is approx 290 km
    dist = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
    assert 280.0 <= dist <= 300.0


def test_candidate_vehicle_filtering():
    finder = CandidateFinder()
    vehicles = [
        CandidateVehicleDomain(vehicle_id=1, vehicle_code="V1", status="EN_ROUTE", weight_capacity_kg=10000, volume_capacity_m3=40),
        CandidateVehicleDomain(vehicle_id=2, vehicle_code="V2", status="MAINTENANCE", weight_capacity_kg=10000, volume_capacity_m3=40),
        CandidateVehicleDomain(vehicle_id=3, vehicle_code="V3", status="IDLE", weight_capacity_kg=10000, volume_capacity_m3=40),
    ]
    valid, rejected = finder.find_candidate_vehicles(vehicles)
    assert len(valid) == 2
    assert len(rejected) == 1
    assert rejected[0]["rejection_reason"] == "VEHICLE_NOT_OPERATIONAL"


def test_pickup_drop_hub_discovery():
    finder = CandidateFinder()
    shipment_loc = Location(latitude=12.9750, longitude=77.5950)  # Near Bengaluru
    hubs = [
        CandidateHubDomain(hub_id=1, code="HUB-BLR", name="Bengaluru Hub", city="BLR", state="KA", latitude=12.9716, longitude=77.5946),
        CandidateHubDomain(hub_id=2, code="HUB-DEL", name="Delhi Hub", city="DEL", state="DL", latitude=28.6139, longitude=77.2090),
    ]
    pickup_hubs = finder.find_pickup_hubs(shipment_loc, hubs)
    assert len(pickup_hubs) >= 1
    assert pickup_hubs[0][0].code == "HUB-BLR"
    assert pickup_hubs[0][1] < 1.0  # dist < 1km

    drop_hubs = finder.find_drop_hubs(destination_hub_id=2, all_hubs=hubs)
    assert len(drop_hubs) >= 1
    assert drop_hubs[0][0].code == "HUB-DEL"


def test_schedule_and_deadline_calculator():
    calc = ScheduleCalculator()
    now = datetime.utcnow()
    pickup_dl = now + timedelta(hours=3)
    delivery_dl = now + timedelta(hours=10)

    est_pickup, est_delivery, extra_hrs, margin_hrs, risk_level, rej_reason = (
        calc.calculate_schedule(now, detour_distance_km=15.0, route_overlap_km=100.0, pickup_deadline=pickup_dl, delivery_deadline=delivery_dl, num_transfers=0)
    )

    assert est_pickup > now
    assert est_delivery > est_pickup
    assert margin_hrs > 0
    assert risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert rej_reason is None


def test_cost_calculator():
    calc = CostCalculator()
    transport_cost, transfer_cost, total_cost, savings = calc.calculate_cost(
        detour_distance_km=20.0, additional_time_hours=1.0, num_transfers=1, direct_shipment_distance_km=150.0
    )

    assert transport_cost > 0
    assert transfer_cost == DEFAULT_PIGGYBACK_CONFIG.BASE_TRANSFER_FEE
    assert total_cost == transport_cost + transfer_cost
    assert savings >= 0


def test_feasibility_checker():
    checker = FeasibilityChecker()
    v = CandidateVehicleDomain(vehicle_id=1, vehicle_code="V1", status="EN_ROUTE", weight_capacity_kg=10000, volume_capacity_m3=40)

    is_feasible, rejections = checker.check_feasibility(
        vehicle=v,
        shipment_weight_kg=500.0,
        shipment_volume_m3=2.0,
        remaining_weight_capacity_kg=2000.0,
        remaining_volume_capacity_m3=10.0,
        detour_distance_km=10.0,
        additional_time_hours=0.5,
        estimated_total_cost=200.0,
        deadline_margin_hours=5.0,
        num_transfers=0,
    )

    assert is_feasible is True
    assert len(rejections) == 0

    # Test failure due to weight capacity
    is_feasible_fail, rejections_fail = checker.check_feasibility(
        vehicle=v,
        shipment_weight_kg=5000.0,
        shipment_volume_m3=2.0,
        remaining_weight_capacity_kg=1000.0,  # insufficient
        remaining_volume_capacity_m3=10.0,
        detour_distance_km=10.0,
        additional_time_hours=0.5,
        estimated_total_cost=200.0,
        deadline_margin_hours=5.0,
        num_transfers=0,
    )

    assert is_feasible_fail is False
    assert "INSUFFICIENT_WEIGHT_CAPACITY" in rejections_fail


def test_component_scorer_and_ranking():
    scorer = OptionScorer()
    now = datetime.utcnow()

    opt1 = PiggybackOptionDomain(
        candidate_id="OPT1", shipment_id=1, vehicle_id=1, vehicle_code="V1", route_id=1, route_code="R1",
        pickup_hub_id=1, pickup_hub_name="P1", drop_hub_id=2, drop_hub_name="D1", number_of_transfers=0, is_direct_piggyback=True,
        available_weight_capacity_kg=10000, remaining_weight_capacity_kg=5000, available_volume_capacity_m3=40, remaining_volume_capacity_m3=20,
        route_overlap_km=50, detour_distance_km=10, additional_time_hours=0.5, estimated_pickup_time=now, estimated_delivery_time=now + timedelta(hours=3),
        transport_cost=150, transfer_cost=0, estimated_total_cost=150, cost_savings_vs_dedicated=300, deadline_margin_hours=5, deadline_risk_level="LOW",
        transfer_complexity="DIRECT", is_feasible=True, piggyback_score=0.85
    )

    opt2 = PiggybackOptionDomain(
        candidate_id="OPT2", shipment_id=1, vehicle_id=2, vehicle_code="V2", route_id=2, route_code="R2",
        pickup_hub_id=1, pickup_hub_name="P1", drop_hub_id=2, drop_hub_name="D1", number_of_transfers=0, is_direct_piggyback=True,
        available_weight_capacity_kg=10000, remaining_weight_capacity_kg=2000, available_volume_capacity_m3=40, remaining_volume_capacity_m3=10,
        route_overlap_km=30, detour_distance_km=25, additional_time_hours=1.5, estimated_pickup_time=now, estimated_delivery_time=now + timedelta(hours=5),
        transport_cost=300, transfer_cost=0, estimated_total_cost=300, cost_savings_vs_dedicated=150, deadline_margin_hours=2, deadline_risk_level="HIGH",
        transfer_complexity="DIRECT", is_feasible=True, piggyback_score=0.60
    )

    ranked = scorer.rank_options([opt2, opt1])
    assert ranked[0].candidate_id == "OPT1"
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


def test_engine_analyze_misplaced_shipment(db_session: Session):
    # Ensure database seeded
    if db_session.query(models.Hub).count() == 0:
        seed.seed_database(db_session, reseed_synthetic_only=False)

    # Flag a shipment as misplaced
    shipment = db_session.query(models.Shipment).first()
    assert shipment is not None
    shipment.current_status = "MISPLACED"
    db_session.commit()

    engine = PiggybackingEngine()
    result = engine.analyze_shipment(db_session, shipment.shipment_id)

    assert result.eligible is True
    assert result.shipment_id == shipment.shipment_id
    assert result.total_candidates_evaluated > 0
    assert isinstance(result.opportunities, list)


def test_ineligible_shipments(db_session: Session):
    engine = PiggybackingEngine()

    # Non-existent shipment
    res1 = engine.analyze_shipment(db_session, shipment_id=999999)
    assert res1.eligible is False
    assert res1.ineligibility_reason == "SHIPMENT_NOT_FOUND"

    # Shipment not misplaced (ON_TRACK)
    shp = db_session.query(models.Shipment).first()
    if shp:
        shp.current_status = "ON_TRACK"
        db_session.commit()
        res2 = engine.analyze_shipment(db_session, shipment_id=shp.shipment_id)
        assert res2.eligible is False
        assert res2.ineligibility_reason == "SHIPMENT_NOT_ELIGIBLE"


def test_analysis_run_persistence_and_duplicate_protection(db_session: Session):
    if db_session.query(models.Hub).count() == 0:
        seed.seed_database(db_session, reseed_synthetic_only=False)

    shipment = db_session.query(models.Shipment).first()
    shipment.current_status = "MISPLACED"
    db_session.commit()

    engine = PiggybackingEngine()
    
    # Run 1
    res1 = engine.analyze_shipment(db_session, shipment.shipment_id, analysis_id=f"TEST-RUN-{shipment.shipment_id}")
    count1 = db_session.query(models.PiggybackAnalysisRun).filter(models.PiggybackAnalysisRun.analysis_id == f"TEST-RUN-{shipment.shipment_id}").count()
    assert count1 == 1

    # Run 2 with same analysis_id (re-run update)
    res2 = engine.analyze_shipment(db_session, shipment.shipment_id, analysis_id=f"TEST-RUN-{shipment.shipment_id}")
    count2 = db_session.query(models.PiggybackAnalysisRun).filter(models.PiggybackAnalysisRun.analysis_id == f"TEST-RUN-{shipment.shipment_id}").count()
    assert count2 == 1  # No duplicate error, updated existing run
