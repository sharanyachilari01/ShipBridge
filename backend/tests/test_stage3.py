"""
Comprehensive test suite for Stage 3: Feasible Option Selection + Impact Analysis.
"""

from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session

from app import models, seed
from app.database import SessionLocal
from app.recovery_selection.config import Stage3Config, DEFAULT_STAGE3_CONFIG
from app.recovery_selection.models import (
    EvaluatedOptionDomain,
    Stage3ImpactMetrics,
    Stage3ComponentScores,
)
from app.recovery_selection.impact_calculator import ImpactCalculator
from app.recovery_selection.selection_engine import SelectionEngine
from app.recovery_selection.recommendation_service import RecommendationService
from app.recovery_selection.decision_service import DecisionService
from app.recovery_selection.repositories import SelectionRepository
from app.piggybacking_engine.engine import PiggybackingEngine


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_impact_calculator():
    calc = ImpactCalculator()
    now = datetime.utcnow()
    deadline = now + timedelta(hours=8)
    estimated_delivery = now + timedelta(hours=3)

    impact = calc.calculate_impact(
        shipment_weight_kg=250.0,
        shipment_volume_m3=1.2,
        delivery_deadline=deadline,
        estimated_total_cost=120.0,
        estimated_delivery_time=estimated_delivery,
        deadline_margin_minutes=300,
        detour_distance_km=15.0,
        additional_time_hours=0.5,
        number_of_transfers=0,
        transfer_complexity="DIRECT",
        deadline_risk="LOW",
        available_weight_kg=10000.0,
        remaining_weight_kg=5000.0,
        available_volume_m3=40.0,
        remaining_volume_m3=20.0,
    )

    assert impact.baseline_recovery_cost == 1500.0
    assert impact.selected_recovery_cost == 120.0
    assert impact.estimated_cost_savings == 1380.0
    assert impact.deadline_margin_minutes == 300
    assert impact.capacity_utilization_after_percent == 50.0
    assert impact.is_high_capacity_utilization is False


def test_selection_engine_ranking_and_scores():
    engine = SelectionEngine()
    now = datetime.utcnow()

    opt1 = EvaluatedOptionDomain(
        opportunity_id=1,
        shipment_id=10,
        vehicle_id=101,
        vehicle_code="V-101",
        route_id=1,
        route_code="R-01",
        pickup_hub_id=1,
        pickup_hub_name="Hub A",
        drop_hub_id=2,
        drop_hub_name="Hub B",
        is_direct_piggyback=True,
        number_of_transfers=0,
        estimated_total_cost=100.0,
        estimated_delivery_time=now + timedelta(hours=3),
        deadline_margin_minutes=360,
        stage2_piggyback_score=0.90,
        remaining_weight_capacity_kg=5000.0,
        remaining_volume_capacity_m3=20.0,
    )

    opt2 = EvaluatedOptionDomain(
        opportunity_id=2,
        shipment_id=10,
        vehicle_id=102,
        vehicle_code="V-102",
        route_id=2,
        route_code="R-02",
        pickup_hub_id=1,
        pickup_hub_name="Hub A",
        drop_hub_id=2,
        drop_hub_name="Hub B",
        is_direct_piggyback=False,
        number_of_transfers=1,
        estimated_total_cost=400.0,
        estimated_delivery_time=now + timedelta(hours=6),
        deadline_margin_minutes=120,
        stage2_piggyback_score=0.60,
        remaining_weight_capacity_kg=2000.0,
        remaining_volume_capacity_m3=10.0,
    )

    ranked = engine.evaluate_and_rank_options(
        shipment_weight_kg=200.0,
        shipment_volume_m3=1.0,
        shipment_priority="HIGH",
        raw_options=[opt2, opt1],
    )

    assert len(ranked) == 2
    assert ranked[0].opportunity_id == 1
    assert ranked[0].rank == 1
    assert ranked[0].designation == "RECOMMENDED"
    assert ranked[0].selection_score > ranked[1].selection_score
    assert 0.0 <= ranked[0].selection_score <= 1.0


