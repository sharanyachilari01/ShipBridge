from pydantic import BaseModel


class DetectionConfig(BaseModel):
    max_off_route_distance_km: float = 15.0
    score_normalizer_corridor_km: float = 30.0
    score_normalizer_heading_deg: float = 90.0
    low_speed_cutoff_kmh: float = 20.0
    min_persistent_observations: int = 3
    max_gps_accuracy_meters: float = 50.0
    vehicle_transfer_grace_minutes: float = 15.0
    signal_loss_threshold_hours: float = 3.0
    misplaced_score_threshold: float = 0.65

    # Composite score weights: 0.40*S_corridor + 0.35*S_heading + 0.25*S_unbind
    weight_corridor: float = 0.40
    weight_heading: float = 0.35
    weight_unbind: float = 0.25


DEFAULT_CONFIG = DetectionConfig()
