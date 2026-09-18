"""
Data adapter connecting SQLAlchemy models to domain models.
"""

import json
from datetime import datetime
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app import models
from app.piggybacking_engine.models import (
    CandidateVehicleDomain,
    CandidateHubDomain,
    CandidateRouteDomain,
    Location,
    PiggybackOptionDomain,
    LegDetail,
)


class DataAdapter:
    @staticmethod
    def get_shipment_and_location(
        db: Session, shipment_id: int
    ) -> Tuple[Optional[models.Shipment], Optional[Location], Optional[str]]:
        """
        Fetch shipment by ID and find its latest telemetry location.
        Returns (shipment_model, Location, ineligibility_reason).
        """
        shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
        if not shipment:
            return None, None, "SHIPMENT_NOT_FOUND"

        if (shipment.current_status or "").upper() != "MISPLACED":
            return shipment, None, "SHIPMENT_NOT_ELIGIBLE"

        # Find latest tracking record
        tracking = (
            db.query(models.ShipmentTracking)
            .filter(models.ShipmentTracking.shipment_id == shipment_id)
            .order_by(models.ShipmentTracking.timestamp.desc())
            .first()
        )

        if tracking and tracking.current_lat is not None and tracking.current_lng is not None:
            location = Location(
                latitude=float(tracking.current_lat),
                longitude=float(tracking.current_lng),
            )
            return shipment, location, None

        # Fallback to expected_next_hub or origin_hub
        hub = shipment.expected_next_hub or shipment.origin_hub
        if hub and hub.latitude is not None and hub.longitude is not None:
            location = Location(
                latitude=float(hub.latitude),
                longitude=float(hub.longitude),
            )
            return shipment, location, None

        return shipment, None, "LOCATION_UNAVAILABLE"

    @staticmethod
    def get_all_hubs(db: Session) -> List[CandidateHubDomain]:
        hubs = db.query(models.Hub).filter(models.Hub.active == True).all()
        return [
            CandidateHubDomain(
                hub_id=h.hub_id,
                code=h.code or f"HUB-{h.hub_id}",
                name=h.name or f"Hub {h.hub_id}",
                city=h.city or "",
                state=h.state or "",
                latitude=float(h.latitude) if h.latitude else 0.0,
                longitude=float(h.longitude) if h.longitude else 0.0,
                active=bool(h.active),
            )
            for h in hubs
        ]

    @staticmethod
    def get_all_vehicles(db: Session) -> List[CandidateVehicleDomain]:
        vehicles = db.query(models.Vehicle).all()
        result = []
        for v in vehicles:
            cap_kg = float(v.capacity_kg) if v.capacity_kg else 10000.0
            cap_m3 = round(cap_kg / 250.0, 2)
            
            # Find latest tracking for vehicle's position if any
            v_tracking = (
                db.query(models.ShipmentTracking)
                .filter(models.ShipmentTracking.assigned_vehicle_id == v.vehicle_id)
                .order_by(models.ShipmentTracking.timestamp.desc())
                .first()
            )
            v_lat = float(v_tracking.current_lat) if v_tracking and v_tracking.current_lat else None
            v_lng = float(v_tracking.current_lng) if v_tracking and v_tracking.current_lng else None

            # Find active vehicle route
            v_route = (
                db.query(models.VehicleRoute)
                .filter(models.VehicleRoute.vehicle_id == v.vehicle_id)
                .first()
            )
            current_route_id = v_route.route_id if v_route else None

            result.append(
                CandidateVehicleDomain(
                    vehicle_id=v.vehicle_id,
                    vehicle_code=v.vehicle_code or f"VEH-{v.vehicle_id}",
                    status=v.status or "IDLE",
                    weight_capacity_kg=cap_kg,
                    volume_capacity_m3=cap_m3,
                    assigned_hub_id=v.assigned_hub_id,
                    current_lat=v_lat,
                    current_lng=v_lng,
                    current_route_id=current_route_id,
                )
            )
        return result

    @staticmethod
    def get_all_routes(db: Session) -> List[CandidateRouteDomain]:
        routes = db.query(models.RouteNetwork).filter(models.RouteNetwork.active == True).all()
        result = []
        for r in routes:
            geom = []
            if r.route_geometry_json:
                try:
                    geom = json.loads(r.route_geometry_json)
                except Exception:
                    geom = []
            result.append(
                CandidateRouteDomain(
                    route_id=r.route_id,
                    route_code=r.route_code or f"RTE-{r.route_id}",
                    origin_hub_id=r.origin_hub_id,
                    destination_hub_id=r.destination_hub_id,
                    route_geometry=geom,
                    active=bool(r.active),
                )
            )
        return result

    @staticmethod
    def save_analysis_and_opportunities(
        db: Session,
        analysis_id: str,
        shipment_id: int,
        status: str,
        total_candidates: int,
        feasible_count: int,
        options: List[PiggybackOptionDomain],
        summary: dict,
    ) -> Tuple[models.PiggybackAnalysisRun, List[models.RecoveryOpportunity]]:
        """
        Persist PiggybackAnalysisRun and RecoveryOpportunity models.
        If run exists for analysis_id, update it rather than creating duplicate.
        """
        # Check existing run
        run = (
            db.query(models.PiggybackAnalysisRun)
            .filter(models.PiggybackAnalysisRun.analysis_id == analysis_id)
            .first()
        )
        if not run:
            run = models.PiggybackAnalysisRun(
                analysis_id=analysis_id,
                shipment_id=shipment_id,
                status=status,
                candidates_found_count=total_candidates,
                feasible_candidates_count=feasible_count,
                created_at=datetime.utcnow(),
                summary_json=json.dumps(summary),
            )
            db.add(run)
        else:
            run.status = status
            run.candidates_found_count = total_candidates
            run.feasible_candidates_count = feasible_count
            run.summary_json = json.dumps(summary)

        db.flush()

        # Delete existing opportunities for this analysis run to ensure clean overwrite
        db.query(models.RecoveryOpportunity).filter(
            models.RecoveryOpportunity.analysis_id == analysis_id
        ).delete(synchronize_session=False)

        saved_opportunities = []
        for opt in options:
            opp = models.RecoveryOpportunity(
                shipment_id=opt.shipment_id,
                vehicle_id=opt.vehicle_id,
                analysis_id=analysis_id,
                candidate_route_id=opt.route_id,
                recovery_type="DIRECT_PIGGYBACK" if opt.is_direct_piggyback else ("TWO_HOP_PIGGYBACK" if opt.number_of_transfers == 1 else "MULTI_TRANSFER"),
                pickup_hub_id=opt.pickup_hub_id,
                drop_hub_id=opt.drop_hub_id,
                transfer_hub_id=opt.legs[0].to_hub_id if len(opt.legs) > 1 else None,
                second_vehicle_id=opt.legs[1].vehicle_id if len(opt.legs) > 1 else None,
                second_route_id=opt.legs[1].route_id if len(opt.legs) > 1 else None,
                available_weight_kg=opt.available_weight_capacity_kg,
                remaining_weight_kg=opt.remaining_weight_capacity_kg,
                available_volume_m3=opt.available_volume_capacity_m3,
                remaining_volume_m3=opt.remaining_volume_capacity_m3,
                route_overlap_km=opt.route_overlap_km,
                detour_distance_km=opt.detour_distance_km,
                additional_time_hours=opt.additional_time_hours,
                estimated_delivery_time=opt.estimated_delivery_time,
                transfer_cost=opt.transfer_cost,
                additional_transport_cost=opt.transport_cost,
                estimated_total_cost=opt.estimated_total_cost,
                deadline_feasible=opt.is_feasible and (opt.deadline_margin_hours >= 0),
                deadline_margin_minutes=int(opt.deadline_margin_hours * 60),
                deadline_risk=opt.deadline_risk_level,
                number_of_transfers=opt.number_of_transfers,
                transfer_complexity=opt.transfer_complexity,
                piggyback_score=opt.piggyback_score,
                match_score=int(opt.piggyback_score * 100),
                potential_cost_saved=opt.cost_savings_vs_dedicated,
                potential_co2_saved=round(opt.cost_savings_vs_dedicated * 0.15, 2),
                score_distance=opt.component_scores.distance_score,
                score_time=opt.component_scores.time_score,
                score_cost=opt.component_scores.cost_score,
                score_deadline=opt.component_scores.deadline_score,
                score_capacity=opt.component_scores.capacity_score,
                score_route=opt.component_scores.route_score,
                score_transfer=opt.component_scores.transfer_score,
                feasible=opt.is_feasible,
                rejection_reason=", ".join(opt.rejection_reasons) if opt.rejection_reasons else None,
                explanation=opt.explanation,
                concerns_json=json.dumps(opt.concerns),
                rank=opt.rank,
                status="RECOMMENDED" if opt.is_feasible else "REJECTED",
            )
            db.add(opp)
            saved_opportunities.append(opp)

        db.commit()
        return run, saved_opportunities
