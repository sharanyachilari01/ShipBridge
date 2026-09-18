from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models, schemas, crud, piggyback, seed
from app.database import engine, get_db, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE

app = FastAPI(
    title="ShipBridge — Intelligent Shipment Recovery API (MySQL Aligned)",
    description="Backend service aligned with MySQL schema.",
    version="2.1.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    # Ensure tables exist & seed demo data if database is empty
    models.Base.metadata.create_all(bind=engine)
    db = next(get_db())
    if db.query(models.Hub).count() == 0:
        seed.seed_database(db, reseed_synthetic_only=False)


@app.get("/api/health", summary="Health check endpoint with database connectivity details")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        hubs_count = db.query(models.Hub).count()
        shipments_count = db.query(models.Shipment).count()

        return {
            "status": "ok",
            "database": {
                "connected": True,
                "type": "mysql",
                "host": MYSQL_HOST,
                "port": MYSQL_PORT,
                "name": MYSQL_DATABASE,
            },
            "metrics": {
                "hubs_loaded": hubs_count,
                "total_shipments": shipments_count,
            },
            "message": "ShipBridge India Logistics Engine operational (MySQL Aligned)"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": {
                "connected": False,
                "type": "mysql",
                "host": MYSQL_HOST,
                "port": MYSQL_PORT,
                "name": MYSQL_DATABASE,
                "error": str(e)
            }
        }


@app.post("/api/admin/seed/reset", summary="Reseed synthetic demo network data")
def admin_seed_reset(db: Session = Depends(get_db)):
    seed.seed_database(db, reseed_synthetic_only=True)
    return {
        "status": "ok",
        "message": "Synthetic India demo network reseeded successfully. Synthetic records updated, real data preserved."
    }


@app.get("/api/hubs", response_model=List[schemas.HubResponse])
def read_hubs(db: Session = Depends(get_db)):
    return crud.get_hubs(db)


@app.get("/api/vehicles", response_model=List[schemas.VehicleResponse])
def read_vehicles(db: Session = Depends(get_db)):
    return crud.get_vehicles(db)


@app.get("/api/shipments", response_model=List[schemas.ShipmentResponse])
def read_shipments(status: Optional[str] = None, db: Session = Depends(get_db)):
    shipments = crud.get_shipments(db, status=status)
    results = []
    for shp in shipments:
        latest_tracking = (
            db.query(models.ShipmentTracking)
            .filter(models.ShipmentTracking.shipment_id == shp.shipment_id)
            .order_by(models.ShipmentTracking.timestamp.desc())
            .first()
        )
        hub = shp.expected_next_hub or shp.origin_hub
        current_lat = float(latest_tracking.current_lat) if (latest_tracking and latest_tracking.current_lat) else (float(hub.latitude) if hub else 17.3850)
        current_lng = float(latest_tracking.current_lng) if (latest_tracking and latest_tracking.current_lng) else (float(hub.longitude) if hub else 78.4867)

        resp = schemas.ShipmentResponse(
            id=shp.shipment_id,
            shipment_id=str(shp.shipment_id),
            tracking_number=shp.tracking_number,
            origin_hub_id=shp.origin_id,
            destination_hub_id=shp.destination_id,
            expected_next_hub_id=shp.expected_next_hub_id,
            assigned_vehicle_id=shp.assigned_vehicle_id,
            priority=shp.shipment_priority,
            status=shp.current_status,
            weight_kg=float(shp.shipment_weight_kg),
            delivery_deadline=shp.delivery_deadline,
            expected_arrival_time=shp.created_timestamp,
            created_at=shp.created_timestamp,
            updated_at=shp.created_timestamp,
            is_synthetic=shp.is_synthetic,
            origin_hub=schemas.HubResponse.model_validate(shp.origin_hub) if shp.origin_hub else None,
            destination_hub=schemas.HubResponse.model_validate(shp.destination_hub) if shp.destination_hub else None,
            expected_next_hub=schemas.HubResponse.model_validate(shp.expected_next_hub) if shp.expected_next_hub else None,
            assigned_vehicle=schemas.VehicleResponse.model_validate(shp.assigned_vehicle) if shp.assigned_vehicle else None,
            current_lat=current_lat,
            current_lng=current_lng
        )
        results.append(resp)
    return results


