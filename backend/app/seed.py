import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app import models


def seed_database(db: Session, reseed_synthetic_only: bool = True):
    """
    Seeds 32 controlled India-wide logistics scenarios (SH001 through SH032),
    26 major Indian hubs, active vehicles, routes, and recovery opportunities in MySQL.
    """
    if reseed_synthetic_only:
        db.query(models.RecoveryImpactSnapshot).delete()
        db.query(models.RecoveryDecision).delete()
        db.query(models.RecoveryRecommendation).delete()
        db.query(models.FinalEvaluation).delete()
        db.query(models.RecoveryCandidateScoring).delete()
        db.query(models.RecoveryOpportunity).delete()
        db.query(models.PiggybackAnalysisRun).delete()
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
        db.query(models.RecoveryImpactSnapshot).delete()
        db.query(models.RecoveryDecision).delete()
        db.query(models.RecoveryRecommendation).delete()
        db.query(models.FinalEvaluation).delete()
        db.query(models.RecoveryCandidateScoring).delete()
        db.query(models.RecoveryOpportunity).delete()
        db.query(models.PiggybackAnalysisRun).delete()
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
        {"code": "HUB-AMD", "name": "Ahmedabad Inland Container Depot", "city": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714},
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

    # 2. Seed Active Fleet Vehicles
    vehicles_data = [
        {"code": "IND-TRK-101", "type": "Heavy Multi-Axle Container Truck", "capacity_kg": 18000.0, "assigned_hub_code": "HUB-BLR"},
        {"code": "IND-TRK-204", "type": "Medium Freight Carrier", "capacity_kg": 9500.0, "assigned_hub_code": "HUB-BOM"},
        {"code": "IND-TRK-309", "type": "Express Air-Cargo Container Van", "capacity_kg": 4200.0, "assigned_hub_code": "HUB-DEL"},
        {"code": "IND-TRK-412", "type": "Heavy Multi-Axle Hauler", "capacity_kg": 24000.0, "assigned_hub_code": "HUB-CCU"},
        {"code": "IND-TRK-550", "type": "Refrigerated Cold-Chain Container", "capacity_kg": 12000.0, "assigned_hub_code": "HUB-HYD"},
        {"code": "IND-TRK-608", "type": "Interstate Express Freighter", "capacity_kg": 15000.0, "assigned_hub_code": "HUB-LKO"},
        {"code": "IND-TRK-722", "type": "Coastal Freight Transporter", "capacity_kg": 10000.0, "assigned_hub_code": "HUB-MAA"},
        {"code": "IND-TRK-815", "type": "Northern Freight Hauler", "capacity_kg": 16000.0, "assigned_hub_code": "HUB-JAI"},
        {"code": "IND-TRK-930", "type": "Central Corridor Container Truck", "capacity_kg": 14000.0, "assigned_hub_code": "HUB-NAG"},
        {"code": "IND-TRK-999", "type": "Low-Capacity Pickup Truck", "capacity_kg": 1500.0, "assigned_hub_code": "HUB-BLR"},  # For weight overload test
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
            "active": True,
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
            "active": True,
            "waypoints": [
                {"hub_id": hubs_map["HUB-BOM"].hub_id, "hub_name": "HUB-BOM", "lat": 19.0760, "lng": 72.8777, "sequence": 1},
                {"hub_id": hubs_map["HUB-PNQ"].hub_id, "hub_name": "HUB-PNQ", "lat": 18.5204, "lng": 73.8567, "sequence": 2},
                {"hub_id": hubs_map["HUB-BDQ"].hub_id, "hub_name": "HUB-BDQ", "lat": 22.3072, "lng": 73.1812, "sequence": 3},
                {"hub_id": hubs_map["HUB-AMD"].hub_id, "hub_name": "HUB-AMD", "lat": 23.0225, "lng": 72.5714, "sequence": 4},
            ]
        },
        {
            "code": "RTE-MAA-HYD-LKO",
            "origin": "HUB-MAA",
            "destination": "HUB-LKO",
            "active": True,
            "waypoints": [
                {"hub_id": hubs_map["HUB-MAA"].hub_id, "hub_name": "HUB-MAA", "lat": 13.0827, "lng": 80.2707, "sequence": 1},
                {"hub_id": hubs_map["HUB-HYD"].hub_id, "hub_name": "HUB-HYD", "lat": 17.3850, "lng": 78.4867, "sequence": 2},
                {"hub_id": hubs_map["HUB-LKO"].hub_id, "hub_name": "HUB-LKO", "lat": 26.8467, "lng": 80.9462, "sequence": 3},
            ]
        },
        {
            "code": "RTE-LKO-DEL",
            "origin": "HUB-LKO",
            "destination": "HUB-DEL",
            "active": True,
            "waypoints": [
                {"hub_id": hubs_map["HUB-LKO"].hub_id, "hub_name": "HUB-LKO", "lat": 26.8467, "lng": 80.9462, "sequence": 1},
                {"hub_id": hubs_map["HUB-NOD"].hub_id, "hub_name": "HUB-NOD", "lat": 28.5355, "lng": 77.3910, "sequence": 2},
                {"hub_id": hubs_map["HUB-DEL"].hub_id, "hub_name": "HUB-DEL", "lat": 28.6139, "lng": 77.2090, "sequence": 3},
            ]
        },
        {
            "code": "RTE-JAI-DEL-BLOCKED",
            "origin": "HUB-JAI",
            "destination": "HUB-DEL",
            "active": False,  # Blocked route test case
            "waypoints": [
                {"hub_id": hubs_map["HUB-JAI"].hub_id, "hub_name": "HUB-JAI", "lat": 26.9124, "lng": 75.7873, "sequence": 1},
                {"hub_id": hubs_map["HUB-DEL"].hub_id, "hub_name": "HUB-DEL", "lat": 28.6139, "lng": 77.2090, "sequence": 2},
            ]
        }
    ]

    routes_map = {}
    for r_data in routes_data:
        route = models.RouteNetwork(
            route_code=r_data["code"],
            origin_hub_id=hubs_map[r_data["origin"]].hub_id,
            destination_hub_id=hubs_map[r_data["destination"]].hub_id,
            route_geometry_json=json.dumps(r_data["waypoints"]),
            active=r_data["active"],
            is_synthetic=True
        )
        db.add(route)
        db.commit()
        db.refresh(route)
        routes_map[route.route_code] = route

        # VehicleRoute assignments
        if route.route_code == "RTE-BLR-HYD-DEL":
            vr1 = models.VehicleRoute(vehicle_id=vehicles_map["IND-TRK-101"].vehicle_id, route_id=route.route_id, status="ACTIVE", is_synthetic=True)
            vr2 = models.VehicleRoute(vehicle_id=vehicles_map["IND-TRK-550"].vehicle_id, route_id=route.route_id, status="ACTIVE", is_synthetic=True)
            db.add_all([vr1, vr2])
        elif route.route_code == "RTE-MAA-HYD-LKO":
            vr3 = models.VehicleRoute(vehicle_id=vehicles_map["IND-TRK-608"].vehicle_id, route_id=route.route_id, status="ACTIVE", is_synthetic=True)
            db.add(vr3)
        elif route.route_code == "RTE-LKO-DEL":
            vr4 = models.VehicleRoute(vehicle_id=vehicles_map["IND-TRK-309"].vehicle_id, route_id=route.route_id, status="ACTIVE", is_synthetic=True)
            db.add(vr4)
        db.commit()

    # 4. Seed 32 Controlled Scenarios (SH001 to SH032)
    now = datetime.utcnow()

    scenarios = [
        # SH001 - SH010 (Standard Stage 1 / Stage 2 baseline cases)
        {"id": 1, "code": "SH001", "tracking": "SB-IND-SH001", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-101", "weight": 350.0, "volume": 1.5, "hours_left": 24, "lat": 17.3850, "lng": 78.4867, "minutes_ago": 10},
        {"id": 2, "code": "SH002", "tracking": "SB-IND-SH002", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "DELAYED", "priority": "HIGH", "vehicle": "IND-TRK-101", "weight": 420.0, "volume": 2.0, "hours_left": -2, "lat": 17.3850, "lng": 78.4867, "minutes_ago": 15},
        {"id": 3, "code": "SH003", "tracking": "SB-IND-SH003", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "NORMAL_REROUTED", "priority": "NORMAL", "vehicle": "IND-TRK-101", "weight": 280.0, "volume": 1.2, "hours_left": 20, "lat": 19.8800, "lng": 75.3200, "minutes_ago": 10, "approved_reroute": True},
        {"id": 4, "code": "SH004", "tracking": "SB-IND-SH004", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-101", "weight": 190.0, "volume": 1.0, "hours_left": 18, "lat": 17.3850, "lng": 78.4867, "minutes_ago": 5, "vehicle_transfer": True},
        {"id": 5, "code": "SH005", "tracking": "SB-IND-SH005", "origin": "HUB-BOM", "dest": "HUB-AMD", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-204", "weight": 510.0, "volume": 2.5, "hours_left": 16, "lat": 18.5204, "lng": 73.8567, "minutes_ago": 12},
        {"id": 6, "code": "SH006", "tracking": "SB-IND-SH006", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "UNKNOWN_SIGNAL_MONITOR", "priority": "HIGH", "vehicle": "IND-TRK-101", "weight": 310.0, "volume": 1.4, "hours_left": 12, "lat": 12.9716, "lng": 77.5946, "minutes_ago": 220},
        {"id": 7, "code": "SH007", "tracking": "SB-IND-SH007", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-101", "weight": 220.0, "volume": 1.1, "hours_left": 24, "lat": 17.3850, "lng": 78.4867, "minutes_ago": 5, "gps_jitter": True},
        {"id": 8, "code": "SH008", "tracking": "SB-IND-SH008", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "SUSPICIOUS", "priority": "NORMAL", "vehicle": "IND-TRK-101", "weight": 410.0, "volume": 1.8, "hours_left": 24, "lat": 19.9500, "lng": 75.4000, "minutes_ago": 5},
        
        # SH009: MISPLACED — Direct Piggyback Opportunity (High Priority)
        {"id": 9, "code": "SH009", "tracking": "SB-IND-SH009", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "CRITICAL", "vehicle": "IND-TRK-101", "weight": 340.0, "volume": 1.6, "hours_left": 24, "lat": 20.0500, "lng": 75.5000, "minutes_ago": 5, "misplaced": True},
        {"id": 10, "code": "SH010", "tracking": "SB-IND-SH010", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "NORMAL_REROUTED", "priority": "NORMAL", "vehicle": "IND-TRK-101", "weight": 550.0, "volume": 2.8, "hours_left": 24, "lat": 19.8800, "lng": 75.3200, "minutes_ago": 10, "approved_reroute": True},
        
        # SH011: MISPLACED — Hub Transfer Piggyback Scenario (Via HYD / LKO)
        {"id": 11, "code": "SH011", "tracking": "SB-IND-SH011", "origin": "HUB-MAA", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "HIGH", "vehicle": "IND-TRK-722", "weight": 620.0, "volume": 2.9, "hours_left": 18, "lat": 17.5000, "lng": 78.5500, "minutes_ago": 10, "misplaced": True},
        
        # SH012: MISPLACED — Two-Hop Piggyback Scenario (MAA -> HYD -> LKO -> DEL)
        {"id": 12, "code": "SH012", "tracking": "SB-IND-SH012", "origin": "HUB-COK", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "HIGH", "vehicle": "IND-TRK-722", "weight": 850.0, "volume": 4.1, "hours_left": 30, "lat": 13.1500, "lng": 80.1000, "minutes_ago": 8, "misplaced": True},
        
        # SH013: MISPLACED — No-Feasible-Route Scenario (Srinagar to Trivandrum corridor)
        {"id": 13, "code": "SH013", "tracking": "SB-IND-SH013", "origin": "HUB-SXR", "dest": "HUB-TRV", "status": "MISPLACED", "priority": "CRITICAL", "vehicle": "IND-TRK-309", "weight": 120.0, "volume": 0.8, "hours_left": 14, "lat": 34.0837, "lng": 74.7973, "minutes_ago": 15, "misplaced": True, "no_route_reason": "No active passing truck route operating on Srinagar-Trivandrum direct corridor"},
        
        # SH014: MISPLACED — Insufficient Weight Capacity Case
        {"id": 14, "code": "SH014", "tracking": "SB-IND-SH014", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "HIGH", "vehicle": "IND-TRK-999", "weight": 14500.0, "volume": 8.0, "hours_left": 22, "lat": 17.4000, "lng": 78.5000, "minutes_ago": 12, "misplaced": True, "no_route_reason": "Shipment weight (14,500kg) exceeds available truck payload capacity"},
        
        # SH015: MISPLACED — Insufficient Volume Capacity Case
        {"id": 15, "code": "SH015", "tracking": "SB-IND-SH015", "origin": "HUB-BOM", "dest": "HUB-AMD", "status": "MISPLACED", "priority": "HIGH", "vehicle": "IND-TRK-204", "weight": 1200.0, "volume": 38.0, "hours_left": 20, "lat": 19.1000, "lng": 72.9000, "minutes_ago": 20, "misplaced": True, "no_route_reason": "Shipment volume (38.0 m³) exceeds available cargo bay space"},
        
        # SH016: MISPLACED — Blocked/Inactive Route Case
        {"id": 16, "code": "SH016", "tracking": "SB-IND-SH016", "origin": "HUB-JAI", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "CRITICAL", "vehicle": "IND-TRK-815", "weight": 480.0, "volume": 2.2, "hours_left": 8, "lat": 27.2000, "lng": 76.2000, "minutes_ago": 10, "misplaced": True, "no_route_reason": "Primary route RTE-JAI-DEL inactive due to highway maintenance"},
        
        # SH017: MISPLACED — Closed/Unavailable Transfer Hub Case
        {"id": 17, "code": "SH017", "tracking": "SB-IND-SH017", "origin": "HUB-PAT", "dest": "HUB-CCU", "status": "MISPLACED", "priority": "NORMAL", "vehicle": "IND-TRK-412", "weight": 700.0, "volume": 3.0, "hours_left": 16, "lat": 25.6000, "lng": 85.2000, "minutes_ago": 25, "misplaced": True, "no_route_reason": "Intermediary transfer hub PAT undergoing scheduled warehouse maintenance"},
        
        # SH018: MISPLACED — Missed Pickup Timing Case
        {"id": 18, "code": "SH018", "tracking": "SB-IND-SH018", "origin": "HUB-HYD", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "HIGH", "vehicle": "IND-TRK-550", "weight": 390.0, "volume": 1.9, "hours_left": 5, "lat": 17.4200, "lng": 78.4500, "minutes_ago": 30, "misplaced": True, "no_route_reason": "Passing truck arrival time is 4.5 hours past the required pickup deadline"},
        
        # SH019: MISPLACED — Deadline Missed Case
        {"id": 19, "code": "SH019", "tracking": "SB-IND-SH019", "origin": "HUB-AMD", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "CRITICAL", "vehicle": "IND-TRK-204", "weight": 920.0, "volume": 4.5, "hours_left": -1, "lat": 23.1000, "lng": 72.6000, "minutes_ago": 40, "misplaced": True, "no_route_reason": "Delivery deadline already passed; piggyback ETA cannot satisfy SLA"},
        
        # SH020: MISPLACED — Valid Alternative Route Scenario
        {"id": 20, "code": "SH020", "tracking": "SB-IND-SH020", "origin": "HUB-BOM", "dest": "HUB-CCU", "status": "MISPLACED", "priority": "NORMAL", "vehicle": "IND-TRK-204", "weight": 410.0, "volume": 2.1, "hours_left": 28, "lat": 21.1458, "lng": 79.0882, "minutes_ago": 15, "misplaced": True},
        
        # SH021: RECOVERY_APPROVED — Approved Reroute Scenario
        {"id": 21, "code": "SH021", "tracking": "SB-IND-SH021", "origin": "HUB-BLR", "dest": "HUB-DEL", "status": "RECOVERY_APPROVED", "priority": "HIGH", "vehicle": "IND-TRK-101", "weight": 600.0, "volume": 3.0, "hours_left": 20, "lat": 17.3850, "lng": 78.4867, "minutes_ago": 5},
        
        # SH022 - SH032: India Network Active Freight Operations
        {"id": 22, "code": "SH022", "tracking": "SB-IND-SH022", "origin": "HUB-CCU", "dest": "HUB-VTZ", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-412", "weight": 1100.0, "volume": 5.0, "hours_left": 24, "lat": 20.2961, "lng": 85.8245, "minutes_ago": 10},
        {"id": 23, "code": "SH023", "tracking": "SB-IND-SH023", "origin": "HUB-AMD", "dest": "HUB-BOM", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-204", "weight": 850.0, "volume": 3.8, "hours_left": 14, "lat": 21.1702, "lng": 72.8311, "minutes_ago": 8},
        {"id": 24, "code": "SH024", "tracking": "SB-IND-SH024", "origin": "HUB-LKO", "dest": "HUB-DEL", "status": "DELAYED", "priority": "HIGH", "vehicle": "IND-TRK-608", "weight": 430.0, "volume": 2.0, "hours_left": -3, "lat": 26.8467, "lng": 80.9462, "minutes_ago": 50},
        {"id": 25, "code": "SH025", "tracking": "SB-IND-SH025", "origin": "HUB-BOM", "dest": "HUB-PNQ", "status": "UNKNOWN_SIGNAL_MONITOR", "priority": "NORMAL", "vehicle": "IND-TRK-204", "weight": 320.0, "volume": 1.5, "hours_left": 10, "lat": 18.5204, "lng": 73.8567, "minutes_ago": 210},
        {"id": 26, "code": "SH026", "tracking": "SB-IND-SH026", "origin": "HUB-JAI", "dest": "HUB-DEL", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-815", "weight": 290.0, "volume": 1.3, "hours_left": 12, "lat": 26.9124, "lng": 75.7873, "minutes_ago": 5},
        {"id": 27, "code": "SH027", "tracking": "SB-IND-SH027", "origin": "HUB-IDR", "dest": "HUB-NAG", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-930", "weight": 670.0, "volume": 3.1, "hours_left": 15, "lat": 22.7196, "lng": 75.8577, "minutes_ago": 18},
        {"id": 28, "code": "SH028", "tracking": "SB-IND-SH028", "origin": "HUB-COK", "dest": "HUB-TRV", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-722", "weight": 520.0, "volume": 2.4, "hours_left": 8, "lat": 9.9312, "lng": 76.2673, "minutes_ago": 6},
        {"id": 29, "code": "SH029", "tracking": "SB-IND-SH029", "origin": "HUB-GAU", "dest": "HUB-CCU", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-412", "weight": 980.0, "volume": 4.2, "hours_left": 36, "lat": 26.1445, "lng": 91.7362, "minutes_ago": 14},
        {"id": 30, "code": "SH030", "tracking": "SB-IND-SH030", "origin": "HUB-IXC", "dest": "HUB-DEL", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-309", "weight": 240.0, "volume": 1.1, "hours_left": 6, "lat": 30.7333, "lng": 76.7794, "minutes_ago": 4},
        {"id": 31, "code": "SH031", "tracking": "SB-IND-SH031", "origin": "HUB-PAT", "dest": "HUB-LKO", "status": "DELAYED", "priority": "HIGH", "vehicle": "IND-TRK-608", "weight": 760.0, "volume": 3.6, "hours_left": -1, "lat": 25.5941, "lng": 85.1376, "minutes_ago": 45},
        {"id": 32, "code": "SH032", "tracking": "SB-IND-SH032", "origin": "HUB-VTZ", "dest": "HUB-HYD", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-550", "weight": 430.0, "volume": 1.9, "hours_left": 16, "lat": 17.6868, "lng": 83.2185, "minutes_ago": 11},
        
        # SH033 - SH040: Extended India Logistics Network Scenarios (Total 40 scenarios)
        {"id": 33, "code": "SH033", "tracking": "SB-IND-SH033", "origin": "HUB-NAG", "dest": "HUB-DEL", "status": "MISPLACED", "priority": "HIGH", "vehicle": "IND-TRK-550", "weight": 480.0, "volume": 2.2, "hours_left": 26, "lat": 21.1458, "lng": 79.0882, "minutes_ago": 15, "misplaced": True},
        {"id": 34, "code": "SH034", "tracking": "SB-IND-SH034", "origin": "HUB-BHO", "dest": "HUB-DEL", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-930", "weight": 610.0, "volume": 2.8, "hours_left": 18, "lat": 23.2599, "lng": 77.4126, "minutes_ago": 8},
        {"id": 35, "code": "SH035", "tracking": "SB-IND-SH035", "origin": "HUB-BDQ", "dest": "HUB-AMD", "status": "NORMAL", "priority": "CRITICAL", "vehicle": "IND-TRK-204", "weight": 250.0, "volume": 1.1, "hours_left": 12, "lat": 22.3072, "lng": 73.1812, "minutes_ago": 5},
        {"id": 36, "code": "SH036", "tracking": "SB-IND-SH036", "origin": "HUB-STV", "dest": "HUB-BOM", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-204", "weight": 790.0, "volume": 3.7, "hours_left": 10, "lat": 21.1702, "lng": 72.8311, "minutes_ago": 12},
        {"id": 37, "code": "SH037", "tracking": "SB-IND-SH037", "origin": "HUB-NOD", "dest": "HUB-LKO", "status": "DELAYED", "priority": "HIGH", "vehicle": "IND-TRK-309", "weight": 340.0, "volume": 1.6, "hours_left": -2, "lat": 28.5355, "lng": 77.3910, "minutes_ago": 40},
        {"id": 38, "code": "SH038", "tracking": "SB-IND-SH038", "origin": "HUB-IDR", "dest": "HUB-BOM", "status": "NORMAL_REROUTED", "priority": "NORMAL", "vehicle": "IND-TRK-930", "weight": 520.0, "volume": 2.4, "hours_left": 22, "lat": 22.7196, "lng": 75.8577, "minutes_ago": 15, "approved_reroute": True},
        {"id": 39, "code": "SH039", "tracking": "SB-IND-SH039", "origin": "HUB-IXR", "dest": "HUB-CCU", "status": "UNKNOWN_SIGNAL_MONITOR", "priority": "NORMAL", "vehicle": "IND-TRK-412", "weight": 410.0, "volume": 1.9, "hours_left": 14, "lat": 23.3441, "lng": 85.3096, "minutes_ago": 190},
        {"id": 40, "code": "SH040", "tracking": "SB-IND-SH040", "origin": "HUB-CJB", "dest": "HUB-MAA", "status": "NORMAL", "priority": "NORMAL", "vehicle": "IND-TRK-722", "weight": 880.0, "volume": 4.0, "hours_left": 16, "lat": 11.0168, "lng": 76.9558, "minutes_ago": 9},
    ]

    for sc in scenarios:
        deadline_time = now + timedelta(hours=sc["hours_left"]) if sc["hours_left"] >= 0 else now - timedelta(hours=abs(sc["hours_left"]))
        shipment = models.Shipment(
            shipment_id=sc["id"],
            tracking_number=sc["tracking"],
            origin_id=hubs_map[sc["origin"]].hub_id,
            destination_id=hubs_map[sc["dest"]].hub_id,
            expected_next_hub_id=hubs_map["HUB-HYD"].hub_id,
            assigned_vehicle_id=vehicles_map[sc["vehicle"]].vehicle_id,
            shipment_priority=sc["priority"],
            current_status=sc["status"],
            shipment_weight_kg=sc["weight"],
            shipment_volume_m3=sc["volume"],
            created_timestamp=now - timedelta(hours=8),
            delivery_deadline=deadline_time,
            is_synthetic=True
        )
        db.add(shipment)
        db.commit()
        db.refresh(shipment)

        # Seed Shipment Tracking
        tracking_times = [sc["minutes_ago"] + 20, sc["minutes_ago"] + 10, sc["minutes_ago"]] if sc.get("misplaced") else [sc["minutes_ago"]]
        for t_offset in tracking_times:
            tracking = models.ShipmentTracking(
                shipment_id=shipment.shipment_id,
                assigned_vehicle_id=shipment.assigned_vehicle_id,
                timestamp=now - timedelta(minutes=t_offset),
                current_lat=sc["lat"],
                current_lng=sc["lng"],
                speed_kmh=0.0 if sc["status"] == "UNKNOWN_SIGNAL_MONITOR" else 60.0,
                heading_degrees=140.0,
                gps_accuracy_meters=5.0 if not sc.get("gps_jitter") else 55.0,
                ble_gateway_id=sc["vehicle"],
                tracking_available=False if sc["status"] == "UNKNOWN_SIGNAL_MONITOR" else True,
                is_synthetic=True
            )
            db.add(tracking)

        if sc.get("approved_reroute"):
            execution = models.RecoveryExecution(
                shipment_id=shipment.shipment_id,
                assigned_vehicle_id=shipment.assigned_vehicle_id,
                pickup_hub_id=hubs_map["HUB-HYD"].hub_id,
                dropoff_hub_id=hubs_map["HUB-DEL"].hub_id,
                cost_saved=14500.0,
                co2_saved_kg=280.0,
                executed_timestamp=now - timedelta(hours=1),
                explanation="Approved reroute via Maharashtra corridor",
                is_synthetic=True
            )
            db.add(execution)

        if sc.get("misplaced"):
            reason = sc.get("no_route_reason", "3 consecutive off-route points detected (>15km deviation)")
            exception = models.ShipmentException(
                shipment_id=shipment.shipment_id,
                exception_type="MISPLACEMENT_DETECTED",
                severity="HIGH" if sc["priority"] in ["HIGH", "CRITICAL"] else "NORMAL",
                detected_timestamp=now - timedelta(minutes=sc["minutes_ago"]),
                confidence_score=0.95,
                exception_details=reason,
                is_synthetic=True
            )
            db.add(exception)

        # Seed FinalEvaluations (in INR ₹)
        if sc["code"] in ["SH003", "SH009", "SH010", "SH021"]:
            fe = models.FinalEvaluation(
                shipment_id=shipment.shipment_id,
                original_cost=18500.0,
                recovery_cost=3200.0,
                cost_saved=15300.0,
                total_savings=15300.0,
                co2_offset=280.0,
                time_saved_hours=14.5,
                deadline_met=True,
                recovery_success_status="SUCCESSFUL" if sc["code"] != "SH009" else "RECOVERY_RECOMMENDED",
                additional_distance_km=18.5,
            )
            db.add(fe)

    db.commit()

    # 5. Pre-seed Recovery Opportunities for misplaced shipments (SH009, SH011, SH012, SH020) in INR ₹
    opportunities_data = [
        # SH009: Direct Piggyback
        {
            "shipment_id": 9,
            "vehicle_id": vehicles_map["IND-TRK-101"].vehicle_id,
            "analysis_id": "REC-SH009-INIT",
            "candidate_route_id": routes_map["RTE-BLR-HYD-DEL"].route_id,
            "recovery_type": "DIRECT_PIGGYBACK",
            "pickup_hub_id": hubs_map["HUB-HYD"].hub_id,
            "drop_hub_id": hubs_map["HUB-DEL"].hub_id,
            "transfer_hub_id": None,
            "available_weight_kg": 18000.0,
            "remaining_weight_kg": 14200.0,
            "available_volume_m3": 45.0,
            "remaining_volume_m3": 32.0,
            "route_overlap_km": 1150.0,
            "detour_distance_km": 14.2,
            "additional_time_hours": 0.8,
            "estimated_delivery_time": now + timedelta(hours=14),
            "transfer_cost": 0.0,
            "additional_transport_cost": 2400.0,
            "estimated_total_cost": 2400.0,
            "deadline_feasible": True,
            "deadline_margin_minutes": 600,
            "deadline_risk": "LOW",
            "number_of_transfers": 0,
            "transfer_complexity": "DIRECT",
            "piggyback_score": 0.94,
            "feasible": True,
            "explanation": "Direct piggyback on vehicle IND-TRK-101 (RTE-BLR-HYD-DEL). Pickup at Hyderabad Hub, direct drop at Delhi Terminal. Saves ₹16,100 vs dedicated truck.",
            "rank": 1
        },
        # SH009: Hub Transfer Piggyback (Option #2 Alternative)
        {
            "shipment_id": 9,
            "vehicle_id": vehicles_map["IND-TRK-722"].vehicle_id,
            "analysis_id": "REC-SH009-INIT",
            "candidate_route_id": routes_map["RTE-MAA-HYD-LKO"].route_id,
            "recovery_type": "HUB_TRANSFER_PIGGYBACK",
            "pickup_hub_id": hubs_map["HUB-HYD"].hub_id,
            "drop_hub_id": hubs_map["HUB-DEL"].hub_id,
            "transfer_hub_id": hubs_map["HUB-LKO"].hub_id,
            "second_vehicle_id": vehicles_map["IND-TRK-309"].vehicle_id,
            "second_route_id": routes_map["RTE-LKO-DEL"].route_id,
            "available_weight_kg": 15000.0,
            "remaining_weight_kg": 9500.0,
            "available_volume_m3": 40.0,
            "remaining_volume_m3": 25.0,
            "route_overlap_km": 920.0,
            "detour_distance_km": 24.0,
            "additional_time_hours": 1.8,
            "estimated_delivery_time": now + timedelta(hours=17),
            "transfer_cost": 1200.0,
            "additional_transport_cost": 3000.0,
            "estimated_total_cost": 4200.0,
            "deadline_feasible": True,
            "deadline_margin_minutes": 420,
            "deadline_risk": "SAFE",
            "number_of_transfers": 1,
            "transfer_complexity": "SINGLE_TRANSFER",
            "piggyback_score": 0.84,
            "feasible": True,
            "explanation": "Hub transfer piggyback: Route RTE-MAA-HYD-LKO to Lucknow Hub, transfer to IND-TRK-309 (RTE-LKO-DEL). Saves ₹14,300 vs dedicated truck.",
            "rank": 2
        },
        # SH009: Two-Hop Piggyback (Option #3 Alternative)
        {
            "shipment_id": 9,
            "vehicle_id": vehicles_map["IND-TRK-550"].vehicle_id,
            "analysis_id": "REC-SH009-INIT",
            "candidate_route_id": routes_map["RTE-BOM-PNQ-AMD"].route_id,
            "recovery_type": "TWO_HOP_PIGGYBACK",
            "pickup_hub_id": hubs_map["HUB-HYD"].hub_id,
            "drop_hub_id": hubs_map["HUB-DEL"].hub_id,
            "transfer_hub_id": hubs_map["HUB-NAG"].hub_id,
            "second_vehicle_id": vehicles_map["IND-TRK-204"].vehicle_id,
            "second_route_id": routes_map["RTE-BOM-PNQ-AMD"].route_id,
            "available_weight_kg": 12000.0,
            "remaining_weight_kg": 7100.0,
            "available_volume_m3": 35.0,
            "remaining_volume_m3": 20.0,
            "route_overlap_km": 1050.0,
            "detour_distance_km": 36.0,
            "additional_time_hours": 2.8,
            "estimated_delivery_time": now + timedelta(hours=20),
            "transfer_cost": 1800.0,
            "additional_transport_cost": 4000.0,
            "estimated_total_cost": 5800.0,
            "deadline_feasible": True,
            "deadline_margin_minutes": 240,
            "deadline_risk": "SAFE",
            "number_of_transfers": 2,
            "transfer_complexity": "TWO_HOP",
            "piggyback_score": 0.74,
            "feasible": True,
            "explanation": "Two-hop piggyback transfer connecting Nagpur & Bhopal hubs before final leg to Delhi Terminal.",
            "rank": 3
        },
        # SH011: Hub Transfer Piggyback
        {
            "shipment_id": 11,
            "vehicle_id": vehicles_map["IND-TRK-608"].vehicle_id,
            "analysis_id": "REC-SH011-INIT",
            "candidate_route_id": routes_map["RTE-MAA-HYD-LKO"].route_id,
            "recovery_type": "HUB_TRANSFER_PIGGYBACK",
            "pickup_hub_id": hubs_map["HUB-HYD"].hub_id,
            "drop_hub_id": hubs_map["HUB-DEL"].hub_id,
            "transfer_hub_id": hubs_map["HUB-LKO"].hub_id,
            "second_vehicle_id": vehicles_map["IND-TRK-309"].vehicle_id,
            "second_route_id": routes_map["RTE-LKO-DEL"].route_id,
            "available_weight_kg": 15000.0,
            "remaining_weight_kg": 9800.0,
            "available_volume_m3": 40.0,
            "remaining_volume_m3": 22.0,
            "route_overlap_km": 890.0,
            "detour_distance_km": 28.5,
            "additional_time_hours": 2.2,
            "estimated_delivery_time": now + timedelta(hours=15),
            "transfer_cost": 1200.0,
            "additional_transport_cost": 3800.0,
            "estimated_total_cost": 5000.0,
            "deadline_feasible": True,
            "deadline_margin_minutes": 180,
            "deadline_risk": "MEDIUM",
            "number_of_transfers": 1,
            "transfer_complexity": "SINGLE_TRANSFER",
            "piggyback_score": 0.82,
            "feasible": True,
            "explanation": "Hub transfer piggyback: Route RTE-MAA-HYD-LKO to Lucknow Hub, transfer to IND-TRK-309 (RTE-LKO-DEL). Saves ₹13,500 vs dedicated truck.",
            "rank": 1
        },
        # SH012: Two-Hop Piggyback
        {
            "shipment_id": 12,
            "vehicle_id": vehicles_map["IND-TRK-722"].vehicle_id,
            "analysis_id": "REC-SH012-INIT",
            "candidate_route_id": routes_map["RTE-MAA-HYD-LKO"].route_id,
            "recovery_type": "TWO_HOP_PIGGYBACK",
            "pickup_hub_id": hubs_map["HUB-MAA"].hub_id,
            "drop_hub_id": hubs_map["HUB-DEL"].hub_id,
            "transfer_hub_id": hubs_map["HUB-LKO"].hub_id,
            "second_vehicle_id": vehicles_map["IND-TRK-309"].vehicle_id,
            "second_route_id": routes_map["RTE-LKO-DEL"].route_id,
            "available_weight_kg": 10000.0,
            "remaining_weight_kg": 6400.0,
            "available_volume_m3": 30.0,
            "remaining_volume_m3": 18.0,
            "route_overlap_km": 1420.0,
            "detour_distance_km": 42.0,
            "additional_time_hours": 3.5,
            "estimated_delivery_time": now + timedelta(hours=22),
            "transfer_cost": 2200.0,
            "additional_transport_cost": 4600.0,
            "estimated_total_cost": 6800.0,
            "deadline_feasible": True,
            "deadline_margin_minutes": 480,
            "deadline_risk": "LOW",
            "number_of_transfers": 2,
            "transfer_complexity": "TWO_HOP",
            "piggyback_score": 0.76,
            "feasible": True,
            "explanation": "Two-hop piggyback transfer connecting Kochi cargo via Chennai & Lucknow hubs to Delhi Terminal.",
            "rank": 1
        },
        # SH020: Direct Piggyback Alternative
        {
            "shipment_id": 20,
            "vehicle_id": vehicles_map["IND-TRK-204"].vehicle_id,
            "analysis_id": "REC-SH020-INIT",
            "candidate_route_id": routes_map["RTE-BOM-PNQ-AMD"].route_id,
            "recovery_type": "DIRECT_PIGGYBACK",
            "pickup_hub_id": hubs_map["HUB-NAG"].hub_id,
            "drop_hub_id": hubs_map["HUB-CCU"].hub_id,
            "available_weight_kg": 9500.0,
            "remaining_weight_kg": 5200.0,
            "available_volume_m3": 28.0,
            "remaining_volume_m3": 16.0,
            "route_overlap_km": 780.0,
            "detour_distance_km": 18.0,
            "additional_time_hours": 1.2,
            "estimated_delivery_time": now + timedelta(hours=20),
            "transfer_cost": 0.0,
            "additional_transport_cost": 3100.0,
            "estimated_total_cost": 3100.0,
            "deadline_feasible": True,
            "deadline_margin_minutes": 480,
            "deadline_risk": "LOW",
            "number_of_transfers": 0,
            "transfer_complexity": "DIRECT",
            "piggyback_score": 0.88,
            "feasible": True,
            "explanation": "Direct piggyback on vehicle IND-TRK-204 via Central India corridor.",
            "rank": 1
        }
    ]

    for opp in opportunities_data:
        rec_opp = models.RecoveryOpportunity(
            shipment_id=opp["shipment_id"],
            vehicle_id=opp["vehicle_id"],
            analysis_id=opp["analysis_id"],
            candidate_route_id=opp["candidate_route_id"],
            recovery_type=opp["recovery_type"],
            pickup_hub_id=opp["pickup_hub_id"],
            drop_hub_id=opp["drop_hub_id"],
            transfer_hub_id=opp.get("transfer_hub_id"),
            second_vehicle_id=opp.get("second_vehicle_id"),
            second_route_id=opp.get("second_route_id"),
            available_weight_kg=opp["available_weight_kg"],
            remaining_weight_kg=opp["remaining_weight_kg"],
            available_volume_m3=opp["available_volume_m3"],
            remaining_volume_m3=opp["remaining_volume_m3"],
            route_overlap_km=opp["route_overlap_km"],
            detour_distance_km=opp["detour_distance_km"],
            additional_time_hours=opp["additional_time_hours"],
            estimated_delivery_time=opp["estimated_delivery_time"],
            transfer_cost=opp["transfer_cost"],
            additional_transport_cost=opp["additional_transport_cost"],
            estimated_total_cost=opp["estimated_total_cost"],
            deadline_feasible=opp["deadline_feasible"],
            deadline_margin_minutes=opp["deadline_margin_minutes"],
            deadline_risk=opp["deadline_risk"],
            number_of_transfers=opp["number_of_transfers"],
            transfer_complexity=opp["transfer_complexity"],
            piggyback_score=opp["piggyback_score"],
            feasible=opp["feasible"],
            explanation=opp["explanation"],
            rank=opp["rank"],
        )
        db.add(rec_opp)

    db.commit()
    print("40 Controlled Scenarios (SH001 through SH040) across India successfully seeded in MySQL database!")
