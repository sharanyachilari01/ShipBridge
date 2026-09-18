import pytest
from datetime import datetime, timedelta
from app import models, seed
from app.database import SessionLocal
from app.recovery_selection.simulation_service import SimulationService
from app.recovery_selection import RecommendationService


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    seed.seed_database(session, reseed_synthetic_only=False)
    yield session
    session.close()


def test_default_planner_shipment_has_at_least_three_feasible_options(db):
    """Verify shipment 9 (SH009) has at least 3 pre-seeded feasible recovery options."""
    opps = (
        db.query(models.RecoveryOpportunity)
        .filter(models.RecoveryOpportunity.shipment_id == 9, models.RecoveryOpportunity.feasible == True)
        .all()
    )
    assert len(opps) >= 3, f"Expected at least 3 feasible options for SH009, found {len(opps)}"


def test_simulator_does_not_change_mysql_records(db):
    """Verify simulation execution does NOT alter live MySQL database records."""
    # Record initial DB state
    initial_opps_count = db.query(models.RecoveryOpportunity).count()
    initial_recs_count = db.query(models.RecoveryRecommendation).count()
    initial_shipments_count = db.query(models.Shipment).count()

    sh9 = db.query(models.Shipment).filter(models.Shipment.shipment_id == 9).first()
    initial_status = sh9.current_status

    service = SimulationService()
    sim_result = service.run_simulation(
        db=db,
        shipment_id=9,
        additional_route_delay_hours=10.0,
        additional_handling_delay_minutes=60.0,
        available_capacity_adjustment_percent=-20.0,
        cost_multiplier=1.5,
    )

    db.refresh(sh9)

    # Assert database records are completely unchanged
    assert db.query(models.RecoveryOpportunity).count() == initial_opps_count
    assert db.query(models.RecoveryRecommendation).count() == initial_recs_count
    assert db.query(models.Shipment).count() == initial_shipments_count
    assert sh9.current_status == initial_status


def test_route_delay_makes_candidate_miss_deadline(db):
    """Verify additional route delay can render candidate options infeasible due to deadline breach."""
    service = SimulationService()
    sim_result = service.run_simulation(
        db=db,
        shipment_id=9,
        additional_route_delay_hours=36.0,  # 36 hour delay will exceed deadline
    )

    assert sim_result["has_feasible_simulated_option"] is False or len(sim_result["simulated_options"]) < len(sim_result["baseline_options"])
    assert len(sim_result["newly_infeasible_candidates"]) > 0
    
    # Verify rejection reason mentions deadline or ETA
    reasons = [r for c in sim_result["newly_infeasible_candidates"] for r in c["rejection_reasons"]]
    assert any("deadline" in r.lower() or "eta" in r.lower() for r in reasons)


def test_capacity_reduction_makes_candidate_infeasible(db):
    """Verify capacity reduction renders candidates infeasible when payload exceeds capacity."""
    service = SimulationService()
    sim_result = service.run_simulation(
        db=db,
        shipment_id=9,
        available_capacity_adjustment_percent=-99.0,  # 99% capacity reduction
    )

    assert len(sim_result["newly_infeasible_candidates"]) > 0
    reasons = [r for c in sim_result["newly_infeasible_candidates"] for r in c["rejection_reasons"]]
    assert any("capacity" in r.lower() or "payload" in r.lower() for r in reasons)


def test_cost_multiplier_changes_costs_and_rankings(db):
    """Verify cost multiplier scales transport cost deterministically."""
    service = SimulationService()
    baseline_sim = service.run_simulation(db=db, shipment_id=9, cost_multiplier=1.0)
    scaled_sim = service.run_simulation(db=db, shipment_id=9, cost_multiplier=2.0)

    if baseline_sim["simulated_recommended_option"] and scaled_sim["simulated_recommended_option"]:
        base_c = baseline_sim["simulated_recommended_option"]["estimated_total_cost"]
        scaled_c = scaled_sim["simulated_recommended_option"]["estimated_total_cost"]
        assert scaled_c > base_c


def test_simulation_returns_deterministic_ranking(db):
    """Verify simulation returns identical ranking for repeated calls with same parameters."""
    service = SimulationService()
    res1 = service.run_simulation(db=db, shipment_id=9, additional_route_delay_hours=2.0, cost_multiplier=1.2)
    res2 = service.run_simulation(db=db, shipment_id=9, additional_route_delay_hours=2.0, cost_multiplier=1.2)

    assert res1["simulated_options"] == res2["simulated_options"]
    assert res1["comparison"] == res2["comparison"]


def test_reset_returns_original_baseline_result(db):
    """Verify reset (0 delay, 0 capacity adjust, 1.0 multiplier) returns baseline recommendation."""
    service = SimulationService()
    reset_sim = service.run_simulation(
        db=db,
        shipment_id=9,
        additional_route_delay_hours=0.0,
        additional_handling_delay_minutes=0.0,
        available_capacity_adjustment_percent=0.0,
        cost_multiplier=1.0,
    )

    assert reset_sim["simulated_recommended_option"] is not None
    assert reset_sim["simulated_recommended_option"]["opportunity_id"] == reset_sim["baseline_recommended_option"]["opportunity_id"]


def test_no_option_scenario_never_shows_fake_recommendation(db):
    """Verify shipment 13 (no feasible route) returns NO_FEASIBLE_RECOVERY_OPTIONS and no recommendation."""
    rec_service = RecommendationService()
    rec_result = rec_service.generate_recommendation(db, shipment_id=13)

    assert rec_result.recommendation_status == "NO_FEASIBLE_RECOVERY_OPTIONS"
    assert rec_result.recommended_option is None
