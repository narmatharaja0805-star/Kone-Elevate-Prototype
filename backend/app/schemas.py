from typing import Optional
from pydantic import BaseModel


class BoltOut(BaseModel):
    id: int
    tag: str
    component_type: str
    elevator_id: str
    fastener_type: str
    fastener_size: str
    cycles: float
    vibration_amplitude_g: float
    temperature_c: float

    class Config:
        from_attributes = True


class SimulateRequest(BaseModel):
    # Optional overrides -- if omitted, the bolt's stored sensor summary is used
    cycles: Optional[float] = None
    vibration_amplitude_g: Optional[float] = None
    temperature_c: Optional[float] = None


class WhatIfRequest(BaseModel):
    vibration_change_pct: float = 0.0     # e.g. -15 means "reduce vibration by 15%"
    temperature_change_c: float = 0.0


class SimulationOut(BaseModel):
    preload_pct: float
    preload_loss_pct: float
    fatigue_damage: float
    health_index_baseline: float
    health_index_final: float
    rul_cycles: float
    band: str
    risk_breakdown_pct: dict
    ml_correction: dict
    decay_curve: dict
    explanation: str

    class Config:
        from_attributes = True


class WhatIfOut(BaseModel):
    baseline: SimulationOut
    scenario: SimulationOut
    health_index_delta: float
    rul_delta_cycles: float
    summary: str


class MaintenanceAction(BaseModel):
    id: int
    tag: str
    component_type: str
    health_index: float
    risk_score: float
    inspection_hours: float


class OptimizeMaintenanceResponse(BaseModel):
    selected: list[MaintenanceAction]
    deferred: list[MaintenanceAction]
    total_hours_used: float
    total_risk_mitigated: float


class TelemetryPayload(BaseModel):
    cycles: float
    vibration_amplitude_g: float
    temperature_c: float


class FastenerSuggestionRequest(BaseModel):
    speed_m_s: float
    bolt_id: int

class FastenerOption(BaseModel):
    type: str
    size: str
    natural_frequency_hz: float
    vibration_threshold_g: float
    calculated_vibration_g: float
    is_safe: bool

class FastenerSuggestionResponse(BaseModel):
    speed_m_s: float
    forcing_frequency_hz: float
    current_type: str
    current_size: str
    options: list[FastenerOption]
    recommended_fastener: str
    recommended_size: str

