"""
Database Repositories for Stage 3 Recovery Selection, Decisions, and Impact Analysis.
"""

import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from app import models
from app.recovery_selection.models import (
    EvaluatedOptionDomain,
    Stage3ImpactMetrics,
    Stage3ComponentScores,
)


class SelectionRepository:
    @staticmethod
    def get_feasible_stage2_opportunities(
        db: Session, shipment_id: int
    ) -> Tuple[Optional[models.Shipment], List[EvaluatedOptionDomain]]:
        """
        Retrieves shipment and all feasible Stage 2 recovery opportunities from recovery_opportunity_table.
        Filters by the latest analysis run and deduplicates using canonical uniqueness key.
        """
        shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
        if not shipment:
            return None, []

        latest_run = (
            db.query(models.PiggybackAnalysisRun)
            .filter(models.PiggybackAnalysisRun.shipment_id == shipment_id)
            .order_by(models.PiggybackAnalysisRun.created_at.desc())
            .first()
        )

        query_builder = db.query(models.RecoveryOpportunity).filter(
            models.RecoveryOpportunity.shipment_id == shipment_id,
            models.RecoveryOpportunity.feasible == True,
            or_(
                models.RecoveryOpportunity.deadline_feasible == True,
                models.RecoveryOpportunity.deadline_feasible.is_(None)
            ),
        )
        if latest_run and latest_run.analysis_id:
            query_builder = query_builder.filter(models.RecoveryOpportunity.analysis_id == latest_run.analysis_id)

        query = query_builder.all()

        seen_keys = set()
        domain_options: List[EvaluatedOptionDomain] = []
        for opp in query:
            canon_key = (
                opp.analysis_id or "",
                opp.shipment_id,
                opp.recovery_type or "",
                opp.vehicle_id,
                opp.second_vehicle_id or 0,
                opp.candidate_route_id or 0,
                opp.second_route_id or 0,
                opp.pickup_hub_id or 0,
                opp.transfer_hub_id or 0,
                opp.drop_hub_id or 0,
            )
            if canon_key in seen_keys:
                continue
            seen_keys.add(canon_key)
            # Parse route geometry if JSON
            geom = []
            if opp.candidate_route and opp.candidate_route.route_geometry_json:
                try:
                    geom = json.loads(opp.candidate_route.route_geometry_json)
                except Exception:
                    geom = []

            avail_wt = float(opp.available_weight_kg) if opp.available_weight_kg else 10000.0
            rem_wt = float(opp.remaining_weight_kg) if opp.remaining_weight_kg else 5000.0
            avail_vol = float(opp.available_volume_m3) if opp.available_volume_m3 else 40.0
            rem_vol = float(opp.remaining_volume_m3) if opp.remaining_volume_m3 else 20.0

            # Estimate utilization
            used_wt = max(0.0, avail_wt - rem_wt)
            wt_util = (used_wt / avail_wt * 100.0) if avail_wt > 0 else 50.0
            used_vol = max(0.0, avail_vol - rem_vol)
            vol_util = (used_vol / avail_vol * 100.0) if avail_vol > 0 else 50.0
            cap_util = round(max(wt_util, vol_util), 1)

            impact = Stage3ImpactMetrics(
                baseline_recovery_cost=1500.0,
                selected_recovery_cost=float(opp.estimated_total_cost or 20.0),
                estimated_cost_savings=max(0.0, 1500.0 - float(opp.estimated_total_cost or 20.0)),
                baseline_delivery_time=shipment.delivery_deadline,
                selected_delivery_time=opp.estimated_delivery_time or datetime.utcnow(),
                delivery_time_change_minutes=0,
                deadline_margin_minutes=int(opp.deadline_margin_minutes or 300),
                additional_distance_km=float(opp.detour_distance_km or 0.0),
                additional_time_hours=float(opp.additional_time_hours or 0.0),
                number_of_transfers=int(opp.number_of_transfers or 0),
                transfer_complexity=opp.transfer_complexity or "DIRECT",
                deadline_risk=opp.deadline_risk or "LOW",
                vehicle_available_weight_kg=avail_wt,
                vehicle_available_volume_m3=avail_vol,
                remaining_weight_capacity_kg=rem_wt,
                remaining_volume_capacity_m3=rem_vol,
                capacity_utilization_after_percent=cap_util,
                is_high_capacity_utilization=cap_util >= 85.0,
                impact_summary=opp.explanation or "",
            )

            # Route code & vehicle code
            v_code = opp.vehicle.vehicle_code if opp.vehicle else f"TRK-{opp.vehicle_id}"
            r_code = opp.candidate_route.route_code if opp.candidate_route else f"RTE-{opp.candidate_route_id or 1}"
            p_name = opp.pickup_hub.name if opp.pickup_hub else "Pickup Hub"
            d_name = opp.drop_hub.name if opp.drop_hub else "Dropoff Hub"

            domain_options.append(
                EvaluatedOptionDomain(
                    opportunity_id=opp.opportunity_id,
                    shipment_id=shipment_id,
                    vehicle_id=opp.vehicle_id,
                    vehicle_code=v_code,
                    route_id=opp.candidate_route_id,
                    route_code=r_code,
                    pickup_hub_id=opp.pickup_hub_id,
                    pickup_hub_name=p_name,
                    drop_hub_id=opp.drop_hub_id,
                    drop_hub_name=d_name,
                    is_direct_piggyback=(opp.recovery_type == "DIRECT_PIGGYBACK" or opp.number_of_transfers == 0),
                    number_of_transfers=int(opp.number_of_transfers or 0),
                    estimated_total_cost=float(opp.estimated_total_cost or 20.0),
                    estimated_delivery_time=opp.estimated_delivery_time or datetime.utcnow(),
                    deadline_margin_minutes=int(opp.deadline_margin_minutes or 300),
                    stage2_piggyback_score=float(opp.piggyback_score or 0.8),
                    remaining_weight_capacity_kg=rem_wt,
                    remaining_volume_capacity_m3=rem_vol,
                    impact_metrics=impact,
                    explanation=opp.explanation or "",
                    route_geometry=geom,
                )
            )

        return shipment, domain_options

    @staticmethod
    def save_recommendation_and_snapshot(
        db: Session,
        recommendation_id: str,
        shipment_id: int,
        analysis_id: Optional[str],
        recommended_option: Optional[EvaluatedOptionDomain],
        reason: str,
    ) -> models.RecoveryRecommendation:
        """
        Persists Stage 3 recommendation and impact snapshot.
        Supersedes any existing PENDING_REVIEW recommendation for the shipment.
        """
        # Supersede existing pending recommendations for this shipment
        db.query(models.RecoveryRecommendation).filter(
            models.RecoveryRecommendation.shipment_id == shipment_id,
            models.RecoveryRecommendation.recommendation_status == "PENDING_REVIEW"
        ).update({"recommendation_status": "SUPERSEDED"}, synchronize_session=False)

        rec = models.RecoveryRecommendation(
            recommendation_id=recommendation_id,
            analysis_id=analysis_id,
            shipment_id=shipment_id,
            selected_opportunity_id=recommended_option.opportunity_id if recommended_option else None,
            recommendation_status="PENDING_REVIEW" if recommended_option else "NO_FEASIBLE_RECOVERY_OPTIONS",
            recommendation_score=recommended_option.selection_score if recommended_option else 0.0,
            recommendation_reason=reason,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(rec)
        db.flush()

        if recommended_option and recommended_option.impact_metrics:
            metrics = recommended_option.impact_metrics
            snap = models.RecoveryImpactSnapshot(
                shipment_id=shipment_id,
                selected_opportunity_id=recommended_option.opportunity_id,
                baseline_recovery_cost=metrics.baseline_recovery_cost,
                selected_recovery_cost=metrics.selected_recovery_cost,
                estimated_cost_savings=metrics.estimated_cost_savings,
                baseline_delivery_time=metrics.baseline_delivery_time,
                selected_delivery_time=metrics.selected_delivery_time,
                delivery_time_change_minutes=metrics.delivery_time_change_minutes,
                deadline_margin_minutes=metrics.deadline_margin_minutes,
                additional_distance_km=metrics.additional_distance_km,
                capacity_utilization_after=metrics.capacity_utilization_after_percent,
                number_of_transfers=metrics.number_of_transfers,
                impact_summary=metrics.impact_summary,
                created_at=datetime.utcnow(),
            )
            db.add(snap)

        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_latest_recommendation(db: Session, shipment_id: int) -> Optional[models.RecoveryRecommendation]:
        return (
            db.query(models.RecoveryRecommendation)
            .filter(models.RecoveryRecommendation.shipment_id == shipment_id)
            .order_by(models.RecoveryRecommendation.created_at.desc())
            .first()
        )

    @staticmethod
    def record_decision(
        db: Session,
        recommendation_id: str,
        decision_str: str,  # APPROVED or REJECTED
        dispatcher_name: str,
        decision_note: Optional[str],
        selected_opportunity_id: Optional[int] = None,
    ) -> Tuple[models.RecoveryRecommendation, models.RecoveryDecision]:
        """
        Records dispatcher decision (APPROVED/REJECTED) and updates recommendation status.
        If APPROVED, updates shipment.current_status to RECOVERY_APPROVED.
        DOES NOT reassign vehicle, change capacity, or execute physical dispatch.
        """
        rec = (
            db.query(models.RecoveryRecommendation)
            .filter(models.RecoveryRecommendation.recommendation_id == recommendation_id)
            .first()
        )
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        rec.recommendation_status = decision_str
        if selected_opportunity_id:
            rec.selected_opportunity_id = selected_opportunity_id
        rec.updated_at = datetime.utcnow()

        dec = models.RecoveryDecision(
            recommendation_id=recommendation_id,
            selected_opportunity_id=selected_opportunity_id or rec.selected_opportunity_id,
            decision=decision_str,
            dispatcher_name=dispatcher_name,
            decision_note=decision_note,
            decided_at=datetime.utcnow(),
        )
        db.add(dec)

        # Update shipment status ONLY to RECOVERY_APPROVED when approved
        if decision_str == "APPROVED":
            shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == rec.shipment_id).first()
            if shipment:
                shipment.current_status = "RECOVERY_APPROVED"

        db.commit()
        db.refresh(rec)
        db.refresh(dec)
        return rec, dec

    @staticmethod
    def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
        """
        Aggregates dashboard impact metrics and briefing panel data.
        """
        total_misplaced = db.query(models.Shipment).filter(models.Shipment.current_status.in_(["MISPLACED", "RECOVERY_APPROVED"])).count()
        
        # Shipments with feasible options
        shipments_with_feasible = (
            db.query(models.RecoveryOpportunity.shipment_id)
            .filter(models.RecoveryOpportunity.feasible == True)
            .distinct()
            .count()
        )

        pending_reviews = (
            db.query(models.RecoveryRecommendation)
            .filter(models.RecoveryRecommendation.recommendation_status == "PENDING_REVIEW")
            .count()
        )

        approved_recs = (
            db.query(models.RecoveryRecommendation)
            .filter(models.RecoveryRecommendation.recommendation_status == "APPROVED")
            .count()
        )

        rejected_recs = (
            db.query(models.RecoveryRecommendation)
            .filter(models.RecoveryRecommendation.recommendation_status == "REJECTED")
            .count()
        )

        # Total estimated cost savings sum
        total_savings = (
            db.query(func.sum(models.RecoveryImpactSnapshot.estimated_cost_savings))
            .scalar() or 0.0
        )

        # Average deadline margin
        avg_margin = (
            db.query(func.avg(models.RecoveryImpactSnapshot.deadline_margin_minutes))
            .scalar() or 300.0
        )

        # Options by recovery type
        direct_count = db.query(models.RecoveryOpportunity).filter(models.RecoveryOpportunity.number_of_transfers == 0, models.RecoveryOpportunity.feasible == True).count()
        transfer_count = db.query(models.RecoveryOpportunity).filter(models.RecoveryOpportunity.number_of_transfers > 0, models.RecoveryOpportunity.feasible == True).count()

        total_decisions = approved_recs + rejected_recs
        approval_rate_pct = round((approved_recs / total_decisions * 100.0), 1) if total_decisions > 0 else 100.0

        # High priority unresolved shipments
        high_priority_unresolved = (
            db.query(models.Shipment)
            .filter(
                models.Shipment.current_status == "MISPLACED",
                models.Shipment.shipment_priority.in_(["HIGH", "CRITICAL"])
            )
            .all()
        )

        # Manager briefing
        urgent_shipment = high_priority_unresolved[0] if high_priority_unresolved else db.query(models.Shipment).filter(models.Shipment.current_status == "MISPLACED").first()
        
        best_opportunity_str = "No active recommendation"
        if urgent_shipment:
            latest_rec = SelectionRepository.get_latest_recommendation(db, urgent_shipment.shipment_id)
            if latest_rec and latest_rec.selected_opportunity:
                opp = latest_rec.selected_opportunity
                best_opportunity_str = f"Option {opp.opportunity_id} (Vehicle {opp.vehicle.vehicle_code if opp.vehicle else opp.vehicle_id})"

        manager_briefing = {
            "most_urgent_shipment": urgent_shipment.tracking_number if urgent_shipment else "None",
            "urgent_shipment_priority": urgent_shipment.shipment_priority if urgent_shipment else "NORMAL",
            "best_current_opportunity": best_opportunity_str,
            "total_estimated_cost_savings": float(total_savings),
            "recommended_manager_action": "Review and approve pending piggyback recovery recommendation for urgent misplaced shipments.",
        }

        return {
            "total_misplaced_shipments": total_misplaced,
            "shipments_with_feasible_options": shipments_with_feasible,
            "pending_reviews_count": pending_reviews,
            "approved_recommendations_count": approved_recs,
            "rejected_recommendations_count": rejected_recs,
            "total_estimated_cost_savings": round(float(total_savings), 2),
            "average_deadline_margin_minutes": round(float(avg_margin), 1),
            "average_deadline_margin_hours": round(float(avg_margin) / 60.0, 1),
            "approval_rate_percent": approval_rate_pct,
            "recovery_options_by_type": [
                {"name": "Direct Piggyback", "value": direct_count},
                {"name": "Hub Transfer Piggyback", "value": transfer_count},
            ],
            "cost_comparison": [
                {"category": "Baseline Dedicated Cost", "cost": 1500.0},
                {"category": "Selected Piggyback Cost", "cost": round(1500.0 - (float(total_savings) / (total_misplaced or 1)), 2)},
            ],
            "high_priority_unresolved_count": len(high_priority_unresolved),
            "manager_briefing": manager_briefing,
            "is_synthetic_estimate": True,
        }
