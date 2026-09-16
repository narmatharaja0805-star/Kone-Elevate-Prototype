from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .physics import SimInputs, run_physics_pipeline, health_band
from .ml_correction import corrector
from .assistant import explain_simulation, explain_whatif, answer_question
from .synthetic_data import FLEET

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BoltTwin API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup: seed the fleet if the DB is empty
# ---------------------------------------------------------------------------
@app.on_event("startup")
def seed_fleet():
    db = next(get_db())
    if db.query(models.Bolt).count() == 0:
        for item in FLEET:
            db.add(models.Bolt(**item))
        db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Core simulation helper (shared by /simulate and /whatif)
# ---------------------------------------------------------------------------
def _simulate(cycles, vibration_amplitude_g, temperature_c) -> dict:
    inp = SimInputs(cycles=cycles, vibration_amplitude_g=vibration_amplitude_g,
                     temperature_c=temperature_c)
    physics = run_physics_pipeline(inp)
    correction = corrector.correct(
        cycles, vibration_amplitude_g, temperature_c,
        physics.health_index_baseline, physics.preload_loss_pct, physics.fatigue_damage,
    )
    band = health_band(correction["health_index_final"])
    return {
        "preload_pct": round(physics.preload_pct, 1),
        "preload_loss_pct": round(physics.preload_loss_pct, 1),
        "fatigue_damage": round(physics.fatigue_damage, 4),
        "health_index_baseline": round(physics.health_index_baseline, 1),
        "health_index_final": correction["health_index_final"],
        "rul_cycles": round(physics.rul_cycles, 0),
        "band": band,
        "risk_breakdown_pct": physics.risk_breakdown_pct,
        "ml_correction": correction,
        "decay_curve": physics.decay_curve,
        "explanation": "",   # filled in by caller once bolt tag is known
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/bolts", response_model=list[schemas.BoltOut])
def list_bolts(db: Session = Depends(get_db)):
    return db.query(models.Bolt).all()


@app.get("/bolts/{bolt_id}", response_model=schemas.BoltOut)
def get_bolt(bolt_id: int, db: Session = Depends(get_db)):
    bolt = db.get(models.Bolt, bolt_id)
    if not bolt:
        raise HTTPException(404, "Bolt not found")
    return bolt


@app.post("/bolts/{bolt_id}/simulate", response_model=schemas.SimulationOut)
def simulate(bolt_id: int, req: schemas.SimulateRequest, db: Session = Depends(get_db)):
    bolt = db.get(models.Bolt, bolt_id)
    if not bolt:
        raise HTTPException(404, "Bolt not found")

    cycles = req.cycles if req.cycles is not None else bolt.cycles
    vib = req.vibration_amplitude_g if req.vibration_amplitude_g is not None else bolt.vibration_amplitude_g
    temp = req.temperature_c if req.temperature_c is not None else bolt.temperature_c

    result = _simulate(cycles, vib, temp)
    result["explanation"] = explain_simulation(bolt.tag, bolt.component_type, result)

    run = models.SimulationRun(bolt_id=bolt.id, **result)
    db.add(run)
    db.commit()

    return result


@app.post("/bolts/{bolt_id}/whatif", response_model=schemas.WhatIfOut)
def whatif(bolt_id: int, req: schemas.WhatIfRequest, db: Session = Depends(get_db)):
    bolt = db.get(models.Bolt, bolt_id)
    if not bolt:
        raise HTTPException(404, "Bolt not found")

    baseline = _simulate(bolt.cycles, bolt.vibration_amplitude_g, bolt.temperature_c)
    baseline["explanation"] = explain_simulation(bolt.tag, bolt.component_type, baseline)

    scenario_vib = bolt.vibration_amplitude_g * (1 + req.vibration_change_pct / 100.0)
    scenario_temp = bolt.temperature_c + req.temperature_change_c
    scenario = _simulate(bolt.cycles, scenario_vib, scenario_temp)
    scenario["explanation"] = explain_simulation(bolt.tag, bolt.component_type, scenario)

    summary = explain_whatif(bolt.tag, baseline, scenario, req.vibration_change_pct)

    return {
        "baseline": baseline,
        "scenario": scenario,
        "health_index_delta": round(scenario["health_index_final"] - baseline["health_index_final"], 1),
        "rul_delta_cycles": round(scenario["rul_cycles"] - baseline["rul_cycles"], 0),
        "summary": summary,
    }


@app.get("/bolts/{bolt_id}/ask")
def ask(bolt_id: int, q: str, db: Session = Depends(get_db)):
    bolt = db.get(models.Bolt, bolt_id)
    if not bolt:
        raise HTTPException(404, "Bolt not found")
    result = _simulate(bolt.cycles, bolt.vibration_amplitude_g, bolt.temperature_c)
    answer = answer_question(q, bolt.tag, bolt.component_type, result)
    return {"question": q, "answer": answer}


@app.get("/")
def root():
    return {"status": "BoltTwin API running", "docs": "/docs"}
