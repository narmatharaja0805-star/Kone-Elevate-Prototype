import time
import random
import requests

API_URL = "http://localhost:8000"

def get_all_bolts():
    try:
        response = requests.get(f"{API_URL}/bolts")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error connecting to backend: {e}")
        return []

def main():
    print("Starting Virtual Sensor Simulator...")
    print("Waiting for API to be available...")
    
    bolts = []
    while not bolts:
        bolts = get_all_bolts()
        if not bolts:
            time.sleep(2)

    print(f"Discovered {len(bolts)} bolts in the fleet. Starting telemetry stream...")

    # Dictionary to keep track of our current simulated state for each bolt
    state = {}
    for b in bolts:
        state[b["id"]] = {
            "cycles": b["cycles"],
            "vibration": b["vibration_amplitude_g"],
            "temperature": b["temperature_c"]
        }

    try:
        while True:
            print("\n--- Sending Telemetry Batch ---")
            for b in bolts:
                bid = b["id"]
                current = state[bid]
                
                # Add 5 to 15 cycles (simulating elevator trips)
                current["cycles"] += random.uniform(5, 15)
                
                # Inject a little bit of noise (drift) to vibration and temperature
                # E.g., drift temperature up to +/- 1.0 degree
                current["temperature"] += random.uniform(-1.0, 1.5)
                # Ensure temperature stays somewhat realistic (not below ambient)
                current["temperature"] = max(20.0, current["temperature"])
                
                # Vibration drift
                current["vibration"] += random.uniform(-0.02, 0.03)
                current["vibration"] = max(0.1, current["vibration"])

                payload = {
                    "cycles": current["cycles"],
                    "vibration_amplitude_g": current["vibration"],
                    "temperature_c": current["temperature"]
                }
                
                try:
                    requests.post(f"{API_URL}/bolts/{bid}/telemetry", json=payload)
                    print(f"Sent {b['tag']} | Temp: {payload['temperature_c']:.1f}°C, Vib: {payload['vibration_amplitude_g']:.2f}g, Cycles: {payload['cycles']:.0f}")
                except Exception as e:
                    print(f"Failed to update {b['tag']}: {e}")

            time.sleep(3)  # Wait 3 seconds before next telemetry push
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")

if __name__ == "__main__":
    main()
