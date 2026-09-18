"""
Demonstration script for Stage 3: Feasible Option Selection + Impact Analysis.
"""

import sys
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app import models, seed
from app.database import SessionLocal
from app.piggybacking_engine.engine import PiggybackingEngine
from app.recovery_selection import (
    RecommendationService,
    DecisionService,
    SelectionRepository,
)


def run_stage3_demo():
    print("=" * 80)
    print(" SHIPBRIDGE STAGE 3: FEASIBLE OPTION SELECTION + IMPACT ANALYSIS DEMO ")
    print("=" * 80)

    db: Session = SessionLocal()
    try:
        # Step 1: Ensure database seeded with 10 controlled scenarios
        print("\n1. Seeding controlled MySQL database scenarios...")
        seed.seed_database(db, reseed_synthetic_only=False)
        print("   Database seeded successfully.")

        # Step 2: Retrieve misplaced shipments
        misplaced_shipments = (
            db.query(models.Shipment)
            .filter(models.Shipment.current_status == "MISPLACED")
            .all()
        )
        print(f"\n2. Found {len(misplaced_shipments)} misplaced shipments in MySQL database.")

        target_shipment = misplaced_shipments[0] if misplaced_shipments else None
        if not target_shipment:
            print("   No misplaced shipment found. Flagging SH009 (Shipment 9) as MISPLACED.")
            target_shipment = db.query(models.Shipment).filter(models.Shipment.shipment_id == 9).first()
            if target_shipment:
                target_shipment.current_status = "MISPLACED"
                db.commit()

        print(f"\n3. Evaluating Shipment: {target_shipment.tracking_number} (ID: {target_shipment.shipment_id})")
        print(f"   Priority: {target_shipment.shipment_priority}")
        print(f"   Weight: {target_shipment.shipment_weight_kg} kg | Delivery Deadline: {target_shipment.delivery_deadline}")

        # Step 3: Run Stage 2 Piggybacking Engine to populate feasible opportunities
        print("\n4. Running Stage 2 Recovery Opportunity Finder...")
        piggyback_engine = PiggybackingEngine()
        stage2_result = piggyback_engine.analyze_shipment(db, target_shipment.shipment_id)
        print(f"   Stage 2 Completed: {len(stage2_result.opportunities)} candidate opportunities evaluated.")
        print(f"   Feasible opportunities found: {sum(1 for o in stage2_result.opportunities if o.is_feasible)}")

        # Step 4: Run Stage 3 Selection & Recommendation Service
        print("\n5. Running Stage 3 Selection Engine & Impact Calculator...")
        rec_service = RecommendationService()
        rec_result = rec_service.generate_recommendation(db, target_shipment.shipment_id)

        print("\n" + "-" * 80)
        print(f" RECOMMENDATION RESULT (Status: {rec_result.recommendation_status}) ")
        print("-" * 80)
        print(f" Recommendation ID: {rec_result.recommendation_id}")
        print(f" Recommendation Score: {rec_result.recommendation_score:.4f}")
        print(f" Recommendation Rationale: {rec_result.recommendation_reason}")

        if rec_result.recommended_option:
            opt = rec_result.recommended_option
            metrics = opt.impact_metrics
            comp = opt.component_scores

            print("\n [BEST CURRENT OPTION (RECOMMENDED)]")
            print(f"   Opportunity ID: {opt.opportunity_id}")
            print(f"   Vehicle: {opt.vehicle_code} | Route: {opt.route_code}")
            print(f"   Pickup Hub: {opt.pickup_hub_name} -> Drop Hub: {opt.drop_hub_name}")
            print(f"   Transfers: {opt.number_of_transfers} ({'Direct Piggyback' if opt.is_direct_piggyback else 'Hub Transfer'})")
            print(f"   Stage 3 Selection Score: {opt.selection_score:.4f}")
            print("\n   --- Component Score Breakdown (0.0 to 1.0) ---")
            print(f"     * Piggyback Fit Score (25%):     {comp.piggyback_score_norm:.4f}")
            print(f"     * Cost Savings Score (20%):       {comp.cost_savings_score:.4f}")
            print(f"     * Deadline Buffer Score (20%):    {comp.deadline_buffer_score:.4f}")
            print(f"     * Capacity Impact Score (15%):    {comp.capacity_impact_score:.4f}")
            print(f"     * Transfer Simplicity (10%):      {comp.transfer_simplicity_score:.4f}")
            print(f"     * Delivery Speed Score (10%):     {comp.delivery_time_score:.4f}")

            if metrics:
                print("\n   --- Quantified Impact Metrics ---")
                print(f"     * Baseline Recovery Cost:         ₹{metrics.baseline_recovery_cost:.2f} (Dedicated Vehicle)")
                print(f"     * Selected Piggyback Cost:        ₹{metrics.selected_recovery_cost:.2f}")
                print(f"     * Estimated Cost Savings:         ₹{metrics.estimated_cost_savings:.2f}")
                print(f"     * Deadline Margin:                {metrics.deadline_margin_minutes} minutes ({metrics.deadline_risk} risk)")
                print(f"     * Capacity Utilization After:     {metrics.capacity_utilization_after_percent}%")

            print("\n   --- Deterministic Explanation ---")
            print(f"   {opt.explanation}")

            if opt.concerns:
                print("\n   --- Operational Concerns / Risks ---")
                for c in opt.concerns:
                    print(f"     ! {c}")

        if rec_result.alternative_options:
            print(f"\n [RANKED ALTERNATIVES ({len(rec_result.alternative_options)} options)]")
            for alt in rec_result.alternative_options:
                print(f"   Rank #{alt.rank}: Vehicle {alt.vehicle_code} | Route {alt.route_code} | Score: {alt.selection_score:.4f} | Cost: ₹{alt.estimated_total_cost:.2f} | Transfers: {alt.number_of_transfers}")

        # Step 5: Simulate Dispatcher Approval
        if rec_result.recommendation_status == "PENDING_REVIEW":
            print("\n" + "-" * 80)
            print(" SIMULATING DISPATCHER REVIEW & APPROVAL ")
            print("-" * 80)
            dispatcher_name = "Chief Dispatcher Sharanya"
            note = "Approved recommended piggyback route to maximize cost savings and meet SLA."

            dec_resp = DecisionService.approve_recommendation(
                db=db,
                recommendation_id=rec_result.recommendation_id,
                dispatcher_name=dispatcher_name,
                decision_note=note,
            )

            print(f" Decision Status: {dec_resp['status']}")
            print(f" Shipment Status: {dec_resp['shipment_status']}")
            print(f" Dispatcher: {dec_resp['dispatcher_name']}")
            print(f" Note: {dec_resp['decision_note']}")
            print(f" Message: {dec_resp['message']}")

        # Step 6: Display Impact Dashboard & Manager Briefing
        print("\n" + "-" * 80)
        print(" RECOVERY IMPACT DASHBOARD & MANAGER BRIEFING ")
        print("-" * 80)
        dash = SelectionRepository.get_dashboard_metrics(db)
        print(f" Total Misplaced Shipments:          {dash['total_misplaced_shipments']}")
        print(f" Shipments with Feasible Options:    {dash['shipments_with_feasible_options']}")
        print(f" Pending Reviews Count:              {dash['pending_reviews_count']}")
        print(f" Approved Recommendations Count:     {dash['approved_recommendations_count']}")
        print(f" Total Estimated Cost Savings:       ₹{dash['total_estimated_cost_savings']:.2f}")
        print(f" Average Deadline Margin:            {dash['average_deadline_margin_hours']} hours")
        print(f" Approval Rate:                      {dash['approval_rate_percent']}%")

        briefing = dash["manager_briefing"]
        print("\n --- Manager Briefing Panel ---")
        print(f"   * Most Urgent Shipment:          {briefing['most_urgent_shipment']} (Priority: {briefing['urgent_shipment_priority']})")
        print(f"   * Best Current Opportunity:       {briefing['best_current_opportunity']}")
        print(f"   * Total Estimated Cost Savings:   ₹{briefing['total_estimated_cost_savings']:.2f}")
        print(f"   * Recommended Manager Action:     {briefing['recommended_manager_action']}")

        print("\n" + "=" * 80)
        print(" STAGE 3 DEMO COMPLETED SUCCESSFULLY ")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_stage3_demo()
