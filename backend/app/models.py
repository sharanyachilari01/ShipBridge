import json
import math
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import relationship, declarative_base
from app.database import Base


class Hub(Base):
    __tablename__ = "hub_table"

    hub_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    @property
    def id(self):
        return self.hub_id

    @property
    def hub_type(self):
        return "HUB"


class RouteNetwork(Base):
    __tablename__ = "route_network_table"

    route_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    route_code = Column(String(50), unique=True, index=True, nullable=False)
    origin_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    destination_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    route_geometry_json = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    origin_hub = relationship("Hub", foreign_keys=[origin_hub_id])
    destination_hub = relationship("Hub", foreign_keys=[destination_hub_id])

    @property
    def id(self):
        return self.route_id


class Vehicle(Base):
    __tablename__ = "vehicle_table"

    vehicle_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_code = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False)
    capacity_kg = Column(Numeric(10, 2), nullable=False)
    assigned_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True, index=True)
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, IN_TRANSIT, MAINTENANCE
    is_synthetic = Column(Boolean, default=True, nullable=False)

    assigned_hub = relationship("Hub", foreign_keys=[assigned_hub_id])

    @property
    def id(self):
        return self.vehicle_id


class VehicleRoute(Base):
    __tablename__ = "vehicle_route_table"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("route_network_table.route_id"), nullable=False, index=True)
    status = Column(String(30), default="ACTIVE", nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    vehicle = relationship("Vehicle")
    route = relationship("RouteNetwork")

    @property
    def vehicle_route_id(self):
        return self.id


class Shipment(Base):
    __tablename__ = "shipment_table"

    shipment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    origin_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    expected_next_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True, index=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=True, index=True)
    shipment_priority = Column(String(20), default="NORMAL", nullable=False)  # NORMAL, HIGH, CRITICAL
    current_status = Column(String(30), default="ON_TRACK", nullable=False, index=True)  # ON_TRACK, MISPLACED, RECOVERING, RECOVERY_APPROVED, DELIVERED, DELAYED
    shipment_weight_kg = Column(Numeric(10, 2), nullable=False)
    shipment_volume_m3 = Column(Numeric(10, 2), nullable=True, default=1.0)
    created_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    pickup_deadline = Column(DateTime, nullable=True)
    delivery_deadline = Column(DateTime, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    origin_hub = relationship("Hub", foreign_keys=[origin_id])
    destination_hub = relationship("Hub", foreign_keys=[destination_id])
    expected_next_hub = relationship("Hub", foreign_keys=[expected_next_hub_id])
    assigned_vehicle = relationship("Vehicle", foreign_keys=[assigned_vehicle_id])

    @property
    def id(self):
        return self.shipment_id

    @property
    def origin_hub_id(self):
        return self.origin_id

    @property
    def destination_hub_id(self):
        return self.destination_id

    @property
    def priority(self):
        return self.shipment_priority

    @property
    def status(self):
        return self.current_status

    @property
    def weight_kg(self):
        return float(self.shipment_weight_kg)

    @property
    def volume_m3(self):
        return float(self.shipment_volume_m3 or 1.0)

    @property
    def created_at(self):
        return self.created_timestamp

    @property
    def updated_at(self):
        return self.created_timestamp


class ShipmentTracking(Base):
    __tablename__ = "shipment_tracking_table"

    tracking_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=True, index=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    current_lat = Column(Numeric(10, 7), nullable=True)
    current_lng = Column(Numeric(10, 7), nullable=True)
    speed_kmh = Column(Numeric(5, 2), nullable=True)
    heading_degrees = Column(Float, nullable=True)
    gps_accuracy_meters = Column(Float, nullable=True)
    ble_gateway_id = Column(String(50), nullable=True)
    tracking_available = Column(Boolean, default=True, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    shipment = relationship("Shipment")
    assigned_vehicle = relationship("Vehicle")

    @property
    def id(self):
        return self.tracking_id


class ShipmentException(Base):
    __tablename__ = "shipment_exception_table"

    exception_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    exception_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="HIGH", nullable=False)
    detected_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = Column(Float, default=0.95, nullable=False)
    exception_details = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    shipment = relationship("Shipment")

    @property
    def id(self):
        return self.exception_id


class VehicleTransfer(Base):
    __tablename__ = "vehicle_transfers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    from_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=True, index=True)
    to_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=False, index=True)
    transfer_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    transferred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(30), default="COMPLETED", nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    shipment = relationship("Shipment")
    from_vehicle = relationship("Vehicle", foreign_keys=[from_vehicle_id])
    to_vehicle = relationship("Vehicle", foreign_keys=[to_vehicle_id])
    transfer_hub = relationship("Hub", foreign_keys=[transfer_hub_id])


