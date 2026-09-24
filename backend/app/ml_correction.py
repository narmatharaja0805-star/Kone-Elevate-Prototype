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

from .physics import SimInputs, run_physics_pipeline

from sklearn.ensemble import RandomForestRegressor

MAX_CORRECTION = 8.0   # points, on a 0-100 Health Index scale
RANDOM_SEED = 42

class BoundedCorrector:
    """Predicts a clamped correction delta using a trained Random Forest model."""

    def __init__(self):
        # Generate a synthetic training dataset
        np.random.seed(RANDOM_SEED)
        
        # 500 simulated data points representing past historical data
        n_samples = 500
        cycles = np.random.uniform(0, 500_000, n_samples)
        vibration = np.random.uniform(0.1, 2.5, n_samples)
        temperature = np.random.uniform(20, 80, n_samples)
        
        # Calculate the "true" residual using our unmodeled physics equation + random noise
        true_residuals = (
            -3.0 * (temperature > 55) 
            + 2.0 * np.sin(cycles / 40_000) 
            - 1.5 * (vibration > 1.5)
        )
        
        # Add random noise to simulate real-world sensor/environmental noise
        noise = np.random.normal(0, 0.5, n_samples)
        y = true_residuals + noise
        
        # Create features matrix X
        X = np.column_stack((cycles, vibration, temperature))
        
        # Train the Random Forest Regressor
        self.model = RandomForestRegressor(n_estimators=50, random_state=RANDOM_SEED)
        self.model.fit(X, y)

    def correct(self, cycles, vibration_amplitude_g, temperature_c,
                health_index_baseline, preload_loss_pct, fatigue_damage) -> dict:
        
        # Prepare the input feature array
        X_input = np.array([[cycles, vibration_amplitude_g, temperature_c]])
        
        # Ask the Random Forest to predict the residual
        predicted_residual = self.model.predict(X_input)[0]
        
        raw_delta = float(predicted_residual)
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
