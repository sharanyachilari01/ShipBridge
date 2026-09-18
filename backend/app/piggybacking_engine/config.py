"""
Configuration settings for Stage 2 Piggybacking & Recovery Opportunity Engine.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class PiggybackConfig:
    # Distance thresholds (km)
    MAX_PICKUP_HUB_DISTANCE_KM: float = 20.0
    MAX_DROP_HUB_DISTANCE_KM: float = 20.0
    MAX_ACCEPTABLE_DETOUR_KM: float = 30.0
    
    # Time thresholds (hours)
    MAX_ACCEPTABLE_EXTRA_TIME_HOURS: float = 2.0
    MAX_DEADLINE_MARGIN_HOURS: float = 6.0
    DEFAULT_HANDLING_TIME_MINUTES: float = 15.0
    
    # Cost thresholds and rates
    MAX_ACCEPTABLE_RECOVERY_COST: float = 500.0
    COST_PER_KM: float = 12.0
    COST_PER_MINUTE: float = 2.0
    BASE_TRANSFER_FEE: float = 50.0
    
    # Route and Hop limits
    MAX_ROUTE_OVERLAP_REFERENCE_KM: float = 50.0
    MAX_HOPS: int = 2
    AVERAGE_VEHICLE_SPEED_KMH: float = 40.0
    
    # Deterministic Scoring Weights (Sum = 1.0)
    WEIGHT_DISTANCE: float = 0.25
    WEIGHT_TIME: float = 0.20
    WEIGHT_COST: float = 0.15
    WEIGHT_DEADLINE: float = 0.15
    WEIGHT_CAPACITY: float = 0.10
    WEIGHT_ROUTE: float = 0.10
    WEIGHT_TRANSFER: float = 0.05

DEFAULT_PIGGYBACK_CONFIG = PiggybackConfig()
