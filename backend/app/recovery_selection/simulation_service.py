import dataclasses
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app import models
from app.recovery_selection.config import Stage3Config, DEFAULT_STAGE3_CONFIG
from app.recovery_selection.models import EvaluatedOptionDomain, Stage3ComponentScores, Stage3ImpactMetrics
from app.recovery_selection.recommendation_service import RecommendationService
from app.recovery_selection.repositories import SelectionRepository
from app.recovery_selection.selection_engine import SelectionEngine


def domain_option_to_dict(opt: Optional[EvaluatedOptionDomain]) -> Optional[Dict[str, Any]]:
    if not opt:
        return None
    res = dataclasses.asdict(opt)
    if isinstance(res.get("estimated_delivery_time"), datetime):
        res["estimated_delivery_time"] = res["estimated_delivery_time"].isoformat()
    if res.get("impact_metrics") and isinstance(res["impact_metrics"].get("selected_delivery_time"), datetime):
        res["impact_metrics"]["selected_delivery_time"] = res["impact_metrics"]["selected_delivery_time"].isoformat()
    if res.get("impact_metrics") and isinstance(res["impact_metrics"].get("baseline_delivery_time"), datetime):
        res["impact_metrics"]["baseline_delivery_time"] = res["impact_metrics"]["baseline_delivery_time"].isoformat()
    return res


