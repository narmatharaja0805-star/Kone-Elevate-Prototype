"""
BoltTwin - Grounded Assistant
=============================
"Grounded" means every sentence is built by reading fields out of the
actual SimulationResult -- there is no free-generation step that could
hallucinate a number. This keeps the MVP dependency-free (no API key
needed to demo). If you want a more fluent narrator for the final
presentation, keep this function's OUTPUT as the source of truth and pass
it as context to an LLM call that is only allowed to *rephrase*, never
invent, numbers -- see README "Upgrading the assistant".
"""


def explain_simulation(bolt_tag: str, component_type: str, result: dict) -> str:
    top_contributor = max(result["risk_breakdown_pct"], key=result["risk_breakdown_pct"].get)
    top_pct = result["risk_breakdown_pct"][top_contributor]
    label_map = {
        "preload_loss": "preload (clamping force) loss",
        "vibration_severity": "vibration severity",
        "temperature": "operating temperature",
        "fatigue_damage": "accumulated fatigue damage",
    }

    band = result["band"]
    hi = result["health_index_final"]
    rul = result["rul_cycles"]
    loss = result["preload_loss_pct"]

    band_sentence = {
        "HEALTHY": "no action is needed at the next scheduled inspection.",
        "INSPECT": "this joint should be prioritized at the next inspection window.",
        "CRITICAL": "this joint should be inspected before its next scheduled cycle -- risk is elevated now.",
    }[band]

    correction = result["ml_correction"]
    ml_note = (
        f"The physics model alone put this at {result['health_index_baseline']:.1f}; "
        f"the bounded ML layer adjusted it by {correction['bounded_delta']:+.1f} points "
        f"(clamped to ±8, so it can refine but never override the physics) "
        f"to a final Health Index of {hi:.1f}."
    )

    return (
        f"Bolt {bolt_tag} ({component_type}) has a Health Index of {hi:.1f}/100, "
        f"in the {band} band -- {band_sentence} "
        f"The governing risk driver is {label_map[top_contributor]}, contributing "
        f"{top_pct:.1f}% of the total risk score, with preload loss currently at {loss:.1f}%. "
        f"At the current trend, an estimated {rul:,.0f} cycles remain before this joint "
        f"crosses into critical territory. {ml_note}"
    )


def explain_whatif(bolt_tag: str, baseline: dict, scenario: dict, vib_change_pct: float) -> str:
    hi_delta = scenario["health_index_final"] - baseline["health_index_final"]
    rul_delta = scenario["rul_cycles"] - baseline["rul_cycles"]
    direction = "reducing" if vib_change_pct < 0 else "increasing"
    return (
        f"{direction.capitalize()} vibration amplitude by {abs(vib_change_pct):.0f}% on {bolt_tag} "
        f"changes the Health Index from {baseline['health_index_final']:.1f} to "
        f"{scenario['health_index_final']:.1f} ({hi_delta:+.1f} points) and remaining life from "
        f"{baseline['rul_cycles']:,.0f} to {scenario['rul_cycles']:,.0f} cycles "
        f"({rul_delta:+,.0f} cycles). This re-runs the same preload-decay and Basquin/Miner "
        f"fatigue formulas with the changed input -- it is not a new guess."
    )


def answer_question(question: str, bolt_tag: str, component_type: str, result: dict) -> str:
    """Very small rule-based router over the same grounded fields -- lets
    the dashboard offer a 'chat' box without needing an external LLM."""
    q = question.lower()
    if "why" in q or "cause" in q or "driver" in q:
        top = max(result["risk_breakdown_pct"], key=result["risk_breakdown_pct"].get)
        return (f"The dominant driver for {bolt_tag} is "
                f"{top.replace('_', ' ')} at {result['risk_breakdown_pct'][top]:.1f}% "
                f"of total risk.")
    if "life" in q or "rul" in q or "remaining" in q:
        return f"{bolt_tag} has an estimated {result['rul_cycles']:,.0f} cycles of remaining useful life."
    if "health" in q or "score" in q or "index" in q:
        return f"{bolt_tag}'s current Health Index is {result['health_index_final']:.1f}/100 ({result['band']})."
    if "preload" in q:
        return f"{bolt_tag} has lost {result['preload_loss_pct']:.1f}% of its original preload (clamping force)."
    if "ml" in q or "machine learning" in q or "correction" in q:
        c = result["ml_correction"]
        return (f"The ML layer applied a {c['bounded_delta']:+.1f}-point correction to the physics "
                f"baseline of {result['health_index_baseline']:.1f}, bounded to ±8 points.")
    return explain_simulation(bolt_tag, component_type, result)
