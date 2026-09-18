"""
Demonstration script for Stage 2 Piggybacking & Recovery Opportunity Engine.
Executes recovery analysis on misplaced shipments in MySQL database and prints structured outputs.
"""

import sys
import os
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine
from app import models, seed
from app.piggybacking_engine import PiggybackingEngine


def main():
    print("=========================================================================")
    print(" SHIPBRIDGE STAGE 2: PIGGYBACKING & RECOVERY OPPORTUNITY ENGINE DEMO")
    print("=========================================================================")
    
    db = SessionLocal()
    try:
        # Ensure database is seeded
        if db.query(models.Hub).count() == 0:
            print("Database empty. Seeding synthetic data...")
            seed.seed_database(db, reseed_synthetic_only=False)
            
        # Ensure we have at least one misplaced shipment for testing
        misplaced_shipments = (
            db.query(models.Shipment)
            .filter(models.Shipment.current_status == "MISPLACED")
            .all()
        )
        
        if not misplaced_shipments:
            print("No misplaced shipments found. Flagging SH001 (shipment_id=1) as MISPLACED...")
            shp = db.query(models.Shipment).first()
            if shp:
                shp.current_status = "MISPLACED"
                db.commit()
                misplaced_shipments = [shp]

        engine_inst = PiggybackingEngine()

        for shipment in misplaced_shipments:
            print(f"\n-------------------------------------------------------------------------")
            print(f" ANALYZING MISPLACED SHIPMENT ID: {shipment.shipment_id} ({shipment.tracking_number})")
            print(f" Priority: {shipment.shipment_priority} | Weight: {shipment.shipment_weight_kg} kg | Status: {shipment.current_status}")
            print(f" Origin Hub ID: {shipment.origin_id} | Destination Hub ID: {shipment.destination_id}")
            print(f" Delivery Deadline: {shipment.delivery_deadline}")
            print(f"-------------------------------------------------------------------------")

            result = engine_inst.analyze_shipment(db, shipment.shipment_id)

            print(f"Analysis Run ID: {result.run_id}")
            print(f"Eligible: {result.eligible} | Ineligibility Reason: {result.ineligibility_reason}")
            print(f"Total Candidates Evaluated: {result.total_candidates_evaluated}")
            print(f"Feasible Opportunities Found: {result.feasible_candidates_count}")

            if result.opportunities:
                print(f"\n>>> RANKED RECOVERY OPPORTUNITIES FOR SHIPMENT {shipment.shipment_id}:")
                for opp in result.opportunities:
                    print(f"\n  [RANK #{opp.rank}] Candidate ID: {opp.candidate_id}")
                    print(f"  - Recovery Type: {'Direct Piggyback' if opp.is_direct_piggyback else 'Multi-Hop Transfer Piggyback'}")
                    print(f"  - Vehicle: {opp.vehicle_code} (ID: {opp.vehicle_id}) | Route: {opp.route_code} (ID: {opp.route_id})")
                    print(f"  - Pickup Hub: {opp.pickup_hub_name} (ID: {opp.pickup_hub_id}) -> Drop Hub: {opp.drop_hub_name} (ID: {opp.drop_hub_id})")
                    print(f"  - Transfers: {opp.number_of_transfers} ({opp.transfer_complexity})")
                    print(f"  - Capacity: Weight Rem {opp.remaining_weight_capacity_kg:.1f}/{opp.available_weight_capacity_kg:.1f} kg, Volume Rem {opp.remaining_volume_capacity_m3:.1f}/{opp.available_volume_capacity_m3:.1f} m3")
                    print(f"  - Metrics: Detour {opp.detour_distance_km:.1f} km | Extra Time {opp.additional_time_hours:.1f} hrs | Overlap {opp.route_overlap_km:.1f} km")
                    print(f"  - Schedule: Est Pickup {opp.estimated_pickup_time.strftime('%Y-%m-%d %H:%M:%S')} | Est Delivery {opp.estimated_delivery_time.strftime('%Y-%m-%d %H:%M:%S')} | Margin {opp.deadline_margin_hours:.1f} hrs ({opp.deadline_risk_level})")
                    print(f"  - Costs: Transport ${opp.transport_cost:.2f} + Transfer ${opp.transfer_cost:.2f} = Total ${opp.estimated_total_cost:.2f} (Savings vs Dedicated: ${opp.cost_savings_vs_dedicated:.2f})")
                    print(f"  - Component Scores: Dist={opp.component_scores.distance_score}, Time={opp.component_scores.time_score}, Cost={opp.component_scores.cost_score}, Deadline={opp.component_scores.deadline_score}, Cap={opp.component_scores.capacity_score}, Route={opp.component_scores.route_score}, Trans={opp.component_scores.transfer_score}")
                    print(f"  - FINAL PIGGYBACK SCORE: {opp.piggyback_score:.4f}")
                    print(f"  - Explanation: {opp.explanation}")
                    if opp.concerns:
                        print(f"  - Concerns: {', '.join(opp.concerns)}")
            else:
                print("\n  [NO FEASIBLE RECOVERY OPPORTUNITIES FOUND]")

            if result.rejected_candidates:
                print(f"\n>>> SAMPLE REJECTED CANDIDATES & REJECTION REASONS:")
                for rej in result.rejected_candidates[:5]:
                    print(f"  - Candidate: {rej.get('candidate_id', rej.get('vehicle_code'))} | Reasons: {rej.get('rejection_reasons', rej.get('rejection_reason'))}")

        print("\n=========================================================================")
        print(" DEMO COMPLETED SUCCESSFULLY.")
        print("=========================================================================")

    finally:
        db.close()


if __name__ == "__main__":
    main()