@app.get("/api/shipments/{shipment_id}", response_model=schemas.ShipmentResponse)
def read_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = crud.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    latest_tracking = (
        db.query(models.ShipmentTracking)
        .filter(models.ShipmentTracking.shipment_id == shipment.shipment_id)
        .order_by(models.ShipmentTracking.timestamp.desc())
        .first()
    )
    hub = shipment.expected_next_hub or shipment.origin_hub
    current_lat = float(latest_tracking.current_lat) if (latest_tracking and latest_tracking.current_lat) else (float(hub.latitude) if hub else 17.3850)
    current_lng = float(latest_tracking.current_lng) if (latest_tracking and latest_tracking.current_lng) else (float(hub.longitude) if hub else 78.4867)

    return schemas.ShipmentResponse(
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
        assigned_vehicle=schemas.VehicleResponse.model_validate(shipment.assigned_vehicle) if shipment.assigned_vehicle else None,
        current_lat=current_lat,
        current_lng=current_lng
    )


@app.post("/api/shipments", response_model=schemas.ShipmentResponse)
def create_shipment(shipment_in: schemas.ShipmentCreate, db: Session = Depends(get_db)):
    shp = crud.create_shipment(db, shipment_in)
    return read_shipment(shp.shipment_id, db)


@app.post("/api/shipments/{shipment_id}/mark-misplaced", response_model=schemas.ShipmentResponse)
def mark_misplaced(shipment_id: int, notes: Optional[str] = None, db: Session = Depends(get_db)):
    shp = crud.mark_shipment_misplaced(db, shipment_id, notes=notes)
    if not shp:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return read_shipment(shp.shipment_id, db)


@app.get("/api/routes", response_model=List[schemas.VehicleRouteResponse])
def read_routes(db: Session = Depends(get_db)):
    return crud.get_routes(db)


@app.get("/api/recovery/recommendations", response_model=List[schemas.PiggybackRecommendation])
def get_piggyback_recommendations(shipment_id: Optional[int] = None, db: Session = Depends(get_db)):
    return piggyback.find_piggyback_recommendations(db, shipment_id=shipment_id)


@app.post("/api/recovery/accept", response_model=schemas.RecoveryPlanResponse)
def accept_recovery_plan(plan_req: schemas.AcceptRecoveryRequest, db: Session = Depends(get_db)):
    return crud.accept_recovery_plan(db, plan_req)


@app.get("/api/impact", response_model=schemas.ImpactMetrics)
def get_impact_metrics(db: Session = Depends(get_db)):
    return crud.get_impact_metrics(db)


from app.detection import service as detection_service