class PiggybackAnalysisRun(Base):
    __tablename__ = "piggyback_analysis_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(String(100), unique=True, index=True, nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    candidates_found_count = Column(Integer, default=0, nullable=False)
    feasible_candidates_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    summary_json = Column(Text, nullable=True)

    shipment = relationship("Shipment")


class RecoveryOpportunity(Base):
    __tablename__ = "recovery_opportunity_table"

    opportunity_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=False, index=True)
    analysis_id = Column(String(100), index=True, nullable=True)
    candidate_route_id = Column(Integer, ForeignKey("route_network_table.route_id"), nullable=True)
    recovery_type = Column(String(50), nullable=True)
    pickup_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True)
    drop_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True)
    transfer_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True)
    second_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=True)
    second_route_id = Column(Integer, ForeignKey("route_network_table.route_id"), nullable=True)
    available_weight_kg = Column(Numeric(10, 2), nullable=True)
    remaining_weight_kg = Column(Numeric(10, 2), nullable=True)
    available_volume_m3 = Column(Numeric(10, 2), nullable=True)
    remaining_volume_m3 = Column(Numeric(10, 2), nullable=True)
    route_overlap_km = Column(Float, nullable=True)
    detour_distance_km = Column(Float, nullable=True)
    additional_time_hours = Column(Float, nullable=True)
    estimated_delivery_time = Column(DateTime, nullable=True)
    transfer_cost = Column(Numeric(10, 2), nullable=True)
    additional_transport_cost = Column(Numeric(10, 2), nullable=True)
    estimated_total_cost = Column(Numeric(10, 2), nullable=True)
    deadline_feasible = Column(Boolean, nullable=True)
    deadline_margin_minutes = Column(Integer, nullable=True)
    deadline_risk = Column(String(20), nullable=True)
    number_of_transfers = Column(Integer, nullable=True)
    transfer_complexity = Column(String(20), nullable=True)
    piggyback_score = Column(Float, nullable=True)
    match_score = Column(Integer, default=0, nullable=False)
    potential_cost_saved = Column(Numeric(10, 2), default=0.0, nullable=False)
    potential_co2_saved = Column(Numeric(10, 2), default=0.0, nullable=False)
    score_distance = Column(Float, nullable=True)
    score_time = Column(Float, nullable=True)
    score_cost = Column(Float, nullable=True)
    score_deadline = Column(Float, nullable=True)
    score_capacity = Column(Float, nullable=True)
    score_route = Column(Float, nullable=True)
    score_transfer = Column(Float, nullable=True)
    feasible = Column(Boolean, default=True, nullable=False)
    rejection_reason = Column(String(255), nullable=True)
    explanation = Column(Text, nullable=True)
    concerns_json = Column(Text, nullable=True)
    rank = Column(Integer, nullable=True)
    status = Column(String(30), default="RECOMMENDED", nullable=False)

    shipment = relationship("Shipment")
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
    candidate_route = relationship("RouteNetwork", foreign_keys=[candidate_route_id])
    pickup_hub = relationship("Hub", foreign_keys=[pickup_hub_id])
    drop_hub = relationship("Hub", foreign_keys=[drop_hub_id])
    transfer_hub = relationship("Hub", foreign_keys=[transfer_hub_id])
    second_vehicle = relationship("Vehicle", foreign_keys=[second_vehicle_id])
    second_route = relationship("RouteNetwork", foreign_keys=[second_route_id])

    @property
    def id(self):
        return self.opportunity_id

    @property
    def candidate_vehicle_id(self):
        return self.vehicle_id

    @property
    def available_capacity_kg(self):
        return float(self.available_weight_kg or 0.0)

    @property
    def available_capacity_m3(self):
        return float(self.available_volume_m3 or 0.0)


class RecoveryCandidateScoring(Base):
    __tablename__ = "recovery_candidate_scoring_table"

    scoring_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("recovery_opportunity_table.opportunity_id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)

    opportunity = relationship("RecoveryOpportunity")

    @property
    def id(self):
        return self.scoring_id


class RecoveryExecution(Base):
    __tablename__ = "recovery_execution_table"

    execution_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=False, index=True)
    pickup_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    dropoff_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    cost_saved = Column(Numeric(10, 2), nullable=False)
    co2_saved_kg = Column(Numeric(10, 2), nullable=False)
    executed_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    explanation = Column(Text, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    shipment = relationship("Shipment")
    assigned_vehicle = relationship("Vehicle")
    pickup_hub = relationship("Hub", foreign_keys=[pickup_hub_id])
    dropoff_hub = relationship("Hub", foreign_keys=[dropoff_hub_id])

    @property
    def id(self):
        return self.execution_id


class FinalEvaluation(Base):
    __tablename__ = "final_evaluation_table"

    evaluation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    original_cost = Column(Numeric(10, 2), nullable=True, default=0.0)
    recovery_cost = Column(Numeric(10, 2), nullable=True, default=0.0)
    cost_saved = Column(Numeric(10, 2), nullable=True, default=0.0)
    total_savings = Column(Numeric(10, 2), nullable=False, default=0.0)
    co2_offset = Column(Numeric(10, 2), nullable=False, default=0.0)
    time_saved_hours = Column(Float, nullable=True, default=0.0)
    deadline_met = Column(Boolean, default=True, nullable=False)
    recovery_success_status = Column(String(50), default="SUCCESSFUL", nullable=False)
    additional_distance_km = Column(Float, nullable=True, default=0.0)

    shipment = relationship("Shipment")

    @property
    def id(self):
        return self.evaluation_id


# =========================================================================
# Stage 3 Domain Models & Database Tables
# =========================================================================

class RecoveryRecommendation(Base):
    __tablename__ = "recovery_recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recommendation_id = Column(String(100), unique=True, index=True, nullable=False)
    analysis_id = Column(String(100), index=True, nullable=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    selected_opportunity_id = Column(Integer, ForeignKey("recovery_opportunity_table.opportunity_id"), nullable=True)
    recommendation_status = Column(String(50), default="PENDING_REVIEW", nullable=False, index=True)  # PENDING_REVIEW, APPROVED, REJECTED, SUPERSEDED
    recommendation_score = Column(Float, nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    shipment = relationship("Shipment")
    selected_opportunity = relationship("RecoveryOpportunity", foreign_keys=[selected_opportunity_id])
    decisions = relationship("RecoveryDecision", back_populates="recommendation", cascade="all, delete-orphan")


class RecoveryDecision(Base):
    __tablename__ = "recovery_decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recommendation_id = Column(String(100), ForeignKey("recovery_recommendations.recommendation_id"), nullable=False, index=True)
    selected_opportunity_id = Column(Integer, ForeignKey("recovery_opportunity_table.opportunity_id"), nullable=True)
    decision = Column(String(20), nullable=False)  # APPROVED or REJECTED
    dispatcher_name = Column(String(100), nullable=False)
    decision_note = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recommendation = relationship("RecoveryRecommendation", back_populates="decisions")
    selected_opportunity = relationship("RecoveryOpportunity", foreign_keys=[selected_opportunity_id])


class RecoveryImpactSnapshot(Base):
    __tablename__ = "recovery_impact_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    selected_opportunity_id = Column(Integer, ForeignKey("recovery_opportunity_table.opportunity_id"), nullable=True)
    baseline_recovery_cost = Column(Numeric(10, 2), nullable=True)
    selected_recovery_cost = Column(Numeric(10, 2), nullable=True)
    estimated_cost_savings = Column(Numeric(10, 2), nullable=True)
    baseline_delivery_time = Column(DateTime, nullable=True)
    selected_delivery_time = Column(DateTime, nullable=True)
    delivery_time_change_minutes = Column(Integer, nullable=True)
    deadline_margin_minutes = Column(Integer, nullable=True)
    additional_distance_km = Column(Float, nullable=True)
    capacity_utilization_after = Column(Float, nullable=True)
    number_of_transfers = Column(Integer, nullable=True)
    impact_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    shipment = relationship("Shipment")
    selected_opportunity = relationship("RecoveryOpportunity", foreign_keys=[selected_opportunity_id])


class AtRiskAlert(Base):
    __tablename__ = "shipment_alert_table"

    alert_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    risk_level = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    reasons_json = Column(Text, nullable=False)
    current_deviation_km = Column(Float, nullable=True, default=0.0)
    deadline_buffer_minutes = Column(Integer, nullable=True, default=0)
    created_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    shipment = relationship("Shipment")

    @property
    def id(self):
        return self.alert_id

