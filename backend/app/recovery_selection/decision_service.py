"""
Decision Service for Stage 3 Dispatcher Approvals and Rejections.
"""

from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app import models
from app.recovery_selection.repositories import SelectionRepository


class DecisionService:
    @staticmethod
    def approve_recommendation(
        db: Session,
        recommendation_id: str,
        dispatcher_name: str,
        decision_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approves a recovery recommendation.
        Sets recommendation status to APPROVED and shipment status to RECOVERY_APPROVED.
        Does NOT alter vehicle assignment, capacity, or physical dispatch.
        """
        if not dispatcher_name or not dispatcher_name.strip():
            raise ValueError("Dispatcher name is required for approval")

        rec, dec = SelectionRepository.record_decision(
            db=db,
            recommendation_id=recommendation_id,
            decision_str="APPROVED",
            dispatcher_name=dispatcher_name.strip(),
            decision_note=decision_note,
        )

        return {
            "status": "APPROVED",
            "recommendation_id": rec.recommendation_id,
            "shipment_id": rec.shipment_id,
            "shipment_status": "RECOVERY_APPROVED",
            "dispatcher_name": dec.dispatcher_name,
            "decision_note": dec.decision_note,
            "decided_at": dec.decided_at.isoformat(),
            "message": f"Recommendation {recommendation_id} approved by {dispatcher_name}. Shipment status updated to RECOVERY_APPROVED.",
        }

    @staticmethod
    def reject_recommendation(
        db: Session,
        recommendation_id: str,
        dispatcher_name: str,
        decision_note: str,
    ) -> Dict[str, Any]:
        """
        Rejects a recovery recommendation.
        Sets recommendation status to REJECTED.
        Keeps shipment status as MISPLACED for future re-evaluation.
        """
        if not dispatcher_name or not dispatcher_name.strip():
            raise ValueError("Dispatcher name is required for rejection")
        if not decision_note or not decision_note.strip():
            raise ValueError("Rejection note is required")

        rec, dec = SelectionRepository.record_decision(
            db=db,
            recommendation_id=recommendation_id,
            decision_str="REJECTED",
            dispatcher_name=dispatcher_name.strip(),
            decision_note=decision_note.strip(),
        )

        return {
            "status": "REJECTED",
            "recommendation_id": rec.recommendation_id,
            "shipment_id": rec.shipment_id,
            "shipment_status": "MISPLACED",
            "dispatcher_name": dec.dispatcher_name,
            "decision_note": dec.decision_note,
            "decided_at": dec.decided_at.isoformat(),
            "message": f"Recommendation {recommendation_id} rejected by {dispatcher_name}. Shipment remains eligible for future recovery analysis.",
        }
