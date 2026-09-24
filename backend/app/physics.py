"""
BoltTwin Physics Engine
=======================
Every function here maps to one named, citable formula so results are
explainable in front of a jury -- nothing in this file is a black box.

Pipeline (matches the architecture diagram):
  Vibration -> Preload Decay -> Stress state -> Goodman correction
  -> Basquin S-N curve -> Miner cumulative damage -> Risk breakdown
  -> Health Index + Remaining Useful Life (RUL)
"""
from dataclasses import dataclass, field
import numpy as np


# ---------------------------------------------------------------------------
# 1. Preload decay
# ---------------------------------------------------------------------------
def preload_remaining_pct(cycles: float, vibration_amplitude_g: float,
                           k0: float = 6.5e-7, ref_amplitude_g: float = 1.0,
                           sensitivity: float = 1.6) -> float:
    """
    Exponential preload relaxation under repeated vibration cycles.

        preload_pct(N) = 100 * exp(-k * N)
        k = k0 * (vibration_amplitude / ref_amplitude) ^ sensitivity

    This is the standard engineering approximation for vibration-induced
    bolt loosening (preload decays geometrically with cycle count; more
    severe vibration steepens the decay). k0/sensitivity are calibration
    constants that would normally be fit from bench-test data for a given
    bolt/joint design.
    """
    k = k0 * (vibration_amplitude_g / ref_amplitude_g) ** sensitivity
    return float(100.0 * np.exp(-k * cycles))


def preload_decay_curve(vibration_amplitude_g: float, max_cycles: float,
                         n_points: int = 9) -> dict:
    """Sampled decay curve for charting (mirrors the 'Preload Decay vs
    Cycles' chart)."""
    cycles = np.linspace(0, max_cycles, n_points)
    values = [preload_remaining_pct(c, vibration_amplitude_g) for c in cycles]
    return {"cycles": cycles.tolist(), "preload_remaining_pct": values}


# ---------------------------------------------------------------------------
# 2. Stress state from vibration + remaining clamp force
# ---------------------------------------------------------------------------
def alternating_stress_mpa(vibration_amplitude_g: float,
                            stress_per_g: float = 12.0) -> float:
    """
    Simplified vibration -> alternating stress mapping (sigma_a).
    In a full deployment this constant comes from an FEA modal/harmonic
    model of the specific bracket; here it's a calibrated linear factor
    so the MVP can run without a per-part FEA model.
    """
    return vibration_amplitude_g * stress_per_g


def mean_stress_mpa(preload_pct: float, design_preload_stress_mpa: float = 220.0) -> float:
    """Mean stress (sigma_m) from the clamping force still present."""
    return (preload_pct / 100.0) * design_preload_stress_mpa


def goodman_corrected_stress(sigma_a: float, sigma_m: float,
                              sigma_ultimate_mpa: float = 830.0) -> float:
    """
    Goodman relation: converts a stress state with non-zero mean stress
    into an equivalent fully-reversed stress amplitude, because mean
    (clamping) stress makes fatigue worse than alternating stress alone
    would predict.

        sigma_ar = sigma_a / (1 - sigma_m / sigma_ultimate)
    """
    denom = max(1e-6, 1.0 - (sigma_m / sigma_ultimate_mpa))
    return sigma_a / denom


# ---------------------------------------------------------------------------
# 3. Basquin S-N fatigue life + Miner cumulative damage
# ---------------------------------------------------------------------------
def basquin_cycles_to_failure(sigma_ar_mpa: float,
                               sigma_f_prime_mpa: float = 1200.0,
                               b_exponent: float = -0.09) -> float:
    """
    Basquin's equation (strain/stress-life S-N relation):

        sigma_ar = sigma_f' * (2 * N_f) ^ b

    Solved for N_f (cycles to failure at this stress amplitude):

        N_f = 0.5 * (sigma_ar / sigma_f')^(1/b)
    """
    ratio = sigma_ar_mpa / sigma_f_prime_mpa
    n_f = 0.5 * (ratio ** (1.0 / b_exponent))
    return float(max(n_f, 1.0))


def miner_damage_fraction(current_cycles: float, n_f_cycles: float) -> float:
    """
    Miner's rule: cumulative fatigue damage as a fraction of life used.
    D = 1.0 means the S-N curve predicts failure.

        D = sum(n_i / N_f,i)   -- single dominant stress block for the MVP
    """
    return float(min(current_cycles / n_f_cycles, 1.0))


# ---------------------------------------------------------------------------
# 4. Risk breakdown, Health Index, RUL
# ---------------------------------------------------------------------------
WEIGHTS = {
    "preload_loss": 0.55,
    "vibration_severity": 0.35,
    "temperature": 0.05,
    "fatigue_damage": 0.05,
}

BAND_THRESHOLDS = [(70, "HEALTHY"), (40, "INSPECT"), (0, "CRITICAL")]


