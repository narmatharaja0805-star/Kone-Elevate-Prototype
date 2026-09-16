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
