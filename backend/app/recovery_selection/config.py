"""
Configuration settings and default parameters for Stage 3 Recovery Selection & Impact Analysis.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage3Config:
    # Baselines & Thresholds
    DEDICATED_RECOVERY_BASE_COST: float = 1500.0
    HIGH_CAPACITY_UTILIZATION_PERCENT: float = 85.0
    TIGHT_DEADLINE_MARGIN_MINUTES: float = 120.0
    HIGH_TRANSFER_COUNT: int = 2

    # Score Weight Parameters (Sum = 1.0)
    WEIGHT_PIGGYBACK_SCORE: float = 0.25
    WEIGHT_COST_SAVINGS: float = 0.20
    WEIGHT_DEADLINE_BUFFER: float = 0.20
    WEIGHT_CAPACITY_IMPACT: float = 0.15
    WEIGHT_TRANSFER_SIMPLICITY: float = 0.10
    WEIGHT_DELIVERY_TIME: float = 0.10


DEFAULT_STAGE3_CONFIG = Stage3Config()
