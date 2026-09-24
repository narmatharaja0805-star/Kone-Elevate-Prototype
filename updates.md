# Fleet Maintenance Optimizer: Implementation Updates

## What is this feature?

At its core, this feature solves a real-world business problem: **"I have 20 broken or deteriorating parts across my elevators, but my technicians only have 5 hours today. What exactly should they fix first to prevent the worst accidents?"**

Here is a simple breakdown of what it does:

1. **Evaluates Health & Risk:** It looks at every single component (bolts, brakes, doors, etc.) across all elevators in your fleet and calculates how close they are to failing based on the live physics data.
2. **Weighs Importance (Criticality):** It knows that a failing brake is much more dangerous (high criticality) than a squeaky door (low criticality), so it calculates a "Risk Score" for each item. 
3. **Considers Time (Budget):** It checks how long each repair takes. For example, fixing a brake might take 2 hours, while fixing a door takes 30 minutes.
4. **Makes the Smartest Choices (Optimization):** Based on the "Available Tech Hours" you provide in the UI, the backend runs an algorithm (the greedy knapsack) to build the perfect schedule. It picks the combination of tasks that reduces the most risk within the time limit.

In short: **It takes the guesswork out of maintenance by automatically giving technicians the most mathematically efficient to-do list for their shift.**

## What was built

### 1. Optimization Endpoint
Added a new `GET /fleet/optimize-maintenance` endpoint that:
- Iterates over all bolts and calculates their real-time physics simulation to determine current health.
- Factors in component-specific **criticality** and **inspection time**. (For example, Brake Calipers are treated as high-criticality [10] with a 2-hour inspection time, while Door Operators are lower-criticality [3] with 0.5-hour inspections).
- Calculates a dynamic `Risk Score` and determines the `value_per_hour` of inspecting each component.
- Uses a **greedy knapsack algorithm** to sort and select the most high-value targets based on the user-provided `hours` budget.

### 2. Frontend Optimizer Dashboard
In `index.html`, we added a new `OptimizerPanel` React component that sits prominently at the top of the main area:
- **Interactive Budget:** You can easily adjust the "Available Tech Hours" using a spinner input.
- **Recommended vs. Deferred Actions:** When you run the optimizer, it clearly splits the fleet into two lists.
  - The **Recommended Actions** panel highlights the highest-priority targets that fit within your time budget.
  - The **Deferred Actions** panel lists the items that were pushed to the next maintenance cycle.
- **Immediate Insights:** It surfaces both the remaining health and the computed risk score for each recommendation, proving to users exactly *why* this order was selected.

## Validation 

If your backend terminal is running Uvicorn with `--reload`, the API changes are already live! Simply refresh your browser tab at **http://localhost:5173**. 

You should see the "Fleet Maintenance Optimizer" block at the top right side of the dashboard. Try adjusting the hours to 2.0 or 5.0 and hit **Run Optimizer** to see how it automatically re-prioritizes the fleet.

---

# True Machine Learning Layer: Implementation Updates

## What is this feature?

Right now, when your Digital Twin predicts that a part is breaking down, it relies 100% on a fixed physics formula (like calculating friction and stress). But in the real world, physics formulas aren't perfect—things like humidity, manufacturing defects, or random sensor noise can cause a part to fail slightly faster or slower than the math predicts.

**This new feature adds a "Machine Learning Brain" on top of the physics.** 

1. **Learning from Data:** Instead of just trusting the math, it looks at historical data to learn the hidden patterns of *why* parts fail faster or slower than expected.
2. **Making Corrections:** When the physics engine says a bolt is at 80% health, the ML model might step in and say, *"Wait, based on the high temperature and vibration patterns I've seen in the past, it's actually closer to 75% health."*
3. **Keeping it Safe:** To prevent the AI from going crazy and making completely wrong predictions, we put a "leash" on it (bounding). The AI is only allowed to tweak the physics prediction by a maximum of 8%. This means you get the intelligence of AI, but the safety and reliability of physics.

In short: **It makes your predictions much more accurate by using AI to learn real-world patterns that pure math can't capture.**

# Live Telemetry & Virtual Sensor Simulator

## What is this feature?

In a real deployment, a Digital Twin doesn't just sit there—it actively listens to live data streaming from IoT sensors attached to physical hardware. To demonstrate this capability in our prototype, we've built a **Live Telemetry Engine** and a **Virtual Sensor Simulator**.

1. **Live Data Pipeline:** The backend now has a dedicated endpoint (`POST /bolts/{bolt_id}/telemetry`) that acts as an intake valve for live data.
2. **Virtual IoT Gateway:** We wrote a script (`sensor_simulator.py`) that acts exactly like a physical KONE IoT gateway attached to an elevator.
3. **Simulating the Real World:** When running, the script continuously sends new data points to the backend every few seconds, increasing the elevator's cycle count and fluctuating the temperature and vibration. 

In short: **This allows you to run a highly impressive, real-time live demo. You can watch your Digital Twin dashboard update dynamically as if it were connected to a physical elevator that is actively running trips.**

---

# 3D Elevator Speed Simulation & Fastener Recommender

## What is this feature?
This feature adds a literal 3D visual model on the screen to simulate elevator speed and calculate physics in real-time.

1. **3D Visual Simulation:** Uses Three.js to render a 3D fastener model that vibrates based on the elevator speed you select.
2. **Speed as the Main Factor & Live Frequency Display:** You can slide the speed setting (m/s). The UI dynamically displays the live **Forcing Frequency** ($f = \text{Speed} \times 5.0\text{ Hz}$).
3. **Resonance and Thresholds:** Based on each fastener's **Natural Frequency ($f_n$)** and the operating forcing frequency, it calculates the amplified vibration (transmissibility/resonance).
4. **Fastener Recommendation:** Displays the natural frequencies, calculated vibration, and safety limits for various fastener types (Steel, Titanium, Polymer), clearly marking whether each passes safety thresholds.

