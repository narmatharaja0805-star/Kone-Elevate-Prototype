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
        "cycles": 80_000, "vibration_amplitude_g": 0.5, "temperature_c": 32,
    },
    {
        "tag": "F-102", "component_type": "Motor Mount", "elevator_id": "EL-A1",
        "cycles": 250_000, "vibration_amplitude_g": 1.0, "temperature_c": 38,
    },
    {
        "tag": "F-103", "component_type": "Guide Rail", "elevator_id": "EL-B2",
        "cycles": 320_000, "vibration_amplitude_g": 1.3, "temperature_c": 42,
    },
    {
        "tag": "F-104", "component_type": "Brake Caliper", "elevator_id": "EL-B2",
        "cycles": 400_000, "vibration_amplitude_g": 1.9, "temperature_c": 55,
    },
    {
        "tag": "F-105", "component_type": "Door Operator", "elevator_id": "EL-C3",
        "cycles": 150_000, "vibration_amplitude_g": 0.7, "temperature_c": 34,
    },
    {
        "tag": "F-106", "component_type": "Guide Rail", "elevator_id": "EL-C3",
        "cycles": 210_000, "vibration_amplitude_g": 0.9, "temperature_c": 36,
    },
]