def health_band(health_index: float) -> str:
    for threshold, name in BAND_THRESHOLDS:
        if health_index >= threshold:
            return name
    return "CRITICAL"


@dataclass
class SimInputs:
    cycles: float
    vibration_amplitude_g: float
    reference_vibration_g: float = 0.6      # "normal" fleet baseline
    temperature_c: float = 35.0
    reference_temperature_c: float = 35.0
    max_temperature_c: float = 90.0


@dataclass
class PhysicsResult:
    preload_pct: float
    preload_loss_pct: float
    sigma_a: float
    sigma_m: float
    sigma_ar: float
    n_f_cycles: float
    fatigue_damage: float
    risk_breakdown_pct: dict
    health_index_baseline: float
    rul_cycles: float
    decay_curve: dict = field(default_factory=dict)


def run_physics_pipeline(inp: SimInputs) -> PhysicsResult:
    preload_pct = preload_remaining_pct(inp.cycles, inp.vibration_amplitude_g)
    preload_loss_pct = 100.0 - preload_pct

    sigma_a = alternating_stress_mpa(inp.vibration_amplitude_g)
    sigma_m = mean_stress_mpa(preload_pct)
    sigma_ar = goodman_corrected_stress(sigma_a, sigma_m)

    n_f = basquin_cycles_to_failure(sigma_ar)
    damage = miner_damage_fraction(inp.cycles, n_f)

    # --- normalized (0-1) severity of each contributor, for the risk mix ---
    preload_severity = min(preload_loss_pct / 45.0, 1.0)          # 45% loss ~ severe
    vibration_severity = min(inp.vibration_amplitude_g / (3 * inp.reference_vibration_g), 1.0)
    temp_severity = max(0.0, min(
        (inp.temperature_c - inp.reference_temperature_c) /
        (inp.max_temperature_c - inp.reference_temperature_c), 1.0))
    fatigue_severity = damage

    raw = {
        "preload_loss": preload_severity * WEIGHTS["preload_loss"],
        "vibration_severity": vibration_severity * WEIGHTS["vibration_severity"],
        "temperature": temp_severity * WEIGHTS["temperature"],
        "fatigue_damage": fatigue_severity * WEIGHTS["fatigue_damage"],
    }
    total_risk = sum(raw.values())
    total_risk = min(total_risk, 1.0)
    # contribution breakdown as % of TOTAL risk (matches the pie/bar on slide 7)
    breakdown_pct = {k: (0.0 if total_risk == 0 else round(100 * v / sum(raw.values()), 1))
                     for k, v in raw.items()}

    health_index_baseline = 100.0 * (1.0 - total_risk)

    # RUL: cycles remaining until whichever mechanism is more limiting hits
    # its critical boundary -- preload dropping below 50% clamp, or Miner
    # damage reaching 1.0. Whichever comes first is the "governing mechanism".
    k = 6.5e-7 * (inp.vibration_amplitude_g / 1.0) ** 1.6
    cycles_to_preload_critical = (np.log(100.0 / 50.0) / k) if k > 0 else float("inf")
    cycles_to_fatigue_critical = n_f
    rul_preload = max(cycles_to_preload_critical - inp.cycles, 0)
    rul_fatigue = max(cycles_to_fatigue_critical - inp.cycles, 0)
    rul_cycles = float(min(rul_preload, rul_fatigue))

    decay_curve = preload_decay_curve(inp.vibration_amplitude_g,
                                       max_cycles=inp.cycles + rul_cycles + 1)

    return PhysicsResult(
        preload_pct=preload_pct,
        preload_loss_pct=preload_loss_pct,
        sigma_a=sigma_a,
        sigma_m=sigma_m,
        sigma_ar=sigma_ar,
        n_f_cycles=n_f,
        fatigue_damage=damage,
        risk_breakdown_pct=breakdown_pct,
        health_index_baseline=health_index_baseline,
        rul_cycles=rul_cycles,
        decay_curve=decay_curve,
    )

# ---------------------------------------------------------------------------
# 5. Fastener Resonance (3D Speed Simulation)
# ---------------------------------------------------------------------------
def calculate_resonance(speed_m_s: float, natural_frequency_hz: float, 
                        damping_ratio: float = 0.05, base_vibration_g: float = 0.5) -> float:
    """
    Calculates the amplified vibration (g) due to resonance.
    Forcing frequency is assumed proportional to elevator speed (e.g., 5 Hz per m/s).
    Uses the standard transmissibility formula for a 1-DOF system.
    """
    forcing_frequency_hz = speed_m_s * 5.0  # simple linear mapping
    frequency_ratio = forcing_frequency_hz / max(natural_frequency_hz, 0.1)
    
    # Amplification factor (Transmissibility)
    transmissibility = 1.0 / np.sqrt((1.0 - frequency_ratio**2)**2 + (2.0 * damping_ratio * frequency_ratio)**2)
    
    return float(base_vibration_g * transmissibility)

