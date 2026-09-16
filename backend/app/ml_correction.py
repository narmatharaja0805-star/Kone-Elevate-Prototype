"""
BoltTwin - Bounded ML Correction Layer
=======================================
The physics engine gives a baseline Health Index. Real bolts deviate from
idealized physics slightly (surface finish, installation torque scatter,
sensor noise, minor unmodeled effects). A Random Forest learns to predict
that residual from operating features -- but the correction is CLAMPED to
+/- MAX_CORRECTION points, so the ML layer can refine, never override, the
physics. This is what "bounded ML" on the slide means, concretely.

Because this is an MVP with no real inspection-log dataset yet, the model
is trained on physics-simulated data with a small synthetic residual baked
in (representing the kind of unmodeled effect a real dataset would contain).
Swap `_synthetic_training_set()` for real logged (predicted vs. inspected)
pairs once field data exists -- nothing else in this module needs to change.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from .physics import SimInputs, run_physics_pipeline

MAX_CORRECTION = 8.0   # points, on a 0-100 Health Index scale
RANDOM_SEED = 42


def _synthetic_training_set(n_samples: int = 800):
    rng = np.random.default_rng(RANDOM_SEED)
    X, y_residual = [], []
    for _ in range(n_samples):
        cycles = rng.uniform(0, 450_000)
        vib = rng.uniform(0.2, 2.2)
        temp = rng.uniform(20, 70)
        inp = SimInputs(cycles=cycles, vibration_amplitude_g=vib, temperature_c=temp)
        r = run_physics_pipeline(inp)

        # Simulated "ground truth" = physics baseline + a bounded unmodeled
        # effect (e.g. installation torque scatter, surface wear) so the
        # forest has something real, bounded, and non-trivial to learn.
        unmodeled = (
            -3.0 * (temp > 55)                       # heat accelerates loosening
            + 2.0 * np.sin(cycles / 40_000)          # cyclic environmental noise
            - 1.5 * (vib > 1.5)                      # high-vibration extra wear
            + rng.normal(0, 1.0)                     # measurement noise
        )
        unmodeled = float(np.clip(unmodeled, -MAX_CORRECTION, MAX_CORRECTION))

        X.append([cycles, vib, temp, r.health_index_baseline,
                  r.preload_loss_pct, r.fatigue_damage])
        y_residual.append(unmodeled)
    return np.array(X), np.array(y_residual)


class BoundedCorrector:
    """Trains once at process start; predicts a clamped correction delta."""

    def __init__(self):
        X, y = _synthetic_training_set()
        self.model = RandomForestRegressor(
            n_estimators=200, max_depth=6, random_state=RANDOM_SEED
        )
        self.model.fit(X, y)

    def correct(self, cycles, vibration_amplitude_g, temperature_c,
                health_index_baseline, preload_loss_pct, fatigue_damage) -> dict:
        features = np.array([[cycles, vibration_amplitude_g, temperature_c,
                               health_index_baseline, preload_loss_pct, fatigue_damage]])
        raw_delta = float(self.model.predict(features)[0])
        bounded_delta = float(np.clip(raw_delta, -MAX_CORRECTION, MAX_CORRECTION))
        corrected_hi = float(np.clip(health_index_baseline + bounded_delta, 0, 100))
        return {
            "raw_delta": round(raw_delta, 2),
            "bounded_delta": round(bounded_delta, 2),
            "was_clamped": abs(raw_delta) > MAX_CORRECTION,
            "health_index_final": round(corrected_hi, 1),
        }


# Singleton -- trained once when the API process starts.
corrector = BoundedCorrector()
