import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from app import models
from app.detection.models_domain import (
    Waypoint,
    RouteGeometry,
    ExpectedJourney,
    TelemetryPoint,
    SystemContext,
    SafeguardOutcomes,
    DetectionResultDomain,
)
from app.detection.config import DEFAULT_CONFIG, DetectionConfig
from app.detection.engine import MisplacementDecisionEngine


def load_shipment_domain_data(db: Session, shipment_id_or_code: Union[int, str]):
    """
    Loads domain dataclasses (ExpectedJourney, TelemetryPoint history, SystemContext)
    for a given shipment identifier from MySQL tables.
    """
    if isinstance(shipment_id_or_code, int) or (isinstance(shipment_id_or_code, str) and shipment_id_or_code.isdigit()):
        shp = db.query(models.Shipment).filter(models.Shipment.shipment_id == int(shipment_id_or_code)).first()
    else:
        code = str(shipment_id_or_code).strip()
        shp = db.query(models.Shipment).filter(
            (models.Shipment.tracking_number == code) |
            (models.Shipment.tracking_number == f"SB-IND-{code}")
        ).first()

    if not shp:
        return None, None, None, [], None

    origin = shp.origin_hub
    destination = shp.destination_hub
    expected_next = shp.expected_next_hub or origin
    vehicle = shp.assigned_vehicle

    # Primary route waypoints
    primary_waypoints = []
    routes = db.query(models.RouteNetwork).filter(models.RouteNetwork.active == True).all()
    primary_route_code = "RTE-PRIMARY"

    for r in routes:
        if r.origin_hub_id == shp.origin_id and r.destination_hub_id == shp.destination_id:
            primary_route_code = r.route_code
            try:
                wps_raw = json.loads(r.route_geometry_json)
                primary_waypoints = [
                    Waypoint(
                        hub_id=w.get("hub_id"),
                        hub_name=w.get("hub_name", f"Hub-{idx+1}"),
                        lat=float(w["lat"]),
                        lng=float(w["lng"]),
                        sequence=w.get("sequence", idx + 1),
                    )
                    for idx, w in enumerate(wps_raw)
                ]
            except Exception:
                pass
            break

    if not primary_waypoints:
        primary_waypoints = [
            Waypoint(hub_id=origin.hub_id if origin else 1, hub_name=origin.name if origin else "BLR", lat=float(origin.latitude) if origin else 12.9716, lng=float(origin.longitude) if origin else 77.5946, sequence=1),
            Waypoint(hub_id=2, hub_name="HUB-HYD", lat=17.3850, lng=78.4867, sequence=2),
            Waypoint(hub_id=3, hub_name="HUB-NAG", lat=21.1458, lng=79.0882, sequence=3),
            Waypoint(hub_id=destination.hub_id if destination else 4, hub_name=destination.name if destination else "DEL", lat=float(destination.latitude) if destination else 28.6139, lng=float(destination.longitude) if destination else 77.2090, sequence=4),
        ]

    primary_route_geom = RouteGeometry(route_code=primary_route_code, waypoints=primary_waypoints)

    # Alternative routes
    allowed_alt_routes = []
    for r in routes:
        if r.route_code == "RTE-BOM-PNQ-AMD":
            try:
                wps_raw = json.loads(r.route_geometry_json)
                wps = [
                    Waypoint(
                        hub_id=w.get("hub_id"),
                        hub_name=w.get("hub_name", f"Hub-{idx+1}"),
                        lat=float(w["lat"]),
                        lng=float(w["lng"]),
                        sequence=w.get("sequence", idx + 1),
                    )
                    for idx, w in enumerate(wps_raw)
                ]
                allowed_alt_routes.append(RouteGeometry(route_code=r.route_code, waypoints=wps))
            except Exception:
                pass

    journey = ExpectedJourney(
        shipment_id=shp.tracking_number.replace("SB-IND-", "") if shp.tracking_number else str(shp.shipment_id),
        origin_hub_id=origin.hub_id if origin else 1,
        origin_code=origin.code if origin else "HUB-BLR",
        destination_hub_id=destination.hub_id if destination else 2,
        destination_code=destination.code if destination else "HUB-DEL",
        expected_next_hub_id=expected_next.hub_id if expected_next else None,
        primary_route=primary_route_geom,
        allowed_alternative_routes=allowed_alt_routes,
        assigned_vehicle_id=vehicle.vehicle_id if vehicle else None,
        vehicle_code=vehicle.vehicle_code if vehicle else "IND-TRK-101",
        expected_arrival_time=shp.created_timestamp + timedelta(hours=12),
        delivery_deadline=shp.delivery_deadline,
    )

    # Telemetry history
    tracking_records = (
        db.query(models.ShipmentTracking)
        .filter(models.ShipmentTracking.shipment_id == shp.shipment_id)
        .order_by(models.ShipmentTracking.timestamp.asc())
        .all()
    )

    telemetry_history = []
    for trk in tracking_records:
        if trk.current_lat is not None and trk.current_lng is not None:
            telemetry_history.append(
                TelemetryPoint(
                    lat=float(trk.current_lat),
                    lng=float(trk.current_lng),
                    timestamp=trk.timestamp,
                    speed_kmh=float(trk.speed_kmh or 0.0),
                    heading_degrees=float(trk.heading_degrees or 0.0),
                    gps_accuracy_meters=float(trk.gps_accuracy_meters or 5.0),
                    ble_gateway_id=trk.ble_gateway_id or "",
                    tracking_available=trk.tracking_available,
                )
            )

    latest_telemetry = telemetry_history[-1] if telemetry_history else None

    # Context
    approved_reroute = False
    exec_rec = db.query(models.RecoveryExecution).filter(models.RecoveryExecution.shipment_id == shp.shipment_id).first()
    if exec_rec or shp.current_status == "NORMAL_REROUTED":
        approved_reroute = True

    active_transfer = False
    transfer_rec = (
        db.query(models.VehicleTransfer)
        .filter(models.VehicleTransfer.shipment_id == shp.shipment_id)
        .filter(models.VehicleTransfer.status == "IN_PROGRESS")
        .first()
    )
    if transfer_rec:
        active_transfer = True

    context = SystemContext(
        approved_reroute_active=approved_reroute,
        active_vehicle_transfer=active_transfer,
        traffic_delay_active=(shp.current_status == "DELAYED"),
    )

    return shp, journey, latest_telemetry, telemetry_history, context


def evaluate_and_persist_shipment(
    db: Session,
    shipment_id_or_code: Union[int, str],
    now: Optional[datetime] = None,
    config: DetectionConfig = DEFAULT_CONFIG,
) -> DetectionResultDomain:
    """
    Evaluates misplaced shipment detection using MisplacementDecisionEngine
    and persists status/exceptions to MySQL database.
    """
    shp, journey, latest_telemetry, telemetry_history, context = load_shipment_domain_data(db, shipment_id_or_code)
    if not shp:
        raise ValueError(f"Shipment {shipment_id_or_code} not found in database.")

    engine = MisplacementDecisionEngine(config)
    result = engine.evaluate_shipment(
        journey=journey,
        current_telemetry=latest_telemetry,
        telemetry_history=telemetry_history,
        context=context,
        now=now or datetime.utcnow(),
    )

    # Persist status to shipment_table
    shp.current_status = result.status

    # Persist or update exception if MISPLACED or SUSPICIOUS
    if result.status in ["MISPLACED", "SUSPICIOUS"]:
        existing = (
            db.query(models.ShipmentException)
            .filter(models.ShipmentException.shipment_id == shp.shipment_id)
            .first()
        )
        if existing:
            existing.exception_type = "MISPLACEMENT_DETECTED" if result.status == "MISPLACED" else "ROUTE_DEVIATION"
            existing.severity = "HIGH" if result.status == "MISPLACED" else "NORMAL"
            existing.confidence_score = result.misplacement_score
            existing.exception_details = result.explanation
        else:
            new_exc = models.ShipmentException(
                shipment_id=shp.shipment_id,
                exception_type="MISPLACEMENT_DETECTED" if result.status == "MISPLACED" else "ROUTE_DEVIATION",
                severity="HIGH" if result.status == "MISPLACED" else "NORMAL",
                detected_timestamp=datetime.utcnow(),
                confidence_score=result.misplacement_score,
                exception_details=result.explanation,
                is_synthetic=True,
            )
            db.add(new_exc)

    db.commit()
    db.refresh(shp)
    return result


def evaluate_all_demo_shipments(db: Session, config: DetectionConfig = DEFAULT_CONFIG) -> List[Dict[str, Any]]:
    """
    Evaluates all 10 demo shipments (SH001 through SH010) and returns structured analysis items.
    """
    results = []
    for i in range(1, 11):
        shipment_code = f"SH{i:03d}"
        try:
            shp, journey, latest_telemetry, telemetry_history, context = load_shipment_domain_data(db, shipment_code)
            if shp:
                engine = MisplacementDecisionEngine(config)
                now_dt = datetime.utcnow()
                res = engine.evaluate_shipment(journey, latest_telemetry, telemetry_history, context, now=now_dt)

                results.append({
                    "id": shp.shipment_id,
                    "shipment_id": shipment_code,
                    "tracking_number": shp.tracking_number,
                    "origin_hub": shp.origin_hub.name if shp.origin_hub else "",
                    "destination_hub": shp.destination_hub.name if shp.destination_hub else "",
                    "expected_next_hub": shp.expected_next_hub.name if shp.expected_next_hub else "",
                    "assigned_vehicle": shp.assigned_vehicle.vehicle_code if shp.assigned_vehicle else "",
                    "current_status": res.status,
                    "misplacement_score": res.misplacement_score,
                    "distance_to_primary_route_km": res.distance_to_primary_route_km,
                    "distance_to_nearest_valid_route_km": res.distance_to_nearest_valid_route_km,
                    "heading_difference_deg": res.heading_difference_deg,
                    "persistent_anomaly": res.persistent_anomaly,
                    "safeguard_outcomes": res.safeguard_outcomes.to_dict(),
                    "primary_cause": res.primary_cause,
                    "explanation": res.explanation,
                    "current_lat": latest_telemetry.lat if latest_telemetry else 17.3850,
                    "current_lng": latest_telemetry.lng if latest_telemetry else 78.4867,
                    "speed_kmh": latest_telemetry.speed_kmh if latest_telemetry else 0.0,
                    "telemetry_points_count": len(telemetry_history),
                })
        except Exception as e:
            print(f"Error evaluating {shipment_code}: {e}")
    return results
