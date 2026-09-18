import pytest
from datetime import datetime, timedelta
from app.detection.config import DEFAULT_CONFIG, DetectionConfig
from app.detection.models_domain import (
    TelemetryPoint,
    ExpectedJourney,
    SystemContext,
    Waypoint,
    RouteGeometry,
)
from app.detection.data_validator import DataValidator
from app.detection.tier1_sentry import Tier1Sentry
from app.detection.route_matcher import RouteMatcher
from app.detection.trajectory_analyzer import TrajectoryAnalyzer, calculate_heading_difference
from app.detection.safeguard_validator import SafeguardValidator
from app.detection.score_calculator import ScoreCalculator
from app.detection.engine import MisplacementDecisionEngine
from app.database import SessionLocal
from app.detection.service import evaluate_and_persist_shipment, evaluate_all_demo_shipments
from app.seed import seed_database


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    seed_database(session, reseed_synthetic_only=False)
    yield session
    session.close()


def test_data_validator_coordinate_bounds():
    val = DataValidator()
    assert val.is_valid_coordinates(17.3850, 78.4867) is True
    assert val.is_valid_coordinates(95.0, 78.4867) is False
    assert val.is_valid_coordinates(17.3850, -190.0) is False
    assert val.is_valid_coordinates(0.0, 0.0) is False  # Null Island coordinates rejected


def test_gps_accuracy_threshold():
    val = DataValidator(DEFAULT_CONFIG)
    p_good = TelemetryPoint(lat=17.0, lng=78.0, timestamp=datetime.utcnow(), gps_accuracy_meters=10.0)
    p_limit = TelemetryPoint(lat=17.0, lng=78.0, timestamp=datetime.utcnow(), gps_accuracy_meters=50.0)
    p_bad = TelemetryPoint(lat=17.0, lng=78.0, timestamp=datetime.utcnow(), gps_accuracy_meters=50.1)

    assert val.is_gps_accuracy_valid(p_good) is True
    assert val.is_gps_accuracy_valid(p_limit) is True
    assert val.is_gps_accuracy_valid(p_bad) is False


def test_heading_difference():
    analyzer = TrajectoryAnalyzer()
    p1 = TelemetryPoint(lat=17.0, lng=78.0, speed_kmh=60.0, timestamp=datetime.utcnow(), heading_degrees=90.0)
    p2 = TelemetryPoint(lat=17.01, lng=78.01, speed_kmh=60.0, timestamp=datetime.utcnow(), heading_degrees=180.0)
    diff = analyzer.compute_heading_difference(p2, p1, 0.0)
    assert abs(diff - 180.0) < 0.1

    # Heading difference 355 deg to 5 deg = 10 deg difference
    wrap_diff = calculate_heading_difference(355.0, 5.0)
    assert abs(wrap_diff - 10.0) < 0.1


def test_low_speed_heading_ignored():
    calc = ScoreCalculator(DEFAULT_CONFIG)
    pt = TelemetryPoint(lat=17.0, lng=78.0, speed_kmh=15.0, heading_degrees=90.0, timestamp=datetime.utcnow())
    journey = ExpectedJourney(
        shipment_id="TEST",
        origin_hub_id=1, origin_code="BLR",
        destination_hub_id=2, destination_code="DEL",
        expected_next_hub_id=None,
        primary_route=RouteGeometry("R1", [Waypoint(1, "BLR", 12.0, 77.0), Waypoint(2, "DEL", 28.0, 77.0)]),
        vehicle_code="IND-TRK-101",
    )
    context = SystemContext()

    score = calc.calculate_score(0.0, 90.0, pt, journey, context)
    assert score == 0.0


def test_tier1_sentry_signal_loss():
    sentry = Tier1Sentry(DEFAULT_CONFIG)
    now = datetime.utcnow()
    recent_pt = TelemetryPoint(lat=17.0, lng=78.0, timestamp=now - timedelta(minutes=30))
    stale_pt = TelemetryPoint(lat=17.0, lng=78.0, timestamp=now - timedelta(hours=3, minutes=10))

    assert sentry.check_signal_status(recent_pt, now) is None  # None = Signal healthy
    assert sentry.check_signal_status(stale_pt, now) == "UNKNOWN_SIGNAL_MONITOR"
    assert sentry.check_signal_status(None, now) == "UNKNOWN_SIGNAL_MONITOR"


def test_transfer_grace_period():
    validator = SafeguardValidator(DEFAULT_CONFIG)
    now = datetime.utcnow()
    recent_transfer = SystemContext(
        active_vehicle_transfer=True,
        transfer_started_at=now - timedelta(minutes=10),
    )
    expired_transfer = SystemContext(
        active_vehicle_transfer=True,
        transfer_started_at=now - timedelta(minutes=20),
    )

    pt = TelemetryPoint(lat=17.0, lng=78.0, ble_gateway_id="IND-TRK-999", timestamp=now)
    journey = ExpectedJourney(
        shipment_id="TEST", origin_hub_id=1, origin_code="BLR",
        destination_hub_id=2, destination_code="DEL", expected_next_hub_id=None,
        primary_route=RouteGeometry("R1", []), vehicle_code="IND-TRK-101",
    )

    s1 = validator.evaluate(pt, journey, recent_transfer, 0.0, False, now)
    assert s1.vehicle_transfer_active is True

    s2 = validator.evaluate(pt, journey, expired_transfer, 0.0, False, now)
    assert s2.vehicle_transfer_active is False


def test_evaluate_all_10_demo_scenarios(db):
    results = evaluate_all_demo_shipments(db)
    res_map = {r["shipment_id"]: r for r in results}

    assert res_map["SH001"]["current_status"] == "NORMAL"
    assert res_map["SH002"]["current_status"] == "DELAYED"
    assert res_map["SH003"]["current_status"] == "NORMAL_REROUTED"
    assert res_map["SH004"]["current_status"] == "NORMAL"
    assert res_map["SH005"]["current_status"] == "NORMAL"
    assert res_map["SH006"]["current_status"] == "UNKNOWN_SIGNAL_MONITOR"
    assert res_map["SH007"]["current_status"] == "NORMAL"
    assert res_map["SH008"]["current_status"] == "SUSPICIOUS"
    assert res_map["SH009"]["current_status"] == "MISPLACED"
    assert res_map["SH010"]["current_status"] == "NORMAL_REROUTED"


def test_sh007_single_jitter_point_not_misplaced(db):
    res = evaluate_and_persist_shipment(db, "SH007")
    assert res.status == "NORMAL"
    assert res.status != "MISPLACED"


def test_sh009_evaluates_to_misplaced(db):
    res = evaluate_and_persist_shipment(db, "SH009")
    assert res.status == "MISPLACED"
    assert res.misplacement_score >= 0.65
    assert res.persistent_anomaly is True
