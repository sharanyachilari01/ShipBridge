"""
Recommendation Service for Stage 3 Recovery Selection.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.recovery_selection.config import Stage3Config, DEFAULT_STAGE3_CONFIG
from app.recovery_selection.models import (
    RecommendationResultDomain,
    EvaluatedOptionDomain,
)
from app.recovery_selection.repositories import SelectionRepository
from app.recovery_selection.selection_engine import SelectionEngine


class RecommendationService:
    def __init__(self, config: Stage3Config = DEFAULT_STAGE3_CONFIG):
        self.config = config
        self.engine = SelectionEngine(config)

    def generate_recommendation(
        self, db: Session, shipment_id: int
    ) -> RecommendationResultDomain:
        """
        Reads Stage 2 feasible recovery opportunities, runs Stage 3 selection engine,
        persists the recommendation and impact snapshot, and returns ranked results.
        """
        shipment, raw_options = SelectionRepository.get_feasible_stage2_opportunities(db, shipment_id)
        
        now = datetime.utcnow()
        rec_id = f"REC-SH{shipment_id}-{now.strftime('%Y%m%d%H%M%S%f')}"

        if not shipment:
            return RecommendationResultDomain(
                recommendation_id=rec_id,
                analysis_id=None,
                shipment_id=shipment_id,
                tracking_number="",
                shipment_priority="NORMAL",
                shipment_status="NOT_FOUND",
                recommendation_status="NO_FEASIBLE_RECOVERY_OPTIONS",
                recommendation_score=0.0,
                recommendation_reason="Shipment not found",
                recommended_option=None,
                alternative_options=[],
                created_at=now,
                decisions=[],
            )

        if not raw_options:
            return RecommendationResultDomain(
                recommendation_id=rec_id,
                analysis_id=None,
                shipment_id=shipment_id,
                tracking_number=shipment.tracking_number,
                shipment_priority=shipment.shipment_priority,
                shipment_status=shipment.current_status,
                recommendation_status="NO_FEASIBLE_RECOVERY_OPTIONS",
                recommendation_score=0.0,
                recommendation_reason="No feasible Stage 2 recovery options meet deadline and capacity constraints",
                recommended_option=None,
                alternative_options=[],
                created_at=now,
                decisions=[],
            )

        # Run Stage 3 Selection Engine
        ranked_options = self.engine.evaluate_and_rank_options(
            shipment_weight_kg=float(shipment.shipment_weight_kg),
            shipment_volume_m3=float(shipment.shipment_volume_m3 or 1.0),
            shipment_priority=shipment.shipment_priority,
            raw_options=raw_options,
        )

        if not ranked_options:
            return RecommendationResultDomain(
                recommendation_id=rec_id,
                analysis_id=None,
                shipment_id=shipment_id,
                tracking_number=shipment.tracking_number,
                shipment_priority=shipment.shipment_priority,
                shipment_status=shipment.current_status,
                recommendation_status="NO_FEASIBLE_RECOVERY_OPTIONS",
                recommendation_score=0.0,
                recommendation_reason="No feasible options pass deadline and capacity feasibility filters",
                recommended_option=None,
                alternative_options=[],
                created_at=now,
                decisions=[],
            )

        top_recommended = ranked_options[0]
        alternatives = ranked_options[1:]

        # Save to database
        db_rec = SelectionRepository.save_recommendation_and_snapshot(
            db=db,
            recommendation_id=rec_id,
            shipment_id=shipment_id,
            analysis_id=None,
            recommended_option=top_recommended,
            reason=top_recommended.explanation,
        )

        return RecommendationResultDomain(
            recommendation_id=rec_id,
            analysis_id=db_rec.analysis_id,
            shipment_id=shipment_id,
            tracking_number=shipment.tracking_number,
            shipment_priority=shipment.shipment_priority,
            shipment_status=shipment.current_status,
            recommendation_status=db_rec.recommendation_status,
            recommendation_score=top_recommended.selection_score,
            recommendation_reason=top_recommended.explanation,
            recommended_option=top_recommended,
            alternative_options=alternatives,
            created_at=db_rec.created_at,
            decisions=[],
        )

    def get_latest_recommendation_for_shipment(
        self, db: Session, shipment_id: int
    ) -> RecommendationResultDomain:
        """
        Gets latest recommendation for shipment, generating one if not yet present.
        """
        db_rec = SelectionRepository.get_latest_recommendation(db, shipment_id)
        if not db_rec:
            return self.generate_recommendation(db, shipment_id)

        # Generate fresh analysis evaluation matching existing recommendation
        result = self.generate_recommendation(db, shipment_id)
        
        # Load decision history
        decisions_list = []
        for dec in db_rec.decisions:
            decisions_list.append({
                "decision_id": dec.id,
                "decision": dec.decision,
                "dispatcher_name": dec.dispatcher_name,
                "decision_note": dec.decision_note,
                "decided_at": dec.decided_at.isoformat() if dec.decided_at else "",
            })

        result.recommendation_id = db_rec.recommendation_id
        result.recommendation_status = db_rec.recommendation_status
        result.decisions = decisions_list
        return result
