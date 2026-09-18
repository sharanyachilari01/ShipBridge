#!/usr/bin/env python3
"""
ShipBridge - Misplaced Shipment Detection Demo Script (Stage 1)
Evaluates all 10 controlled India logistics scenarios against the false-positive-resistant engine.
"""

import sys
import os
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.seed import seed_database
from app.detection.service import evaluate_all_demo_shipments

EXPECTED_STATUSES = {
    "SH001": "NORMAL",
    "SH002": "DELAYED",
    "SH003": "NORMAL_REROUTED",
    "SH004": "NORMAL",
    "SH005": "NORMAL",
    "SH006": "UNKNOWN_SIGNAL_MONITOR",
    "SH007": "NORMAL",
    "SH008": "SUSPICIOUS",
    "SH009": "MISPLACED",
    "SH010": "NORMAL_REROUTED",
}


def run_demo():
    print("=" * 110)
    print(" SHIPBRIDGE STAGE 1: EXPLAINABLE MISPLACED SHIPMENT DETECTION DEMO")
    print("=" * 110)
    print(f" Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(" Engine: MisplacementDecisionEngine (7 False-Positive Safeguards Enabled)")
    print(" Database: MySQL (shipbridge)")
    print("=" * 110)
    print()

    db = SessionLocal()
    try:
        # Reseed synthetic controlled data to ensure baseline state
        seed_database(db, reseed_synthetic_only=False)

        results = evaluate_all_demo_shipments(db)

        header = f"| {'ID':<6} | {'Expected Status':<22} | {'Evaluated Status':<22} | {'Score':<6} | {'Dist (km)':<9} | {'Match':<6} |"
        divider = "-" * len(header)
        print(divider)
        print(header)
        print(divider)

        all_passed = True
        for r in results:
            shp_id = r["shipment_id"]
            exp = EXPECTED_STATUSES.get(shp_id, "UNKNOWN")
            act = r["current_status"]
            score = r["misplacement_score"]
            dist = r["distance_to_nearest_valid_route_km"]
            matched = "PASS" if exp == act else "FAIL"
            if exp != act:
                all_passed = False

            print(f"| {shp_id:<6} | {exp:<22} | {act:<22} | {score:<6.2f} | {dist:<9.1f} | {matched:<6} |")

        print(divider)
        print()

        print("DETAILED EXPLANATIONS & EVIDENCE BREAKDOWN:")
        print("-" * 110)
        for r in results:
            shp_id = r["shipment_id"]
            print(f"[{shp_id}] Status: {r['current_status']} | Score: {r['misplacement_score']:.2f}")
            print(f"     Vehicle: {r['assigned_vehicle']} | Corridor Dev: {r['distance_to_nearest_valid_route_km']:.1f}km")
            print(f"     Cause: {r['primary_cause']}")
            print(f"     Explanation: {r['explanation']}")
            print(f"     Safeguards: {r['safeguard_outcomes']}")
            print("-" * 110)

        print()
        if all_passed:
            print(">>> SUCCESS: ALL 10 CONTROLLED DEMO SCENARIOS EVALUATED EXACTLY AS EXPECTED! <<<")
        else:
            print(">>> FAILURE: DISCREPANCY DETECTED IN DEMO SCENARIOS! <<<")

    finally:
        db.close()


if __name__ == "__main__":
    run_demo()
