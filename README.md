# BoltTwin — Working Prototype

A physics-informed, ML-corrected digital twin for elevator bolted joints,
built with exactly the stack named in the pitch deck: Python (NumPy/SciPy)
physics engine → scikit-learn bounded ML correction → FastAPI backend →
SQLAlchemy/SQLite storage → React + Tailwind + Plotly dashboard.

Everything below was written and unit-tested; only the last "run it"
step needs to happen on your own machine (this build sandbox has no
internet access, so `pip install` / npm CDN calls couldn't be exercised
here — the physics + ML logic itself was verified directly with Python).

## Project layout

```
boltwin/
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── physics.py        # preload decay, Basquin/Miner, Goodman correction, Health Index, RUL
│       ├── ml_correction.py  # bounded Random Forest correction layer
│       ├── synthetic_data.py # MVP "sensor" data (swap for real IMU feed later)
│       ├── assistant.py      # grounded explanation generator (no external API needed)
│       ├── models.py         # SQLAlchemy ORM (Bolt, SimulationRun)
│       ├── database.py       # SQLite engine (Postgres-ready: just change the URL)
│       ├── schemas.py        # Pydantic request/response models
│       └── main.py           # FastAPI app + routes
└── frontend/
    └── index.html            # single-file React + Tailwind + Plotly dashboard
```

## Step 1 — Backend setup

```bash
cd boltwin/backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2 — Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

- On first startup it auto-creates `boltwin.db` (SQLite) and seeds 6 demo
  bolts (door, motor, guide-rail, brake — spanning HEALTHY/INSPECT/CRITICAL
  bands so your demo has variety).
- Visit **http://localhost:8000/docs** — FastAPI's auto-generated Swagger UI.
  Try `POST /bolts/2/simulate` right there before touching the frontend.

## Step 3 — Run the dashboard

No build step needed — it's a single HTML file using React/Tailwind/Plotly
from CDN.

```bash
cd ../frontend
python3 -m http.server 5173
```

Open **http://localhost:5173** in your browser. The dashboard talks to the
API at `http://localhost:8000` (edit `API_BASE` at the top of the `<script>`
in `index.html` if you run the backend elsewhere).

If you'd rather use a real dev server later (hot reload, npm ecosystem),
this same JSX can be dropped into a Vite + React + Tailwind project — the
CDN version exists purely so you can demo tonight without an npm install.

## What each piece proves, mapped to the deck

| Deck claim | Where it lives | How to show it |
|---|---|---|
| "Preload decay + Basquin/Miner fatigue + Goodman correction" | `physics.py` | Open the file — every function docstring names its formula |
| "0–100 Fastener Health Index + RUL" | `physics.run_physics_pipeline` | `/bolts/{id}/simulate` returns both |
| "Bounded ML layer, never overrides physics" | `ml_correction.py` | Response includes `ml_correction.bounded_delta` and `was_clamped` — show it's clamped to ±8 |
| "Live What-If engine" | `main.py: /bolts/{id}/whatif` + dashboard slider | Drag the vibration slider, click Run What-If, watch both charts move |
| "Grounded AI assistant, nothing is a black box" | `assistant.py` | Every sentence reads a field out of the actual result — type a question in the dashboard box |
| "Synthetic data now, IMU-ready later" | `synthetic_data.py` | Swap this module's output for a real sensor feed; nothing downstream changes |
| "PostgreSQL-ready" | `database.py` | Only `SQLALCHEMY_DATABASE_URL` needs to change |

## Demo script for the jury (5 minutes)

1. **Open the dashboard**, click through 2–3 bolts in the sidebar to show
   the fleet spans HEALTHY → INSPECT → CRITICAL bands.
2. **Pick an INSPECT-band bolt** (e.g. F-102 or F-103). Point at the Health
   Index, Preload Loss, and Remaining Life cards.
3. **Point at the Risk Contributor chart** — explain that this is *why*
   the score is what it is, not just a number.
4. **Read the Grounded Assistant paragraph aloud** — note it explicitly
   states the physics baseline vs. the ML-corrected final number.
5. **Drag the What-If slider** to −15%, click Run What-If — show the two
   bars moving and read the summary sentence: "same formulas re-run, not
   a new guess."
6. Optionally type a question into the assistant box ("why is this bolt
   at risk?") to show the Q&A isn't hardcoded per-bolt.

## Known simplifications (be upfront about these if asked)

- **Data is synthetic**, not live sensor data — architecture is designed
  to swap in real IMU/accelerometer streams (see Future Scope).
- **Vibration→stress mapping** (`alternating_stress_mpa`) uses one
  calibrated constant instead of a per-bracket FEA model — a real
  deployment would calibrate this per joint design.
- **Miner's rule** here sums damage from a single dominant stress block;
  the deck's Future Scope item ("multi-fastener joint interaction
  modelling") is exactly the extension to variable-amplitude loading.
- **ML training data is physics-simulated with a synthetic residual**
  baked in, since there's no real inspection-log dataset yet — swap
  `_synthetic_training_set()` for real (predicted vs. inspected) pairs
  once field data exists; nothing else changes.

## Upgrading the assistant later (optional)

`assistant.py` is fully rule-based today (no API key required — good for
a hackathon demo with no network dependency). If you want more fluent
phrasing for the final round, keep its output as ground truth and pass it
as context to an LLM call that's only allowed to *rephrase*, not invent,
numbers — that preserves the "nothing is a black box" claim instead of
undermining it.
