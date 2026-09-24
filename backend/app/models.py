from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .database import Base


class Bolt(Base):
    __tablename__ = "bolts"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True, index=True)               # e.g. "F-102"
    component_type = Column(String)                              # Door / Motor / Guide Rail / Brake
    elevator_id = Column(String)
    fastener_type = Column(String, default="Standard Steel Bolt")
    fastener_size = Column(String, default="M12")
    cycles = Column(Float)
    vibration_amplitude_g = Column(Float)
    temperature_c = Column(Float)

    runs = relationship("SimulationRun", back_populates="bolt")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    bolt_id = Column(Integer, ForeignKey("bolts.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    preload_pct = Column(Float)
    preload_loss_pct = Column(Float)
    fatigue_damage = Column(Float)
    health_index_baseline = Column(Float)
    health_index_final = Column(Float)
    rul_cycles = Column(Float)
    band = Column(String)
    risk_breakdown_pct = Column(JSON)
    ml_correction = Column(JSON)
    decay_curve = Column(JSON)
    explanation = Column(String)

    bolt = relationship("Bolt", back_populates="runs")


class Elevator(Base):
    __tablename__ = "elevators"

    id = Column(Integer, primary_key=True, index=True)
    elevator_tag = Column(String, unique=True, index=True)       # e.g. "EL-A1"
    building_name = Column(String)                               # e.g. "Tower A - North Wing"
    floor_count = Column(Integer)                                # e.g. 24
    rated_speed_m_s = Column(Float)                              # e.g. 2.5
    installation_date = Column(DateTime, default=datetime.utcnow)
    last_inspection_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE")                    # ACTIVE, MAINTENANCE, OFFLINE


class FastenerCatalog(Base):
    __tablename__ = "fastener_catalog"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)                            # e.g. "Standard Steel Bolt"
    size = Column(String)                                        # e.g. "M12"
    material_grade = Column(String)                              # e.g. "Grade 8.8 Steel"
    natural_frequency_hz = Column(Float)                         # e.g. 50.0
    vibration_threshold_g = Column(Float)                        # e.g. 1.5
    tensile_strength_mpa = Column(Float)                         # e.g. 800.0
    damping_ratio = Column(Float, default=0.05)                  # e.g. 0.05
    unit_cost_eur = Column(Float)                                # e.g. 4.50
    manufacturer = Column(String)                                # e.g. "Würth / KONE OEM"


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    bolt_id = Column(Integer, ForeignKey("bolts.id"), index=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    cycles = Column(Float)
    vibration_amplitude_g = Column(Float)
    temperature_c = Column(Float)
    trip_speed_m_s = Column(Float, nullable=True)

    bolt = relationship("Bolt", backref="telemetry_logs")


class MaintenanceWorkOrder(Base):
    __tablename__ = "maintenance_work_orders"

    id = Column(Integer, primary_key=True, index=True)
    elevator_id = Column(String, index=True)
    bolt_id = Column(Integer, ForeignKey("bolts.id"), nullable=True)
    priority = Column(String)                                    # CRITICAL, INSPECT, ROUTINE
    required_hours = Column(Float)
    technician_name = Column(String, nullable=True)
    status = Column(String, default="PENDING")                   # PENDING, IN_PROGRESS, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    bolt = relationship("Bolt", backref="work_orders")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    bolt_id = Column(Integer, ForeignKey("bolts.id"), index=True)
    severity = Column(String)                                    # WARNING, CRITICAL
    message = Column(String)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    is_acknowledged = Column(Integer, default=0)                 # 0: Unacknowledged, 1: Acknowledged

    bolt = relationship("Bolt", backref="alerts")