def test_feasibility_filtering_in_stage3():
    engine = SelectionEngine()
    now = datetime.utcnow()

    opt_tight = EvaluatedOptionDomain(
        opportunity_id=1,
        shipment_id=10,
        vehicle_id=101,
        vehicle_code="V-101",
        route_id=1,
        route_code="R-01",
        pickup_hub_id=1,
        pickup_hub_name="Hub A",
        drop_hub_id=2,
        drop_hub_name="Hub B",
        is_direct_piggyback=True,
        number_of_transfers=0,
        estimated_total_cost=100.0,
        estimated_delivery_time=now + timedelta(hours=10),
        deadline_margin_minutes=-10,  # Negative deadline margin (infeasible)
        stage2_piggyback_score=0.90,
        remaining_weight_capacity_kg=5000.0,
        remaining_volume_capacity_m3=20.0,
    )

    opt_overcapacity = EvaluatedOptionDomain(
        opportunity_id=2,
        shipment_id=10,
        vehicle_id=102,
        vehicle_code="V-102",
        route_id=2,
        route_code="R-02",
        pickup_hub_id=1,
        pickup_hub_name="Hub A",
        drop_hub_id=2,
        drop_hub_name="Hub B",
        is_direct_piggyback=True,
        number_of_transfers=0,
        estimated_total_cost=100.0,
        estimated_delivery_time=now + timedelta(hours=2),
        deadline_margin_minutes=200,
        stage2_piggyback_score=0.85,
        remaining_weight_capacity_kg=100.0,  # Only 100kg left for 500kg shipment
        remaining_volume_capacity_m3=20.0,
    )

    ranked = engine.evaluate_and_rank_options(
        shipment_weight_kg=500.0,
        shipment_volume_m3=1.0,
        shipment_priority="NORMAL",
        raw_options=[opt_tight, opt_overcapacity],
    )

    assert len(ranked) == 0  # Both filtered out


def test_recommendation_and_decision_pipeline(db_session: Session):
    # Ensure DB seeded
    if db_session.query(models.Hub).count() == 0:
        seed.seed_database(db_session, reseed_synthetic_only=False)

    # Set up misplaced shipment
    shipment = db_session.query(models.Shipment).first()
    assert shipment is not None
    shipment.current_status = "MISPLACED"
    db_session.commit()

    # Step 1: Run Stage 2 to discover feasible recovery opportunities
    piggyback_engine = PiggybackingEngine()
    stage2_result = piggyback_engine.analyze_shipment(db_session, shipment.shipment_id)
    assert stage2_result.eligible is True

    # Step 2: Run Stage 3 recommendation service
    service = RecommendationService()
    rec_result = service.generate_recommendation(db_session, shipment.shipment_id)

    assert rec_result.shipment_id == shipment.shipment_id
    assert rec_result.recommendation_status in ["PENDING_REVIEW", "NO_FEASIBLE_RECOVERY_OPTIONS"]

    if rec_result.recommendation_status == "PENDING_REVIEW":
        assert rec_result.recommended_option is not None
        assert rec_result.recommended_option.rank == 1
        assert rec_result.recommended_option.designation == "RECOMMENDED"

        # Step 3: Approve recommendation via DecisionService
        rec_id = rec_result.recommendation_id
        dec_resp = DecisionService.approve_recommendation(
            db=db_session,
            recommendation_id=rec_id,
            dispatcher_name="Dispatcher Tests",
            decision_note="Approved optimal route piggyback",
        )

        assert dec_resp["status"] == "APPROVED"
        assert dec_resp["shipment_status"] == "RECOVERY_APPROVED"

        # Verify shipment status in DB updated to RECOVERY_APPROVED
        db_session.refresh(shipment)
        assert shipment.current_status == "RECOVERY_APPROVED"


def test_rejection_decision_pipeline(db_session: Session):
    if db_session.query(models.Hub).count() == 0:
        seed.seed_database(db_session, reseed_synthetic_only=False)

    # Find or set a misplaced shipment
    shipments = db_session.query(models.Shipment).all()
    shipment = shipments[1] if len(shipments) > 1 else shipments[0]
    shipment.current_status = "MISPLACED"
    db_session.commit()

    # Run Stage 2
    piggyback_engine = PiggybackingEngine()
    piggyback_engine.analyze_shipment(db_session, shipment.shipment_id)

    # Run Stage 3
    service = RecommendationService()
    rec_result = service.generate_recommendation(db_session, shipment.shipment_id)

    if rec_result.recommendation_status == "PENDING_REVIEW":
        rec_id = rec_result.recommendation_id
        dec_resp = DecisionService.reject_recommendation(
            db=db_session,
            recommendation_id=rec_id,
            dispatcher_name="Dispatcher Rejecter",
            decision_note="Cost too high for budget",
        )

        assert dec_resp["recommendation_status"] == "REJECTED"
        assert dec_resp["shipment_status"] == "MISPLACED"

        # Verify shipment status remains MISPLACED
        db_session.refresh(shipment)
        assert shipment.current_status == "MISPLACED"


def test_dashboard_metrics_aggregation(db_session: Session):
    metrics = SelectionRepository.get_dashboard_metrics(db_session)
    assert "total_misplaced_shipments" in metrics
    assert "shipments_with_feasible_options" in metrics
    assert "pending_reviews_count" in metrics
    assert "total_estimated_cost_savings" in metrics
    assert "manager_briefing" in metrics
    assert metrics["is_synthetic_estimate"] is True
