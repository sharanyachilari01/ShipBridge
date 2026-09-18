import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models


def seed_database(db: Session, reseed_synthetic_only: bool = True):
    """
    Seeds 10 controlled MySQL scenarios (SH001 through SH010) and 26 Indian hubs.
    """
    if reseed_synthetic_only:
        db.query(models.FinalEvaluation).delete()
        db.query(models.RecoveryCandidateScoring).delete()
        db.query(models.RecoveryOpportunity).delete()
        db.query(models.RecoveryExecution).filter(models.RecoveryExecution.is_synthetic == True).delete()
        db.query(models.ShipmentException).filter(models.ShipmentException.is_synthetic == True).delete()
        db.query(models.ShipmentTracking).filter(models.ShipmentTracking.is_synthetic == True).delete()
        db.query(models.VehicleTransfer).filter(models.VehicleTransfer.is_synthetic == True).delete()
        db.query(models.Shipment).filter(models.Shipment.is_synthetic == True).delete()
        db.query(models.VehicleRoute).filter(models.VehicleRoute.is_synthetic == True).delete()
        db.query(models.Vehicle).filter(models.Vehicle.is_synthetic == True).delete()
        db.query(models.RouteNetwork).filter(models.RouteNetwork.is_synthetic == True).delete()
        db.query(models.Hub).filter(models.Hub.is_synthetic == True).delete()
        db.commit()
    else:
        db.query(models.FinalEvaluation).delete()
        db.query(models.RecoveryCandidateScoring).delete()
        db.query(models.RecoveryOpportunity).delete()
        db.query(models.RecoveryExecution).delete()
        db.query(models.ShipmentException).delete()
        db.query(models.ShipmentTracking).delete()
        db.query(models.VehicleTransfer).delete()
        db.query(models.Shipment).delete()
        db.query(models.VehicleRoute).delete()
        db.query(models.Vehicle).delete()
        db.query(models.RouteNetwork).delete()
        db.query(models.Hub).delete()
        db.commit()

    # 1. Seed 26 India Hubs
    hubs_data = [
        {"code": "HUB-BLR", "name": "Bengaluru Tech & Cargo Hub", "city": "Bengaluru", "state": "Karnataka", "latitude": 12.9716, "longitude": 77.5946},
        {"code": "HUB-MAA", "name": "Chennai Port Logistics Center", "city": "Chennai", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707},
        {"code": "HUB-HYD", "name": "Hyderabad Cyber Freight Terminal", "city": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867},
        {"code": "HUB-BOM", "name": "Mumbai JNPT Gateway Hub", "city": "Mumbai", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777},
        {"code": "HUB-PNQ", "name": "Pune Industrial Logistics Park", "city": "Pune", "state": "Maharashtra", "latitude": 18.5204, "longitude": 73.8567},
        {"code": "HUB-DEL", "name": "Delhi IGI Air Cargo Terminal", "city": "Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
        {"code": "HUB-NOD", "name": "Noida Express Logistics Hub", "city": "Noida", "state": "Uttar Pradesh", "latitude": 28.5355, "longitude": 77.3910},
        {"code": "HUB-AMD", "name": "Ahmedabad Inland Freight Container Terminal", "city": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714},
        {"code": "HUB-CCU", "name": "Kolkata Eastern Logistics Hub", "city": "Kolkata", "state": "West Bengal", "latitude": 22.5726, "longitude": 88.3639},
        {"code": "HUB-COK", "name": "Kochi Maritime Logistics Terminal", "city": "Kochi", "state": "Kerala", "latitude": 9.9312, "longitude": 76.2673},
        {"code": "HUB-JAI", "name": "Jaipur Pink City Freight Junction", "city": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873},
        {"code": "HUB-LKO", "name": "Lucknow Awadh Transport Depot", "city": "Lucknow", "state": "Uttar Pradesh", "latitude": 26.8467, "longitude": 80.9462},
        {"code": "HUB-BBI", "name": "Bhubaneswar Kalinga Logistics Hub", "city": "Bhubaneswar", "state": "Odisha", "latitude": 20.2961, "longitude": 85.8245},
        {"code": "HUB-NAG", "name": "Nagpur Multi-Modal Cargo Hub", "city": "Nagpur", "state": "Maharashtra", "latitude": 21.1458, "longitude": 79.0882},
        {"code": "HUB-IDR", "name": "Indore Malwa Freight Logistics", "city": "Indore", "state": "Madhya Pradesh", "latitude": 22.7196, "longitude": 75.8577},
        {"code": "HUB-CJB", "name": "Coimbatore Textile Cargo Hub", "city": "Coimbatore", "state": "Tamil Nadu", "latitude": 11.0168, "longitude": 76.9558},
        {"code": "HUB-VTZ", "name": "Visakhapatnam Vizag Port Depot", "city": "Visakhapatnam", "state": "Andhra Pradesh", "latitude": 17.6868, "longitude": 83.2185},
        {"code": "HUB-PAT", "name": "Patna Pataliputra Freight Terminal", "city": "Patna", "state": "Bihar", "latitude": 25.5941, "longitude": 85.1376},
        {"code": "HUB-GAU", "name": "Guwahati Northeast Gateway Hub", "city": "Guwahati", "state": "Assam", "latitude": 26.1445, "longitude": 91.7362},
        {"code": "HUB-IXC", "name": "Chandigarh Tricity Logistics Park", "city": "Chandigarh", "state": "Chandigarh", "latitude": 30.7333, "longitude": 76.7794},
        {"code": "HUB-SXR", "name": "Srinagar Valley Air Cargo Hub", "city": "Srinagar", "state": "Jammu & Kashmir", "latitude": 34.0837, "longitude": 74.7973},
        {"code": "HUB-STV", "name": "Surat Diamond & Textile Depot", "city": "Surat", "state": "Gujarat", "latitude": 21.1702, "longitude": 72.8311},
        {"code": "HUB-BDQ", "name": "Vadodara Industrial Corridor Hub", "city": "Vadodara", "state": "Gujarat", "latitude": 22.3072, "longitude": 73.1812},
        {"code": "HUB-BHO", "name": "Bhopal Central MP Logistics", "city": "Bhopal", "state": "Madhya Pradesh", "latitude": 23.2599, "longitude": 77.4126},
        {"code": "HUB-IXR", "name": "Ranchi Chota Nagpur Freight Park", "city": "Ranchi", "state": "Jharkhand", "latitude": 23.3441, "longitude": 85.3096},
        {"code": "HUB-TRV", "name": "Thiruvananthapuram Southern Hub", "city": "Thiruvananthapuram", "state": "Kerala", "latitude": 8.5241, "longitude": 76.9366},
    ]

    hubs_map = {}
    for h_data in hubs_data:
        hub = models.Hub(
            code=h_data["code"],
            name=h_data["name"],
            city=h_data["city"],
            state=h_data["state"],
            latitude=h_data["latitude"],
            longitude=h_data["longitude"],
            active=True,
            is_synthetic=True
        )
        db.add(hub)
        db.commit()
        db.refresh(hub)
        hubs_map[hub.code] = hub

    # 2. Seed Vehicles
    vehicles_data = [
        {"code": "IND-TRK-101", "type": "Heavy Container Truck (18-Wheeler)", "capacity_kg": 18000.0, "assigned_hub_code": "HUB-BLR"},
        {"code": "IND-TRK-204", "type": "Medium Freight Carrier", "capacity_kg": 9500.0, "assigned_hub_code": "HUB-BOM"},
        {"code": "IND-TRK-309", "type": "Express Air-Cargo Container Van", "capacity_kg": 4200.0, "assigned_hub_code": "HUB-DEL"},
        {"code": "IND-TRK-412", "type": "Heavy Multi-Axle Hauler", "capacity_kg": 24000.0, "assigned_hub_code": "HUB-CCU"},
        {"code": "IND-TRK-550", "type": "Refrigerated Cold-Chain Container", "capacity_kg": 12000.0, "assigned_hub_code": "HUB-HYD"},
    ]

    vehicles_map = {}
    for v_data in vehicles_data:
        vehicle = models.Vehicle(
            vehicle_code=v_data["code"],
            type=v_data["type"],
            capacity_kg=v_data["capacity_kg"],
            assigned_hub_id=hubs_map[v_data["assigned_hub_code"]].hub_id,
            status="ACTIVE",
            is_synthetic=True
        )
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)
        vehicles_map[vehicle.vehicle_code] = vehicle

    # 3. Seed Route Network
    routes_data = [
        {
            "code": "RTE-BLR-HYD-DEL",
            "origin": "HUB-BLR",
            "destination": "HUB-DEL",
            "waypoints": [
                {"hub_id": hubs_map["HUB-BLR"].hub_id, "hub_name": "HUB-BLR", "lat": 12.9716, "lng": 77.5946, "sequence": 1},
                {"hub_id": hubs_map["HUB-HYD"].hub_id, "hub_name": "HUB-HYD", "lat": 17.3850, "lng": 78.4867, "sequence": 2},
                {"hub_id": hubs_map["HUB-NAG"].hub_id, "hub_name": "HUB-NAG", "lat": 21.1458, "lng": 79.0882, "sequence": 3},
                {"hub_id": hubs_map["HUB-DEL"].hub_id, "hub_name": "HUB-DEL", "lat": 28.6139, "lng": 77.2090, "sequence": 4},
            ]
        },
        {
            "code": "RTE-BOM-PNQ-AMD",
            "origin": "HUB-BOM",
            "destination": "HUB-AMD",
            "waypoints": [
                {"hub_id": hubs_map["HUB-BOM"].hub_id, "hub_name": "HUB-BOM", "lat": 19.0760, "lng": 72.8777, "sequence": 1},
                {"hub_id": hubs_map["HUB-PNQ"].hub_id, "hub_name": "HUB-PNQ", "lat": 18.5204, "lng": 73.8567, "sequence": 2},
                {"hub_id": hubs_map["HUB-BDQ"].hub_id, "hub_name": "HUB-BDQ", "lat": 22.3072, "lng": 73.1812, "sequence": 3},
                {"hub_id": hubs_map["HUB-AMD"].hub_id, "hub_name": "HUB-AMD", "lat": 23.0225, "lng": 72.5714, "sequence": 4},
            ]
        },
    ]

    routes_map = {}
    for r_data in routes_data:
        route = models.RouteNetwork(
            route_code=r_data["code"],
            origin_hub_id=hubs_map[r_data["origin"]].hub_id,
            destination_hub_id=hubs_map[r_data["destination"]].hub_id,
            route_geometry_json=json.dumps(r_data["waypoints"]),
            active=True,
            is_synthetic=True
        )
        db.add(route)
        db.commit()
        db.refresh(route)
        routes_map[route.route_code] = route

    # 4. Seed 10 Controlled Scenarios (SH001 to SH010)
    now = datetime.utcnow()

    demo_scenarios = [
        # SH001: NORMAL — On primary corridor BLR-HYD-DEL, speed 65km/h, good GPS
        {
            "id": 1,
            "shipment_id": "SH001",
            "tracking_number": "SB-IND-SH001",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "NORMAL",
            "vehicle": "IND-TRK-101",
            "weight": 350.0,
            "deadline": now + timedelta(hours=24),
            "telemetry_points": [
                {"lat": 17.3850, "lng": 78.4867, "speed": 65.0, "accuracy": 5.0, "gateway": "IND-TRK-101", "minutes_ago": 10},
            ]
        },
        # SH002: DELAYED — Late past delivery deadline while remaining on primary route
        {
            "id": 2,
            "shipment_id": "SH002",
            "tracking_number": "SB-IND-SH002",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "DELAYED",
            "vehicle": "IND-TRK-101",
            "weight": 420.0,
            "deadline": now - timedelta(hours=2),  # Past deadline
            "telemetry_points": [
                {"lat": 17.3850, "lng": 78.4867, "speed": 18.0, "accuracy": 8.0, "gateway": "IND-TRK-101", "minutes_ago": 15},
            ]
        },
        # SH003: NORMAL_REROUTED — Off primary route, but active approved reroute recorded
        {
            "id": 3,
            "shipment_id": "SH003",
            "tracking_number": "SB-IND-SH003",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "NORMAL_REROUTED",
            "vehicle": "IND-TRK-101",
            "weight": 280.0,
            "deadline": now + timedelta(hours=20),
            "telemetry_points": [
                {"lat": 19.8800, "lng": 75.3200, "speed": 55.0, "accuracy": 10.0, "gateway": "IND-TRK-101", "minutes_ago": 10},
            ],
            "approved_reroute": True
        },
        # SH004: NORMAL (vehicle transfer active within 15-min grace period)
        {
            "id": 4,
            "shipment_id": "SH004",
            "tracking_number": "SB-IND-SH004",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "NORMAL",
            "vehicle": "IND-TRK-101",
            "weight": 190.0,
            "deadline": now + timedelta(hours=18),
            "telemetry_points": [
                {"lat": 17.3850, "lng": 78.4867, "speed": 10.0, "accuracy": 6.0, "gateway": "IND-TRK-550", "minutes_ago": 5},
            ],
            "vehicle_transfer": True
        },
        # SH005: NORMAL (Off primary route, but on allowed alternative route BOM-PNQ-AMD)
        {
            "id": 5,
            "shipment_id": "SH005",
            "tracking_number": "SB-IND-SH005",
            "origin_code": "HUB-BOM",
            "destination_code": "HUB-AMD",
            "status": "NORMAL",
            "vehicle": "IND-TRK-204",
            "weight": 510.0,
            "deadline": now + timedelta(hours=16),
            "telemetry_points": [
                {"lat": 18.5204, "lng": 73.8567, "speed": 60.0, "accuracy": 8.0, "gateway": "IND-TRK-204", "minutes_ago": 12},
            ]
        },
        # SH006: UNKNOWN_SIGNAL_MONITOR — Telemetry missing / signal lost > 3 hours
        {
            "id": 6,
            "shipment_id": "SH006",
            "tracking_number": "SB-IND-SH006",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "UNKNOWN_SIGNAL_MONITOR",
            "vehicle": "IND-TRK-101",
            "weight": 310.0,
            "deadline": now + timedelta(hours=12),
            "telemetry_points": [
                {"lat": 12.9716, "lng": 77.5946, "speed": 0.0, "accuracy": 10.0, "gateway": "IND-TRK-101", "minutes_ago": 220},  # > 3.6 hours ago
            ]
        },
        # SH007: NORMAL (Single isolated GPS jitter point off-route, 1 off-route point != persistent anomaly)
        {
            "id": 7,
            "shipment_id": "SH007",
            "tracking_number": "SB-IND-SH007",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "NORMAL",
            "vehicle": "IND-TRK-101",
            "weight": 220.0,
            "deadline": now + timedelta(hours=24),
            "telemetry_points": [
                {"lat": 12.9716, "lng": 77.5946, "speed": 60.0, "accuracy": 5.0, "gateway": "IND-TRK-101", "minutes_ago": 40},
                {"lat": 19.8800, "lng": 75.3200, "speed": 60.0, "accuracy": 5.0, "gateway": "IND-TRK-101", "minutes_ago": 20},  # 1 off-route jitter point
                {"lat": 17.3850, "lng": 78.4867, "speed": 60.0, "accuracy": 5.0, "gateway": "IND-TRK-101", "minutes_ago": 5},   # Back on route
            ]
        },
        # SH008: SUSPICIOUS — Exactly 2 consecutive off-route points (insufficient for 3-point persistence requirement)
        {
            "id": 8,
            "shipment_id": "SH008",
            "tracking_number": "SB-IND-SH008",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "SUSPICIOUS",
            "vehicle": "IND-TRK-101",
            "weight": 410.0,
            "deadline": now + timedelta(hours=24),
            "telemetry_points": [
                {"lat": 19.8800, "lng": 75.3200, "speed": 55.0, "accuracy": 10.0, "gateway": "IND-TRK-101", "minutes_ago": 25},
                {"lat": 19.9500, "lng": 75.4000, "speed": 55.0, "accuracy": 10.0, "gateway": "IND-TRK-101", "minutes_ago": 5},  # 2 consecutive off-route points
            ]
        },
        # SH009: MISPLACED — 3+ consecutive off-route points, >15km off route, composite score >= 0.65
        {
            "id": 9,
            "shipment_id": "SH009",
            "tracking_number": "SB-IND-SH009",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "MISPLACED",
            "vehicle": "IND-TRK-101",
            "weight": 340.0,
            "deadline": now + timedelta(hours=24),
            "telemetry_points": [
                {"lat": 19.8800, "lng": 75.3200, "speed": 65.0, "accuracy": 5.0, "gateway": "IND-TRK-999", "minutes_ago": 45},
                {"lat": 19.9500, "lng": 75.4000, "speed": 65.0, "accuracy": 5.0, "gateway": "IND-TRK-999", "minutes_ago": 25},
                {"lat": 20.0500, "lng": 75.5000, "speed": 65.0, "accuracy": 5.0, "gateway": "IND-TRK-999", "minutes_ago": 5},   # 3 consecutive off-route points + gateway unbind
            ]
        },
        # SH010: NORMAL_REROUTED — Off-route but with active approved reroute
        {
            "id": 10,
            "shipment_id": "SH010",
            "tracking_number": "SB-IND-SH010",
            "origin_code": "HUB-BLR",
            "destination_code": "HUB-DEL",
            "status": "NORMAL_REROUTED",
            "vehicle": "IND-TRK-101",
            "weight": 550.0,
            "deadline": now + timedelta(hours=24),
            "telemetry_points": [
                {"lat": 19.8800, "lng": 75.3200, "speed": 60.0, "accuracy": 5.0, "gateway": "IND-TRK-101", "minutes_ago": 10},
            ],
            "approved_reroute": True
        }
    ]

    for sc in demo_scenarios:
        shipment = models.Shipment(
            shipment_id=sc["id"],
            tracking_number=sc["tracking_number"],
            origin_id=hubs_map[sc["origin_code"]].hub_id,
            destination_id=hubs_map[sc["destination_code"]].hub_id,
            expected_next_hub_id=hubs_map["HUB-HYD"].hub_id,
            assigned_vehicle_id=vehicles_map[sc["vehicle"]].vehicle_id,
            shipment_priority="HIGH" if sc["status"] == "MISPLACED" else "NORMAL",
            current_status=sc["status"],
            shipment_weight_kg=sc["weight"],
            created_timestamp=now - timedelta(hours=5),
            delivery_deadline=sc["deadline"],
            is_synthetic=True
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)

        # Seed Telemetry Points
        for tp in sc["telemetry_points"]:
            tracking = models.ShipmentTracking(
                shipment_id=shipment.shipment_id,
                assigned_vehicle_id=shipment.assigned_vehicle_id,
                timestamp=now - timedelta(minutes=tp["minutes_ago"]),
                current_lat=tp["lat"],
                current_lng=tp["lng"],
                speed_kmh=tp["speed"],
                heading_degrees=140.0,
                gps_accuracy_meters=tp["accuracy"],
                ble_gateway_id=tp["gateway"],
                tracking_available=False if sc["status"] == "UNKNOWN_SIGNAL_MONITOR" else True,
                is_synthetic=True
            )
            db.add(tracking)

        # Seed Vehicle Transfer if SH004
        if sc.get("vehicle_transfer"):
            transfer = models.VehicleTransfer(
                shipment_id=shipment.shipment_id,
                from_vehicle_id=vehicles_map["IND-TRK-101"].vehicle_id,
                to_vehicle_id=vehicles_map["IND-TRK-550"].vehicle_id,
                transfer_hub_id=hubs_map["HUB-HYD"].hub_id,
                transferred_at=now - timedelta(minutes=8),  # Within 15-min grace
                status="IN_PROGRESS",
                is_synthetic=True
            )
            db.add(transfer)

        # Seed Approved Reroute if SH003 or SH010
        if sc.get("approved_reroute"):
            execution = models.RecoveryExecution(
                shipment_id=shipment.shipment_id,
                assigned_vehicle_id=vehicles_map["IND-TRK-101"].vehicle_id,
                pickup_hub_id=hubs_map["HUB-HYD"].hub_id,
                dropoff_hub_id=hubs_map["HUB-DEL"].hub_id,
                cost_saved=1200.0,
                co2_saved_kg=280.0,
                executed_timestamp=now - timedelta(hours=1),
                explanation="Approved reroute via Maharashtra corridor",
                is_synthetic=True
            )
            db.add(execution)

        # Seed ShipmentException if MISPLACED
        if sc["status"] == "MISPLACED":
            exception = models.ShipmentException(
                shipment_id=shipment.shipment_id,
                exception_type="MISPLACEMENT_DETECTED",
                severity="HIGH",
                detected_timestamp=now - timedelta(minutes=5),
                confidence_score=0.95,
                exception_details="3 consecutive off-route points detected (>15km deviation)",
                is_synthetic=True
            )
            db.add(exception)

        # Seed FinalEvaluation records
        if sc["shipment_id"] == "SH003":
            fe = models.FinalEvaluation(
                shipment_id=shipment.shipment_id,
                original_cost=1500.0,
                recovery_cost=300.0,
                cost_saved=1200.0,
                total_savings=1200.0,
                co2_offset=280.0,
                time_saved_hours=14.5,
                deadline_met=True,
                recovery_success_status="SUCCESSFUL",
                additional_distance_km=18.5,
            )
            db.add(fe)
        elif sc["shipment_id"] == "SH009":
            fe = models.FinalEvaluation(
                shipment_id=shipment.shipment_id,
                original_cost=1800.0,
                recovery_cost=450.0,
                cost_saved=1350.0,
                total_savings=1350.0,
                co2_offset=310.0,
                time_saved_hours=12.0,
                deadline_met=True,
                recovery_success_status="RECOVERY_RECOMMENDED",
                additional_distance_km=24.0,
            )
            db.add(fe)
        elif sc["shipment_id"] == "SH010":
            fe = models.FinalEvaluation(
                shipment_id=shipment.shipment_id,
                original_cost=1400.0,
                recovery_cost=250.0,
                cost_saved=1150.0,
                total_savings=1150.0,
                co2_offset=250.0,
                time_saved_hours=16.0,
                deadline_met=True,
                recovery_success_status="SUCCESSFUL",
                additional_distance_km=12.0,
            )
            db.add(fe)

    db.commit()
    print("10 Controlled Demo Scenarios (SH001 to SH010) successfully seeded in MySQL database!")

