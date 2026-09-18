import json
import math
from typing import List
from sqlalchemy.orm import Session
from app import models, schemas


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_piggyback_recommendations(
    db: Session, shipment_id: int = None
) -> List[dict]:
    query = db.query(models.Shipment).filter(models.Shipment.current_status == "MISPLACED")
    if shipment_id:
        query = query.filter(models.Shipment.shipment_id == shipment_id)

    misplaced_shipments = query.all()
    routes = db.query(models.RouteNetwork).filter(models.RouteNetwork.active == True).all()
    hubs = {h.hub_id: h for h in db.query(models.Hub).filter(models.Hub.active == True).all()}

    recommendations = []

    for shipment in misplaced_shipments:
        latest_tracking = (
            db.query(models.ShipmentTracking)
            .filter(models.ShipmentTracking.shipment_id == shipment.shipment_id)
            .order_by(models.ShipmentTracking.timestamp.desc())
            .first()
        )

        current_hub = shipment.expected_next_hub or hubs.get(shipment.origin_id)
        dest_hub = shipment.destination_hub or hubs.get(shipment.destination_id)

        if latest_tracking and latest_tracking.current_lat and latest_tracking.current_lng:
            shipment_lat = float(latest_tracking.current_lat)
            shipment_lng = float(latest_tracking.current_lng)
        else:
            shipment_lat = float(current_hub.latitude) if current_hub else 17.3850
            shipment_lng = float(current_hub.longitude) if current_hub else 78.4867

        dest_lat = float(dest_hub.latitude) if dest_hub else 28.6139
        dest_lng = float(dest_hub.longitude) if dest_hub else 77.2090

        direct_dist_km = haversine_km(shipment_lat, shipment_lng, dest_lat, dest_lng)
        shipment_weight = float(shipment.shipment_weight_kg)

        for route in routes:
            try:
                waypoints = json.loads(route.route_geometry_json)
            except Exception:
                continue

            vehicle = db.query(models.Vehicle).filter(models.Vehicle.assigned_hub_id == route.origin_hub_id).first()
            max_capacity = float(vehicle.capacity_kg) if vehicle else 15000.0
            spare_capacity = round(max_capacity * 0.35, 1)

            if spare_capacity < shipment_weight:
                continue

            pickup_idx = -1
            dropoff_idx = -1
            min_pickup_dist = float("inf")
            min_dropoff_dist = float("inf")

            for idx, wp in enumerate(waypoints):
                wp_lat = float(wp.get("lat", 0.0))
                wp_lng = float(wp.get("lng", 0.0))
                dist_to_shipment = haversine_km(shipment_lat, shipment_lng, wp_lat, wp_lng)
                if dist_to_shipment < min_pickup_dist and dist_to_shipment < 250.0:
                    min_pickup_dist = dist_to_shipment
                    pickup_idx = idx

            if pickup_idx != -1:
                for idx in range(pickup_idx, len(waypoints)):
                    wp = waypoints[idx]
                    wp_lat = float(wp.get("lat", 0.0))
                    wp_lng = float(wp.get("lng", 0.0))
                    dist_to_dest = haversine_km(dest_lat, dest_lng, wp_lat, wp_lng)
                    if dist_to_dest < min_dropoff_dist and dist_to_dest < 250.0:
                        min_dropoff_dist = dist_to_dest
                        dropoff_idx = idx

            if pickup_idx != -1 and dropoff_idx != -1 and dropoff_idx >= pickup_idx:
                pickup_wp = waypoints[pickup_idx]
                dropoff_wp = waypoints[dropoff_idx]

                pickup_hub_id = pickup_wp.get("hub_id", shipment.origin_id)
                dropoff_hub_id = dropoff_wp.get("hub_id", shipment.destination_id)

                pickup_hub = hubs.get(pickup_hub_id, current_hub or list(hubs.values())[0])
                dropoff_hub = hubs.get(dropoff_hub_id, dest_hub or list(hubs.values())[1])

                dedicated_dist_km = round(direct_dist_km * 2.1, 1)
                dedicated_cost = round(250.0 + (dedicated_dist_km * 2.20), 2)
                dedicated_co2 = round(dedicated_dist_km * 0.48, 1)

                incremental_cost = 65.0
                cost_saved = round(max(dedicated_cost - incremental_cost, 120.0), 2)
                co2_saved = round(dedicated_co2, 1)

                match_score = min(99, max(68, int(98 - (min_pickup_dist * 0.15))))

                eta_pickup = pickup_wp.get("eta", "10:00 AM")
                eta_dropoff = dropoff_wp.get("eta", "06:00 PM")
                vehicle_code = vehicle.vehicle_code if vehicle else f"TRK-{route.route_id}"
                vehicle_type = vehicle.type if vehicle else "Intercity Container Truck"

                explanation = (
                    f"Vehicle {vehicle_code} ({vehicle_type}) has {int(spare_capacity)}kg spare capacity (needs {int(shipment_weight)}kg). "
                    f"Passes pickup point ({pickup_hub.name}) at {eta_pickup} and arrives near destination ({dropoff_hub.name}) at {eta_dropoff}. "
                    f"Piggybacking avoids a dedicated {int(dedicated_dist_km)}km dispatch across the corridor, saving ₹{cost_saved:.2f} ($) and preventing {co2_saved:.1f}kg CO2."
                )

                shipment_resp = schemas.ShipmentResponse(
                    id=shipment.shipment_id,
                    shipment_id=str(shipment.shipment_id),
                    tracking_number=shipment.tracking_number,
                    origin_hub_id=shipment.origin_id,
                    destination_hub_id=shipment.destination_id,
                    expected_next_hub_id=shipment.expected_next_hub_id,
                    assigned_vehicle_id=shipment.assigned_vehicle_id,
                    priority=shipment.shipment_priority,
                    status=shipment.current_status,
                    weight_kg=float(shipment.shipment_weight_kg),
                    delivery_deadline=shipment.delivery_deadline,
                    expected_arrival_time=shipment.created_timestamp,
                    created_at=shipment.created_timestamp,
                    updated_at=shipment.created_timestamp,
                    is_synthetic=shipment.is_synthetic,
                    origin_hub=schemas.HubResponse.model_validate(shipment.origin_hub) if shipment.origin_hub else None,
                    destination_hub=schemas.HubResponse.model_validate(shipment.destination_hub) if shipment.destination_hub else None,
                    expected_next_hub=schemas.HubResponse.model_validate(shipment.expected_next_hub) if shipment.expected_next_hub else None,
                    current_lat=shipment_lat,
                    current_lng=shipment_lng
                )

                rec = {
                    "recommendation_id": f"REC-{shipment.shipment_id}-{route.route_id}",
                    "shipment": shipment_resp,
                    "vehicle_route": schemas.VehicleRouteResponse(
                        id=route.route_id,
                        vehicle_code=vehicle_code,
                        vehicle_type=vehicle_type,
                        driver_name=f"Driver-{route.route_id}",
                        max_capacity_kg=max_capacity,
                        spare_capacity_kg=spare_capacity,
                        waypoints=waypoints,
                        status="EN_ROUTE"
                    ),
                    "pickup_hub": schemas.HubResponse.model_validate(pickup_hub),
                    "dropoff_hub": schemas.HubResponse.model_validate(dropoff_hub),
                    "match_score": match_score,
                    "cost_saved": cost_saved,
                    "co2_saved_kg": co2_saved,
                    "explanation": explanation,
                    "spare_capacity_after_kg": round(spare_capacity - shipment_weight, 1)
                }
                recommendations.append(rec)

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations
