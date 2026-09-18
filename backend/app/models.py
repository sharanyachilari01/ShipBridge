from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Hub(Base):
    __tablename__ = "hub_table"

    hub_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(30), unique=True, index=True, nullable=False)
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


class Vehicle(Base):
    __tablename__ = "vehicle_table"

    vehicle_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_code = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False)
    capacity_kg = Column(Numeric(10, 2), nullable=False)
    assigned_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True, index=True)
    status = Column(String(30), default="ACTIVE", nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    assigned_hub = relationship("Hub", foreign_keys=[assigned_hub_id])

    @property
    def id(self):
        return self.vehicle_id


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


class VehicleRoute(Base):
    __tablename__ = "vehicle_route_table"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=False)
    route_id = Column(Integer, ForeignKey("route_network_table.route_id"), nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    vehicle = relationship("Vehicle")
    route = relationship("RouteNetwork")


class Shipment(Base):
    __tablename__ = "shipment_table"

    shipment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tracking_number = Column(String(50), unique=True, index=True, nullable=False)
    origin_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    destination_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=False, index=True)
    expected_next_hub_id = Column(Integer, ForeignKey("hub_table.hub_id"), nullable=True, index=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=True, index=True)
    shipment_priority = Column(String(20), default="NORMAL", nullable=False)  # NORMAL, HIGH, CRITICAL
    current_status = Column(String(30), default="ON_TRACK", nullable=False, index=True)  # ON_TRACK, MISPLACED, RECOVERING, DELIVERED, DELAYED
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
        return self.shipment_weight_kg

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
    exception_type = Column(String(50), nullable=False)  # MISPLACEMENT_DETECTED, ROUTE_DEVIATION, DELAY_RISK
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


class RecoveryOpportunity(Base):
    __tablename__ = "recovery_opportunity_table"

    opportunity_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(Integer, ForeignKey("shipment_table.shipment_id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_table.vehicle_id"), nullable=False, index=True)
    match_score = Column(Integer, nullable=False)
    potential_cost_saved = Column(Numeric(10, 2), nullable=False)
    potential_co2_saved = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), default="RECOMMENDED", nullable=False)

    shipment = relationship("Shipment")
    vehicle = relationship("Vehicle")

    @property
    def id(self):
        return self.opportunity_id


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