class SimulationService:
    def __init__(self, config: Stage3Config = DEFAULT_STAGE3_CONFIG):
        self.config = config
        self.engine = SelectionEngine(config)
        self.rec_service = RecommendationService(config)

    def run_simulation(
        self,
        db: Session,
        shipment_id: int,
        additional_route_delay_hours: float = 0.0,
        additional_handling_delay_minutes: float = 0.0,
        available_capacity_adjustment_percent: float = 0.0,
        cost_multiplier: float = 1.0,
        priority_override: Optional[str] = None,
        transfer_hub_unavailable: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs non-persistent simulation on Stage 2 candidate recovery opportunities.
        Returns side-by-side baseline vs simulated comparison.
        Does NOT alter live MySQL database records.
        """
        # 1. Fetch shipment
        shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == shipment_id).first()
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found.")

        # 2. Get baseline recommendation in-memory without DB insertion
        shipment_obj, raw_options = SelectionRepository.get_feasible_stage2_opportunities(db, shipment_id)
        if raw_options:
            ranked_options = self.engine.evaluate_and_rank_options(
                shipment_weight_kg=float(shipment.shipment_weight_kg),
                shipment_volume_m3=float(shipment.shipment_volume_m3 or 1.0),
                shipment_priority=shipment.shipment_priority,
                raw_options=raw_options,
            )
            baseline_top = ranked_options[0] if ranked_options else None
            baseline_alts = ranked_options[1:] if len(ranked_options) > 1 else []
        else:
            baseline_top = None
            baseline_alts = []

        # 3. Load candidate opportunities from DB
        query_opps = (
            db.query(models.RecoveryOpportunity)
            .filter(models.RecoveryOpportunity.shipment_id == shipment_id)
            .all()
        )

        effective_priority = priority_override or shipment.shipment_priority
        shipment_weight = float(shipment.shipment_weight_kg)
        shipment_volume = float(shipment.shipment_volume_m3 or 1.0)
        delivery_deadline = shipment.delivery_deadline

        simulated_options: List[Dict[str, Any]] = []
        newly_infeasible: List[Dict[str, Any]] = []

        for opp in query_opps:
            rejection_reasons = []
            is_feasible = True

            # Hub availability check
            if transfer_hub_unavailable and transfer_hub_unavailable.strip():
                unavail = transfer_hub_unavailable.strip().upper()
                hub_codes = []
                if opp.pickup_hub:
                    hub_codes.extend([opp.pickup_hub.code.upper(), opp.pickup_hub.name.upper(), str(opp.pickup_hub.hub_id)])
                if opp.drop_hub:
                    hub_codes.extend([opp.drop_hub.code.upper(), opp.drop_hub.name.upper(), str(opp.drop_hub.hub_id)])
                if opp.transfer_hub:
                    hub_codes.extend([opp.transfer_hub.code.upper(), opp.transfer_hub.name.upper(), str(opp.transfer_hub.hub_id)])

                if any(unavail in code or code in unavail for code in hub_codes):
                    is_feasible = False
                    rejection_reasons.append(
                        f"Transfer hub {transfer_hub_unavailable} is unavailable due to simulated hub closure"
                    )

            # Baseline capacity & adjustment
            base_avail_wt = float(opp.available_weight_kg or 10000.0)
            base_avail_vol = float(opp.available_volume_m3 or 40.0)

            sim_avail_wt = base_avail_wt * (1.0 + available_capacity_adjustment_percent / 100.0)
            sim_avail_vol = base_avail_vol * (1.0 + available_capacity_adjustment_percent / 100.0)

            if shipment_weight > sim_avail_wt:
                is_feasible = False
                rejection_reasons.append(
                    f"Insufficient simulated payload capacity ({shipment_weight:.1f}kg exceeds available {sim_avail_wt:.1f}kg)"
                )
            if shipment_volume > sim_avail_vol:
                is_feasible = False
                rejection_reasons.append(
                    f"Insufficient simulated cargo volume ({shipment_volume:.1f}m³ exceeds available {sim_avail_vol:.1f}m³)"
                )

            # Baseline time & ETA adjustments
            base_eta = opp.estimated_delivery_time or (datetime.utcnow() + timedelta(hours=12))
            base_add_time_hrs = float(opp.additional_time_hours or 1.0)

            total_delay_mins = additional_route_delay_hours * 60.0 + additional_handling_delay_minutes
            sim_add_time_hrs = base_add_time_hrs + total_delay_mins / 60.0
            sim_eta = base_eta + timedelta(minutes=total_delay_mins)

            sim_margin_mins = 600
            if delivery_deadline:
                sim_margin_mins = int((delivery_deadline - sim_eta).total_seconds() / 60.0)
                if sim_margin_mins < 0:
                    is_feasible = False
                    rejection_reasons.append(
                        f"Simulated ETA ({sim_eta.strftime('%H:%M')}) exceeds delivery deadline by {abs(sim_margin_mins)} minutes"
                    )

            # Risk level
            if sim_margin_mins > 120:
                sim_risk = "SAFE"
            elif sim_margin_mins >= 1:
                sim_risk = "TIGHT"
            else:
                sim_risk = "AT_RISK"

            # Cost adjustments
            base_transport_cost = float(opp.additional_transport_cost or 2000.0)
            base_transfer_cost = float(opp.transfer_cost or 0.0)

            sim_transport_cost = base_transport_cost * max(0.1, cost_multiplier)
            sim_total_cost = sim_transport_cost + base_transfer_cost

            # Recalculate component scores
            fit_score = float(opp.piggyback_score or 0.8)
            cost_score = max(0.0, min(1.0, 1.0 - sim_total_cost / 15000.0))
            deadline_score = max(0.0, min(1.0, sim_margin_mins / 720.0))
            capacity_score = max(0.0, min(1.0, (sim_avail_wt - shipment_weight) / max(1.0, sim_avail_wt)))
            transfer_simplicity = 1.0 if (opp.number_of_transfers or 0) == 0 else (0.7 if (opp.number_of_transfers or 0) == 1 else 0.4)
            speed_score = max(0.0, min(1.0, 1.0 - sim_add_time_hrs / 12.0))

            sim_selection_score = round(
                0.25 * fit_score +
                0.20 * cost_score +
                0.20 * deadline_score +
                0.15 * capacity_score +
                0.10 * transfer_simplicity +
                0.10 * speed_score,
                4
            )

            # Build vehicle and route info
            vehicle_code = opp.vehicle.vehicle_code if opp.vehicle else "IND-TRK-101"
            route_code = opp.candidate_route.route_code if opp.candidate_route else "RTE-BLR-HYD-DEL"
            pickup_name = opp.pickup_hub.name if opp.pickup_hub else "Origin Hub"
            drop_name = opp.drop_hub.name if opp.drop_hub else "Destination Hub"

            sim_item = {
                "opportunity_id": opp.opportunity_id,
                "shipment_id": opp.shipment_id,
                "vehicle_id": opp.vehicle_id,
                "vehicle_code": vehicle_code,
                "route_id": opp.candidate_route_id,
                "route_code": route_code,
                "pickup_hub_id": opp.pickup_hub_id,
                "pickup_hub_name": pickup_name,
                "drop_hub_id": opp.drop_hub_id,
                "drop_hub_name": drop_name,
                "is_direct_piggyback": (opp.number_of_transfers or 0) == 0,
                "number_of_transfers": opp.number_of_transfers or 0,
                "estimated_total_cost": round(sim_total_cost, 2),
                "estimated_delivery_time": sim_eta.isoformat(),
                "deadline_margin_minutes": sim_margin_mins,
                "deadline_risk": sim_risk,
                "stage2_piggyback_score": fit_score,
                "component_scores": {
                    "piggyback_score_norm": round(fit_score, 4),
                    "cost_savings_score": round(cost_score, 4),
                    "deadline_buffer_score": round(deadline_score, 4),
                    "capacity_impact_score": round(capacity_score, 4),
                    "transfer_simplicity_score": round(transfer_simplicity, 4),
                    "delivery_time_score": round(speed_score, 4),
                    "selection_score": sim_selection_score,
                },
                "selection_score": sim_selection_score,
                "is_feasible": is_feasible,
                "rejection_reasons": rejection_reasons,
                "explanation": (
                    f"Simulated option on {vehicle_code} ({route_code}). "
                    f"ETA: {sim_eta.strftime('%Y-%m-%d %H:%M')}, Est Cost: ₹{sim_total_cost:.2f}, "
                    f"Deadline Margin: {sim_margin_mins}m ({sim_risk} risk)."
                ),
                "concerns": rejection_reasons if not is_feasible else (["Tight deadline margin"] if sim_risk == "TIGHT" else []),
                "route_geometry": [],
            }

            if is_feasible:
                simulated_options.append(sim_item)
            else:
                newly_infeasible.append({
                    "opportunity_id": opp.opportunity_id,
                    "vehicle_code": vehicle_code,
                    "route_code": route_code,
                    "rejection_reasons": rejection_reasons,
                })

        # Deterministic sorting of simulated feasible options
        simulated_options.sort(
            key=lambda x: (
                -x["selection_score"],
                -x["deadline_margin_minutes"],
                x["estimated_total_cost"],
                x["number_of_transfers"],
                x["vehicle_id"],
            )
        )

        # Assign ranks
        for idx, item in enumerate(simulated_options):
            item["rank"] = idx + 1
            item["designation"] = "RECOMMENDED_PLAN" if idx == 0 else f"ALTERNATIVE_RANK_{idx+1}"

        simulated_top = simulated_options[0] if simulated_options else None

        # Build rank changes
        baseline_ranks = {}
        if baseline_top:
            baseline_ranks[baseline_top.opportunity_id] = 1
        for alt in baseline_alts:
            baseline_ranks[alt.opportunity_id] = alt.rank

        rank_changes = []
        all_opp_ids = set(baseline_ranks.keys()).union({o["opportunity_id"] for o in simulated_options})
        for opp_id in all_opp_ids:
            base_r = baseline_ranks.get(opp_id)
            sim_match = next((o for o in simulated_options if o["opportunity_id"] == opp_id), None)
            sim_r = sim_match["rank"] if sim_match else None
            v_code = sim_match["vehicle_code"] if sim_match else (baseline_top.vehicle_code if baseline_top and baseline_top.opportunity_id == opp_id else "TRK")

            if base_r and sim_r:
                delta = base_r - sim_r
                status_change = "IMPROVED" if delta > 0 else ("DROPPED" if delta < 0 else "UNCHANGED")
            elif base_r and not sim_r:
                delta = -99
                status_change = "NEWLY_INFEASIBLE"
            else:
                delta = 0
                status_change = "NEWLY_FEASIBLE"

            rank_changes.append({
                "opportunity_id": opp_id,
                "vehicle_code": v_code,
                "baseline_rank": base_r,
                "simulated_rank": sim_r,
                "rank_delta": delta,
                "status_change": status_change,
            })

        # Comparison summary metrics
        base_cost = baseline_top.estimated_total_cost if baseline_top else 0.0
        sim_cost = simulated_top["estimated_total_cost"] if simulated_top else 0.0
        base_score = baseline_top.selection_score if baseline_top else 0.0
        sim_score = simulated_top["selection_score"] if simulated_top else 0.0
        base_margin = baseline_top.deadline_margin_minutes if baseline_top else 0
        sim_margin = simulated_top["deadline_margin_minutes"] if simulated_top else 0

        rec_changed = False
        if baseline_top and simulated_top:
            rec_changed = (baseline_top.opportunity_id != simulated_top["opportunity_id"])
        elif (baseline_top is None) != (simulated_top is None):
            rec_changed = True

        if rec_changed:
            change_summary = f"Simulation changed recommended plan to Vehicle {simulated_top['vehicle_code']}" if simulated_top else "Simulation rendered all candidate routes infeasible."
        else:
            change_summary = f"Recommended plan remains Vehicle {simulated_top['vehicle_code']} under simulated parameters." if simulated_top else "No feasible recovery option under this scenario."

        baseline_dict = domain_option_to_dict(baseline_top)
        baseline_alts_dict = [domain_option_to_dict(a) for a in baseline_alts if a]

        return {
            "shipment_id": shipment_id,
            "tracking_number": shipment.tracking_number,
            "simulation_inputs": {
                "additional_route_delay_hours": additional_route_delay_hours,
                "additional_handling_delay_minutes": additional_handling_delay_minutes,
                "available_capacity_adjustment_percent": available_capacity_adjustment_percent,
                "cost_multiplier": cost_multiplier,
                "priority_override": effective_priority,
                "transfer_hub_unavailable": transfer_hub_unavailable,
            },
            "baseline_recommended_option": baseline_dict,
            "simulated_recommended_option": simulated_top,
            "baseline_options": ([baseline_dict] if baseline_dict else []) + [a for a in baseline_alts_dict if a],
            "simulated_options": simulated_options,
            "rank_changes": rank_changes,
            "newly_infeasible_candidates": newly_infeasible,
            "comparison": {
                "baseline_cost": base_cost,
                "simulated_cost": sim_cost,
                "cost_delta": round(sim_cost - base_cost, 2),
                "baseline_eta": baseline_top.estimated_delivery_time.isoformat() if baseline_top and isinstance(baseline_top.estimated_delivery_time, datetime) else str(baseline_top.estimated_delivery_time) if baseline_top else None,
                "simulated_eta": simulated_top["estimated_delivery_time"] if simulated_top else None,
                "eta_delay_minutes": round(additional_route_delay_hours * 60 + additional_handling_delay_minutes, 1),
                "baseline_deadline_margin_minutes": base_margin,
                "simulated_deadline_margin_minutes": sim_margin,
                "baseline_score": base_score,
                "simulated_score": sim_score,
                "score_delta": round(sim_score - base_score, 4),
                "recommendation_changed": rec_changed,
                "change_summary": change_summary,
            },
            "has_feasible_simulated_option": simulated_top is not None,
        }
