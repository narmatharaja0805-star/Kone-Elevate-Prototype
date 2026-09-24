"""
Synthetic fleet data -- stands in for real IMU/accelerometer sensors for
the MVP demo. Each entry represents one bolted joint's current operating
summary (mean vibration amplitude, cycle count, temperature) as if it had
been aggregated from a stream of raw accelerometer samples. The pipeline
itself doesn't care whether these numbers came from a simulator or a real
sensor -- swapping this module for a live IMU feed is the only change
"real-time deployment" (Future Scope) requires.
"""

FLEET = [
    {
        "tag": "F-101", "component_type": "Door Operator", "elevator_id": "EL-A1",
        "fastener_type": "Standard Steel Bolt", "fastener_size": "M10",
        "cycles": 80_000, "vibration_amplitude_g": 0.5, "temperature_c": 32,
    },
    {
        "tag": "F-102", "component_type": "Motor Mount", "elevator_id": "EL-A1",
        "fastener_type": "Standard Steel Bolt", "fastener_size": "M16",
        "cycles": 250_000, "vibration_amplitude_g": 1.0, "temperature_c": 38,
    },
    {
        "tag": "F-103", "component_type": "Guide Rail", "elevator_id": "EL-B2",
        "fastener_type": "High-Tensile Titanium Bolt", "fastener_size": "M12",
        "cycles": 320_000, "vibration_amplitude_g": 1.3, "temperature_c": 42,
    },
    {
        "tag": "F-104", "component_type": "Brake Caliper", "elevator_id": "EL-B2",
        "fastener_type": "Standard Steel Bolt", "fastener_size": "M12",
        "cycles": 400_000, "vibration_amplitude_g": 1.9, "temperature_c": 55,
    },
    {
        "tag": "F-105", "component_type": "Door Operator", "elevator_id": "EL-C3",
        "fastener_type": "Damped Polymer Bolt", "fastener_size": "M10",
        "cycles": 150_000, "vibration_amplitude_g": 0.7, "temperature_c": 34,
    },
    {
        "tag": "F-106", "component_type": "Guide Rail", "elevator_id": "EL-C3",
        "fastener_type": "Standard Steel Bolt", "fastener_size": "M12",
        "cycles": 210_000, "vibration_amplitude_g": 0.9, "temperature_c": 36,
    },
]

ELEVATORS = [
    {
        "elevator_tag": "EL-A1",
        "building_name": "KONE HQ Tower - North",
        "floor_count": 28,
        "rated_speed_m_s": 2.5,
        "status": "ACTIVE",
    },
    {
        "elevator_tag": "EL-B2",
        "building_name": "KONE HQ Tower - South",
        "floor_count": 34,
        "rated_speed_m_s": 3.0,
        "status": "ACTIVE",
    },
    {
        "elevator_tag": "EL-C3",
        "building_name": "Innovation Center Annex",
        "floor_count": 12,
        "rated_speed_m_s": 1.75,
        "status": "ACTIVE",
    },
]

FASTENERS = [
    {
        "name": "Standard Steel Bolt",
        "size": "M10",
        "material_grade": "Grade 8.8 Structural Steel",
        "natural_frequency_hz": 40.0,
        "vibration_threshold_g": 1.5,
        "tensile_strength_mpa": 800.0,
        "damping_ratio": 0.05,
        "unit_cost_eur": 3.20,
        "manufacturer": "Würth Industry",
    },
    {
        "name": "Standard Steel Bolt",
        "size": "M12",
        "material_grade": "Grade 8.8 Structural Steel",
        "natural_frequency_hz": 50.0,
        "vibration_threshold_g": 1.5,
        "tensile_strength_mpa": 800.0,
        "damping_ratio": 0.05,
        "unit_cost_eur": 3.80,
        "manufacturer": "Würth Industry",
    },
    {
        "name": "Standard Steel Bolt",
        "size": "M16",
        "material_grade": "Grade 8.8 Structural Steel",
        "natural_frequency_hz": 65.0,
        "vibration_threshold_g": 1.5,
        "tensile_strength_mpa": 800.0,
        "damping_ratio": 0.05,
        "unit_cost_eur": 5.50,
        "manufacturer": "Würth Industry",
    },
    {
        "name": "High-Tensile Titanium Bolt",
        "size": "M12",
        "material_grade": "Ti-6Al-4V Grade 5 Titanium",
        "natural_frequency_hz": 120.0,
        "vibration_threshold_g": 2.5,
        "tensile_strength_mpa": 1100.0,
        "damping_ratio": 0.03,
        "unit_cost_eur": 24.50,
        "manufacturer": "KONE Aerospace Components",
    },
    {
        "name": "High-Tensile Titanium Bolt",
        "size": "M16",
        "material_grade": "Ti-6Al-4V Grade 5 Titanium",
        "natural_frequency_hz": 140.0,
        "vibration_threshold_g": 2.5,
        "tensile_strength_mpa": 1100.0,
        "damping_ratio": 0.03,
        "unit_cost_eur": 38.00,
        "manufacturer": "KONE Aerospace Components",
    },
    {
        "name": "Damped Polymer Bolt",
        "size": "M10",
        "material_grade": "Viscoelastic Polyurethane Composite",
        "natural_frequency_hz": 16.0,
        "vibration_threshold_g": 1.2,
        "tensile_strength_mpa": 450.0,
        "damping_ratio": 0.15,
        "unit_cost_eur": 7.00,
        "manufacturer": "Sorbothane Industrial",
    },
    {
        "name": "Damped Polymer Bolt",
        "size": "M12",
        "material_grade": "Viscoelastic Polyurethane Composite",
        "natural_frequency_hz": 20.0,
        "vibration_threshold_g": 1.2,
        "tensile_strength_mpa": 450.0,
        "damping_ratio": 0.15,
        "unit_cost_eur": 8.20,
        "manufacturer": "Sorbothane Industrial",
    },
    {
        "name": "Stainless 316 Marine-Grade Bolt",
        "size": "M12",
        "material_grade": "A4-80 Stainless Steel",
        "natural_frequency_hz": 75.0,
        "vibration_threshold_g": 1.8,
        "tensile_strength_mpa": 800.0,
        "damping_ratio": 0.04,
        "unit_cost_eur": 6.90,
        "manufacturer": "Böllhoff Fastenings",
    },
]

