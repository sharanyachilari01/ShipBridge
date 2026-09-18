"""
Main Engine orchestrator for Stage 2 Piggybacking & Recovery Opportunity Engine.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app import models
from app.piggybacking_engine.config import PiggybackConfig, DEFAULT_PIGGYBACK_CONFIG
from app.piggybacking_engine.models import (
    AnalysisResultDomain,
    PiggybackOptionDomain,
    ComponentScores,
    LegDetail,
    Location,
)
from app.piggybacking_engine.data_adapter import DataAdapter
from app.piggybacking_engine.candidate_finder import CandidateFinder
from app.piggybacking_engine.route_compatibility import RouteCompatibilityMatcher
from app.piggybacking_engine.distance_calculator import (
    haversine_km,
    calculate_detour_distance_km,
    calculate_route_overlap_km,
)
from app.piggybacking_engine.schedule_calculator import ScheduleCalculator
from app.piggybacking_engine.cost_calculator import CostCalculator
from app.piggybacking_engine.feasibility import FeasibilityChecker
from app.piggybacking_engine.scoring import OptionScorer
from app.piggybacking_engine.explanations import generate_explanation_and_concerns


class PiggybackingEngine:
    def __init__(self, config: PiggybackConfig = DEFAULT_PIGGYBACK_CONFIG):
        self.config = config
        self.candidate_finder = CandidateFinder(config)
        self.route_matcher = RouteCompatibilityMatcher()
        self.schedule_calculator = ScheduleCalculator(config)
        self.cost_calculator = CostCalculator(config)
        self.feasibility_checker = FeasibilityChecker(config)
        self.scorer = OptionScorer(config)

    def analyze_shipment(
        self, db: Session, shipment_id: int, analysis_id: Optional[str] = None
    ) -> AnalysisResultDomain:
        """
        Main entry point to perform complete Stage 2 recovery analysis for a misplaced shipment.
        """
        now = datetime.utcnow()
        if not analysis_id:
            analysis_id = f"PIGGYBACK-{shipment_id}-{now.strftime('%Y%m%d%H%M%S')}"

        # 1. Fetch shipment & location
        shipment, location, error = DataAdapter.get_shipment_and_location(db, shipment_id)
        if error or not shipment or not location:
            return AnalysisResultDomain(
                run_id=analysis_id,
                shipment_id=shipment_id,
                analyzed_at=now,
                misplaced_location={"latitude": location.latitude, "longitude": location.longitude} if location else None,
                eligible=False,
                ineligibility_reason=error or "LOCATION_UNAVAILABLE",
                total_candidates_evaluated=0,
                feasible_candidates_count=0,
                opportunities=[],
                rejected_candidates=[],
            )

        # 2. Fetch network data
        hubs = DataAdapter.get_all_hubs(db)
        vehicles = DataAdapter.get_all_vehicles(db)
        routes = DataAdapter.get_all_routes(db)

        # 3. Filter candidate vehicles
        valid_vehicles, rejected_vehicle_reasons = self.candidate_finder.find_candidate_vehicles(vehicles)
        rejected_candidates = list(rejected_vehicle_reasons)

        # 4. Find pickup and drop hubs
        pickup_hubs = self.candidate_finder.find_pickup_hubs(
            location, hubs, origin_hub_id=shipment.origin_id
        )
        drop_hubs = self.candidate_finder.find_drop_hubs(
            shipment.destination_id, hubs
        )

        shipment_weight = float(shipment.shipment_weight_kg)
        shipment_volume = float(shipment.shipment_volume_m3) if shipment.shipment_volume_m3 else 1.0

        all_options: List[PiggybackOptionDomain] = []
        candidate_count = 0

        # Map hubs for quick lookup
        hub_dict = {h.hub_id: h for h in hubs}
        route_dict = {r.route_id: r for r in routes}

        # 5. Evaluate Direct Piggybacking Candidates
        for vehicle in valid_vehicles:
            # Find routes matching vehicle
            v_routes = [r for r in routes if r.origin_hub_id == vehicle.assigned_hub_id or r.route_id == vehicle.current_route_id]
            if not v_routes:
                v_routes = routes  # Fallback to check active routes network

            for route in v_routes:
                for pickup_hub, pickup_dist in pickup_hubs:
                    for drop_hub, drop_dist in drop_hubs:
                        candidate_count += 1
                        
                        is_compat, route_rejection, geom_slice = self.route_matcher.check_direct_route_compatibility(
                            vehicle, route, pickup_hub, drop_hub
                        )
                        
                        rejection_reasons = []
                        if not is_compat and route_rejection:
                            rejection_reasons.append(route_rejection)

                        # Estimate load on vehicle
                        avail_wt = vehicle.weight_capacity_kg
                        avail_vol = vehicle.volume_capacity_m3
                        rem_wt = max(0.0, avail_wt - (avail_wt * 0.5))  # Estimate current 50% load factor
                        rem_vol = max(0.0, avail_vol - (avail_vol * 0.5))

                        # Distance calculations
                        detour_km = calculate_detour_distance_km(
                            location.latitude,
                            location.longitude,
                            pickup_hub.latitude,
                            pickup_hub.longitude,
                            drop_hub.latitude,
                            drop_hub.longitude,
                        )
                        
                        overlap_km = calculate_route_overlap_km(
                            pickup_hub.latitude,
                            pickup_hub.longitude,
                            drop_hub.latitude,
                            drop_hub.longitude,
                            geom_slice or route.route_geometry,
                        )

                        # Timing calculations
                        est_pickup, est_delivery, extra_hrs, margin_hrs, risk_level, time_rejection = (
                            self.schedule_calculator.calculate_schedule(
                                now,
                                detour_km,
                                overlap_km,
                                shipment.pickup_deadline,
                                shipment.delivery_deadline,
                                num_transfers=0,
                            )
                        )
                        if time_rejection:
                            rejection_reasons.append(time_rejection)

                        # Cost calculations
                        direct_dist = haversine_km(
                            location.latitude,
                            location.longitude,
                            drop_hub.latitude,
                            drop_hub.longitude,
                        )
                        transport_cost, transfer_cost, total_cost, savings = (
                            self.cost_calculator.calculate_cost(
                                detour_km, extra_hrs, num_transfers=0, direct_shipment_distance_km=direct_dist
                            )
                        )

                        # Feasibility evaluation
                        is_feasible, final_rejections = self.feasibility_checker.check_feasibility(
                            vehicle=vehicle,
                            shipment_weight_kg=shipment_weight,
                            shipment_volume_m3=shipment_volume,
                            remaining_weight_capacity_kg=rem_wt,
                            remaining_volume_capacity_m3=rem_vol,
                            detour_distance_km=detour_km,
                            additional_time_hours=extra_hrs,
                            estimated_total_cost=total_cost,
                            deadline_margin_hours=margin_hrs,
                            num_transfers=0,
                            initial_rejection_reasons=rejection_reasons,
                        )

                        # Scoring
                        scores = self.scorer.calculate_scores(
                            detour_distance_km=detour_km,
                            additional_time_hours=extra_hrs,
                            estimated_total_cost=total_cost,
                            available_weight_kg=avail_wt,
                            remaining_weight_kg=rem_wt,
                            available_volume_m3=avail_vol,
                            remaining_volume_m3=rem_vol,
                            deadline_margin_hours=margin_hrs,
                            route_overlap_km=overlap_km,
                            num_transfers=0,
                        )

                        cand_id = f"OPT-DIRECT-V{vehicle.vehicle_id}-R{route.route_id}-P{pickup_hub.hub_id}-D{drop_hub.hub_id}"
                        
                        leg = LegDetail(
                            leg_index=1,
                            vehicle_id=vehicle.vehicle_id,
                            vehicle_code=vehicle.vehicle_code,
                            route_id=route.route_id,
                            route_code=route.route_code,
                            from_hub_id=pickup_hub.hub_id,
                            from_hub_name=pickup_hub.name,
                            to_hub_id=drop_hub.hub_id,
                            to_hub_name=drop_hub.name,
                            departure_time=est_pickup,
                            arrival_time=est_delivery,
                            distance_km=overlap_km,
                        )

                        option = PiggybackOptionDomain(
                            candidate_id=cand_id,
                            shipment_id=shipment_id,
                            vehicle_id=vehicle.vehicle_id,
                            vehicle_code=vehicle.vehicle_code,
                            route_id=route.route_id,
                            route_code=route.route_code,
                            pickup_hub_id=pickup_hub.hub_id,
                            pickup_hub_name=pickup_hub.name,
                            drop_hub_id=drop_hub.hub_id,
                            drop_hub_name=drop_hub.name,
                            number_of_transfers=0,
                            is_direct_piggyback=True,
                            available_weight_capacity_kg=avail_wt,
                            remaining_weight_capacity_kg=rem_wt,
                            available_volume_capacity_m3=avail_vol,
                            remaining_volume_capacity_m3=rem_vol,
                            route_overlap_km=overlap_km,
                            detour_distance_km=detour_km,
                            additional_time_hours=extra_hrs,
                            estimated_pickup_time=est_pickup,
                            estimated_delivery_time=est_delivery,
                            transport_cost=transport_cost,
                            transfer_cost=transfer_cost,
                            estimated_total_cost=total_cost,
                            cost_savings_vs_dedicated=savings,
                            deadline_margin_hours=margin_hrs,
                            deadline_risk_level=risk_level,
                            transfer_complexity="DIRECT",
                            is_feasible=is_feasible,
                            rejection_reasons=final_rejections,
                            component_scores=scores,
                            piggyback_score=scores.total_score if is_feasible else 0.0,
                            legs=[leg],
                            route_geometry=geom_slice or route.route_geometry,
                        )

                        explanation, concerns = generate_explanation_and_concerns(option)
                        option.explanation = explanation
                        option.concerns = concerns

                        all_options.append(option)

        # 6. Evaluate 2-Hop Hub-Transfer Candidates (if fewer than 3 feasible direct options)
        feasible_direct = [o for o in all_options if o.is_feasible]
        if len(feasible_direct) < 3 and len(valid_vehicles) >= 2:
            for i, v1 in enumerate(valid_vehicles):
                for j, v2 in enumerate(valid_vehicles):
                    if i == j:
                        continue
                    v1_routes = [r for r in routes if r.origin_hub_id == v1.assigned_hub_id or r.route_id == v1.current_route_id] or routes
                    v2_routes = [r for r in routes if r.origin_hub_id == v2.assigned_hub_id or r.route_id == v2.current_route_id] or routes

                    for r1 in v1_routes:
                        for r2 in v2_routes:
                            for pickup_hub, _ in pickup_hubs:
                                for drop_hub, _ in drop_hubs:
                                    is_compat, transfer_hub, rej_reason = (
                                        self.route_matcher.find_two_hop_route_compatibility(
                                            v1, r1, v2, r2, pickup_hub, drop_hub, hubs
                                        )
                                    )
                                    if is_compat and transfer_hub:
                                        candidate_count += 1
                                        avail_wt = min(v1.weight_capacity_kg, v2.weight_capacity_kg)
                                        avail_vol = min(v1.volume_capacity_m3, v2.volume_capacity_m3)
                                        rem_wt = max(0.0, avail_wt * 0.4)
                                        rem_vol = max(0.0, avail_vol * 0.4)

                                        detour_km = calculate_detour_distance_km(
                                            location.latitude,
                                            location.longitude,
                                            pickup_hub.latitude,
                                            pickup_hub.longitude,
                                            drop_hub.latitude,
                                            drop_hub.longitude,
                                        ) + 10.0  # extra transfer detour

                                        overlap_km = round(
                                            haversine_km(pickup_hub.latitude, pickup_hub.longitude, transfer_hub.latitude, transfer_hub.longitude)
                                            + haversine_km(transfer_hub.latitude, transfer_hub.longitude, drop_hub.latitude, drop_hub.longitude),
                                            2,
                                        )

                                        est_pickup, est_delivery, extra_hrs, margin_hrs, risk_level, time_rejection = (
                                            self.schedule_calculator.calculate_schedule(
                                                now,
                                                detour_km,
                                                overlap_km,
                                                shipment.pickup_deadline,
                                                shipment.delivery_deadline,
                                                num_transfers=1,
                                            )
                                        )

                                        rejection_reasons = []
                                        if time_rejection:
                                            rejection_reasons.append(time_rejection)

                                        transport_cost, transfer_cost, total_cost, savings = (
                                            self.cost_calculator.calculate_cost(
                                                detour_km, extra_hrs, num_transfers=1, direct_shipment_distance_km=overlap_km
                                            )
                                        )

                                        is_feasible, final_rejections = self.feasibility_checker.check_feasibility(
                                            vehicle=v1,
                                            shipment_weight_kg=shipment_weight,
                                            shipment_volume_m3=shipment_volume,
                                            remaining_weight_capacity_kg=rem_wt,
                                            remaining_volume_capacity_m3=rem_vol,
                                            detour_distance_km=detour_km,
                                            additional_time_hours=extra_hrs,
                                            estimated_total_cost=total_cost,
                                            deadline_margin_hours=margin_hrs,
                                            num_transfers=1,
                                            initial_rejection_reasons=rejection_reasons,
                                        )

                                        scores = self.scorer.calculate_scores(
                                            detour_distance_km=detour_km,
                                            additional_time_hours=extra_hrs,
                                            estimated_total_cost=total_cost,
                                            available_weight_kg=avail_wt,
                                            remaining_weight_kg=rem_wt,
                                            available_volume_m3=avail_vol,
                                            remaining_volume_m3=rem_vol,
                                            deadline_margin_hours=margin_hrs,
                                            route_overlap_km=overlap_km,
                                            num_transfers=1,
                                        )

                                        cand_id = f"OPT-TRANSFER-V{v1.vehicle_id}-V{v2.vehicle_id}-TH{transfer_hub.hub_id}"
                                        
                                        leg1 = LegDetail(
                                            leg_index=1,
                                            vehicle_id=v1.vehicle_id,
                                            vehicle_code=v1.vehicle_code,
                                            route_id=r1.route_id,
                                            route_code=r1.route_code,
                                            from_hub_id=pickup_hub.hub_id,
                                            from_hub_name=pickup_hub.name,
                                            to_hub_id=transfer_hub.hub_id,
                                            to_hub_name=transfer_hub.name,
                                            departure_time=est_pickup,
                                            arrival_time=est_pickup + (est_delivery - est_pickup) / 2,
                                        )

                                        leg2 = LegDetail(
                                            leg_index=2,
                                            vehicle_id=v2.vehicle_id,
                                            vehicle_code=v2.vehicle_code,
                                            route_id=r2.route_id,
                                            route_code=r2.route_code,
                                            from_hub_id=transfer_hub.hub_id,
                                            from_hub_name=transfer_hub.name,
                                            to_hub_id=drop_hub.hub_id,
                                            to_hub_name=drop_hub.name,
                                            departure_time=est_pickup + (est_delivery - est_pickup) / 2,
                                            arrival_time=est_delivery,
                                        )

                                        option = PiggybackOptionDomain(
                                            candidate_id=cand_id,
                                            shipment_id=shipment_id,
                                            vehicle_id=v1.vehicle_id,
                                            vehicle_code=v1.vehicle_code,
                                            route_id=r1.route_id,
                                            route_code=r1.route_code,
                                            pickup_hub_id=pickup_hub.hub_id,
                                            pickup_hub_name=pickup_hub.name,
                                            drop_hub_id=drop_hub.hub_id,
                                            drop_hub_name=drop_hub.name,
                                            number_of_transfers=1,
                                            is_direct_piggyback=False,
                                            available_weight_capacity_kg=avail_wt,
                                            remaining_weight_capacity_kg=rem_wt,
                                            available_volume_capacity_m3=avail_vol,
                                            remaining_volume_capacity_m3=rem_vol,
                                            route_overlap_km=overlap_km,
                                            detour_distance_km=detour_km,
                                            additional_time_hours=extra_hrs,
                                            estimated_pickup_time=est_pickup,
                                            estimated_delivery_time=est_delivery,
                                            transport_cost=transport_cost,
                                            transfer_cost=transfer_cost,
                                            estimated_total_cost=total_cost,
                                            cost_savings_vs_dedicated=savings,
                                            deadline_margin_hours=margin_hrs,
                                            deadline_risk_level=risk_level,
                                            transfer_complexity="SINGLE_TRANSFER",
                                            is_feasible=is_feasible,
                                            rejection_reasons=final_rejections,
                                            component_scores=scores,
                                            piggyback_score=scores.total_score if is_feasible else 0.0,
                                            legs=[leg1, leg2],
                                            route_geometry=(r1.route_geometry or []) + (r2.route_geometry or []),
                                        )

                                        explanation, concerns = generate_explanation_and_concerns(option)
                                        option.explanation = explanation
                                        option.concerns = concerns

                                        all_options.append(option)

        # Separate feasible vs rejected options
        feasible_options = [o for o in all_options if o.is_feasible]
        rejected_options = [o for o in all_options if not o.is_feasible]

        # Deduplicate feasible options by candidate_id to avoid redundant route permutation entries
        unique_feasible: Dict[str, PiggybackOptionDomain] = {}
        for opt in feasible_options:
            key = f"{opt.vehicle_id}-{opt.route_id}-{opt.pickup_hub_id}-{opt.drop_hub_id}-{opt.number_of_transfers}"
            if key not in unique_feasible or opt.piggyback_score > unique_feasible[key].piggyback_score:
                unique_feasible[key] = opt
        
        final_feasible = list(unique_feasible.values())

        # 7. Rank feasible options deterministically
        ranked_feasible = self.scorer.rank_options(final_feasible)

        # 8. Persist to MySQL database
        summary = {
            "total_candidates_evaluated": candidate_count,
            "feasible_count": len(ranked_feasible),
            "rejected_count": len(rejected_options) + len(rejected_candidates),
        }

        DataAdapter.save_analysis_and_opportunities(
            db=db,
            analysis_id=analysis_id,
            shipment_id=shipment_id,
            status="COMPLETED" if ranked_feasible else "NO_FEASIBLE_OPTIONS",
            total_candidates=candidate_count,
            feasible_count=len(ranked_feasible),
            options=ranked_feasible + rejected_options[:10],  # persist top feasible + sample rejected
            summary=summary,
        )

        return AnalysisResultDomain(
            run_id=analysis_id,
            shipment_id=shipment_id,
            analyzed_at=now,
            misplaced_location={"latitude": location.latitude, "longitude": location.longitude} if location else None,
            eligible=True,
            ineligibility_reason=None,
            total_candidates_evaluated=candidate_count,
            feasible_candidates_count=len(ranked_feasible),
            opportunities=ranked_feasible,
            rejected_candidates=[
                {
                    "candidate_id": o.candidate_id,
                    "vehicle_code": o.vehicle_code,
                    "rejection_reasons": o.rejection_reasons,
                }
                for o in rejected_options[:10]
            ] + rejected_candidates,
        )