@app.post("/api/v1/detection/check", response_model=schemas.DetectionCheckResponse)
def check_shipment_detection(req: schemas.DetectionCheckRequest, db: Session = Depends(get_db)):
    try:
        domain_result = detection_service.evaluate_and_persist_shipment(db, req.shipment_id)
        return schemas.DetectionCheckResponse(
            alert_id=domain_result.alert_id,
            shipment_id=domain_result.shipment_id,
            status=domain_result.status,
            misplacement_score=domain_result.misplacement_score,
            location=domain_result.location,
            assigned_vehicle=domain_result.assigned_vehicle,
            distance_to_primary_route_km=domain_result.distance_to_primary_route_km,
            distance_to_nearest_valid_route_km=domain_result.distance_to_nearest_valid_route_km,
            heading_difference_deg=domain_result.heading_difference_deg,
            persistent_anomaly=domain_result.persistent_anomaly,
            safeguard_outcomes=schemas.SafeguardOutcomesSchema(**domain_result.safeguard_outcomes.to_dict()),
            primary_cause=domain_result.primary_cause,
            explanation=domain_result.explanation,
            timestamp=domain_result.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/shipments/{shipment_id}/status", response_model=schemas.DetectionCheckResponse)
def get_shipment_detection_status(shipment_id: str, db: Session = Depends(get_db)):
    try:
        domain_result = detection_service.evaluate_and_persist_shipment(db, shipment_id)
        return schemas.DetectionCheckResponse(
            alert_id=domain_result.alert_id,
            shipment_id=domain_result.shipment_id,
            status=domain_result.status,
            misplacement_score=domain_result.misplacement_score,
            location=domain_result.location,
            assigned_vehicle=domain_result.assigned_vehicle,
            distance_to_primary_route_km=domain_result.distance_to_primary_route_km,
            distance_to_nearest_valid_route_km=domain_result.distance_to_nearest_valid_route_km,
            heading_difference_deg=domain_result.heading_difference_deg,
            persistent_anomaly=domain_result.persistent_anomaly,
            safeguard_outcomes=schemas.SafeguardOutcomesSchema(**domain_result.safeguard_outcomes.to_dict()),
            primary_cause=domain_result.primary_cause,
            explanation=domain_result.explanation,
            timestamp=domain_result.timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/detection/history")
def get_detection_history(db: Session = Depends(get_db)):
    exceptions = db.query(models.ShipmentException).order_by(models.ShipmentException.detected_timestamp.desc()).all()
    results = []
    for exc in exceptions:
        results.append({
            "exception_id": exc.exception_id,
            "shipment_id": exc.shipment_id,
            "exception_type": exc.exception_type,
            "severity": exc.severity,
            "detected_timestamp": exc.detected_timestamp,
            "confidence_score": exc.confidence_score,
            "exception_details": exc.exception_details,
        })
    return results


@app.get("/api/v1/demo/shipments", response_model=List[schemas.DemoShipmentAnalysis])
def get_demo_shipments_analysis(db: Session = Depends(get_db)):
    return detection_service.evaluate_all_demo_shipments(db)


@app.get("/api/v1/evaluations", response_model=List[schemas.FinalEvaluationResponse])
@app.get("/api/evaluations", response_model=List[schemas.FinalEvaluationResponse])
def read_final_evaluations(db: Session = Depends(get_db)):
    evals = crud.get_final_evaluations(db)
    results = []
    for ev in evals:
        shp = ev.shipment
        tracking_num = shp.tracking_number if shp else f"SB-IND-SH{ev.shipment_id:03d}"
        results.append(schemas.FinalEvaluationResponse(
            id=ev.evaluation_id,
            evaluation_id=ev.evaluation_id,
            shipment_id=ev.shipment_id,
            tracking_number=tracking_num,
            original_cost=float(ev.original_cost or 0.0),
            recovery_cost=float(ev.recovery_cost or 0.0),
            cost_saved=float(ev.cost_saved or ev.total_savings or 0.0),
            total_savings=float(ev.total_savings or 0.0),
            co2_offset=float(ev.co2_offset or 0.0),
            time_saved_hours=float(ev.time_saved_hours or 0.0),
            deadline_met=ev.deadline_met,
            recovery_success_status=ev.recovery_success_status,
            additional_distance_km=float(ev.additional_distance_km or 0.0),
        ))
    return results


@app.get("/api/v1/evaluations/{shipment_id}", response_model=schemas.FinalEvaluationResponse)
@app.get("/api/evaluations/{shipment_id}", response_model=schemas.FinalEvaluationResponse)
def read_final_evaluation(shipment_id: int, db: Session = Depends(get_db)):
    ev = crud.get_final_evaluation(db, shipment_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Final evaluation not found for shipment")
    shp = ev.shipment
    tracking_num = shp.tracking_number if shp else f"SB-IND-SH{ev.shipment_id:03d}"
    return schemas.FinalEvaluationResponse(
        id=ev.evaluation_id,
        evaluation_id=ev.evaluation_id,
        shipment_id=ev.shipment_id,
        tracking_number=tracking_num,
        original_cost=float(ev.original_cost or 0.0),
        recovery_cost=float(ev.recovery_cost or 0.0),
        cost_saved=float(ev.cost_saved or ev.total_savings or 0.0),
        total_savings=float(ev.total_savings or 0.0),
        co2_offset=float(ev.co2_offset or 0.0),
        time_saved_hours=float(ev.time_saved_hours or 0.0),
        deadline_met=ev.deadline_met,
        recovery_success_status=ev.recovery_success_status,
        additional_distance_km=float(ev.additional_distance_km or 0.0),
    )


@app.get("/api/v1/exceptions", response_model=List[schemas.ShipmentExceptionResponse])
@app.get("/api/exceptions", response_model=List[schemas.ShipmentExceptionResponse])
def read_shipment_exceptions(db: Session = Depends(get_db)):
    exceptions = crud.get_shipment_exceptions(db)
    results = []
    for exc in exceptions:
        shp = exc.shipment
        tracking_num = shp.tracking_number if shp else f"SB-IND-SH{exc.shipment_id:03d}"
        results.append(schemas.ShipmentExceptionResponse(
            id=exc.exception_id,
            exception_id=exc.exception_id,
            shipment_id=exc.shipment_id,
            tracking_number=tracking_num,
            exception_type=exc.exception_type,
            severity=exc.severity,
            detected_timestamp=exc.detected_timestamp,
            confidence_score=float(exc.confidence_score),
            exception_details=exc.exception_details,
            is_synthetic=exc.is_synthetic,
        ))
    return results


