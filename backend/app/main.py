from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db
from .physics import SimInputs, run_physics_pipeline, health_band, calculate_resonance
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


@app.post("/bolts/{bolt_id}/telemetry", response_model=schemas.BoltOut)
def update_telemetry(bolt_id: int, req: schemas.TelemetryPayload, db: Session = Depends(get_db)):
    bolt = db.get(models.Bolt, bolt_id)
    if not bolt:
        raise HTTPException(404, "Bolt not found")
    
    bolt.cycles = req.cycles
    bolt.vibration_amplitude_g = req.vibration_amplitude_g
    bolt.temperature_c = req.temperature_c
    
    db.commit()
    db.refresh(bolt)
    return bolt


@app.get("/fleet/optimize-maintenance", response_model=schemas.OptimizeMaintenanceResponse)
def optimize_maintenance(hours: float = 5.0, db: Session = Depends(get_db)):
    # Hardcoded component properties: criticality (1-10) and inspection hours
    COMPONENT_PROPS = {
        "Brake Caliper": {"criticality": 10, "hours": 2.0},
        "Motor Mount": {"criticality": 7, "hours": 1.5},
        "Guide Rail": {"criticality": 5, "hours": 1.0},
        "Door Operator": {"criticality": 3, "hours": 0.5},
    }
    
    bolts = db.query(models.Bolt).all()
    actions = []
    
    for b in bolts:
        # Get simulated health
        sim = _simulate(b.cycles, b.vibration_amplitude_g, b.temperature_c)
        health = sim["health_index_final"]
        
        props = COMPONENT_PROPS.get(b.component_type, {"criticality": 5, "hours": 1.0})
        risk = (100 - health) * props["criticality"]
        value_per_hour = risk / props["hours"]
        
        actions.append({
            "action": schemas.MaintenanceAction(
                id=b.id,
                tag=b.tag,
                component_type=b.component_type,
                health_index=round(health, 1),
                risk_score=round(risk, 1),
                inspection_hours=props["hours"]
            ),
            "value_per_hour": value_per_hour
        })
        
    # Greedy knapsack: sort by value per hour descending
    actions.sort(key=lambda x: x["value_per_hour"], reverse=True)
    
    selected = []
    deferred = []
    hours_used = 0.0
    risk_mitigated = 0.0
    
    for item in actions:
        act = item["action"]
        if hours_used + act.inspection_hours <= hours:
            selected.append(act)
            hours_used += act.inspection_hours
            risk_mitigated += act.risk_score
        else:
            deferred.append(act)
            
    return schemas.OptimizeMaintenanceResponse(
        selected=selected,
        deferred=deferred,
        total_hours_used=round(hours_used, 1),
        total_risk_mitigated=round(risk_mitigated, 1)
    )


@app.post("/simulate-speed", response_model=schemas.FastenerSuggestionResponse)
def simulate_speed(req: schemas.FastenerSuggestionRequest):
    speed = req.speed_m_s
    forcing_freq = speed * 5.0
    
    fasteners = [
        {"type": "Standard Steel Bolt", "freq": 50.0, "thresh": 1.5},
        {"type": "High-Tensile Titanium Bolt", "freq": 120.0, "thresh": 2.5},
        {"type": "Damped Polymer Bolt", "freq": 20.0, "thresh": 1.2}
    ]
    
    options = []
    recommended = None
    best_margin = -float('inf')
    
    for f in fasteners:
        vib = calculate_resonance(speed, f["freq"], base_vibration_g=0.5)
        is_safe = vib < f["thresh"]
        
        options.append({
            "type": f["type"],
            "natural_frequency_hz": f["freq"],
            "vibration_threshold_g": f["thresh"],
            "calculated_vibration_g": round(vib, 3),
            "is_safe": is_safe
        })
        
        margin = f["thresh"] - vib
        if is_safe and margin > best_margin:
            best_margin = margin
            recommended = f["type"]
            
    # If none are safe, pick the one with highest threshold
    if not recommended:
        recommended = "High-Tensile Titanium Bolt"
        
    return schemas.FastenerSuggestionResponse(
        speed_m_s=speed,
        forcing_frequency_hz=forcing_freq,
        options=options,
        recommended_fastener=recommended
    )

@app.get("/")
def root():
    return {"status": "BoltTwin API running", "docs": "/docs"}
