from __future__ import annotations

from .models import FrequencyMetrics, IdentifiedModel, PIDRecommendation


def generate_pid_recommendations(model: IdentifiedModel, frequency: FrequencyMetrics) -> list[PIDRecommendation]:
    tau = max(model.time_constant_s, 0.02)
    delay = max(model.dead_time_s, 0.005)
    gain = max(abs(model.gain), 0.05)

    presets = [
        ("conservative", 3.5, "low"),
        ("balanced", 2.5, "medium"),
        ("aggressive", 1.7, "high"),
    ]

    recommendations: list[PIDRecommendation] = []
    for preset, lambda_factor, risk in presets:
        closed_loop_tau = max(delay * lambda_factor, 0.03)
        kp = tau / (gain * (closed_loop_tau + delay))
        ki = kp / max(tau + delay * 0.5, 0.02)
        kd = kp * delay * 0.35

        rationale = [
            f"Derived from an IMC-style FOPDT tuning law with lambda factor {lambda_factor:.1f}.",
            f"Model fit score is {model.fit_score:.2f}, so the {preset} preset emphasizes {'robustness' if preset == 'conservative' else 'response speed' if preset == 'aggressive' else 'balanced tracking'}.",
        ]
        if frequency.noise_frequency_hz > frequency.bandwidth_estimate_hz * 1.5:
            kd *= 0.8
            rationale.append("Derivative gain was softened because high-frequency noise is visible in the log.")
        if frequency.latency_s > 0.05:
            kp *= 0.9
            kd *= 0.9
            rationale.append("Delay compensation reduced P and D slightly to preserve robustness.")
        if model.damping_ratio < 0.45:
            kp *= 0.92
            kd *= 1.05
            rationale.append("The identified plant appears lightly damped, so the controller biases slightly toward damping.")
        if model.fit_score < 0.60:
            kp *= 0.95
            ki *= 0.92
            rationale.append("Integral action was slightly reduced because identification confidence is not yet strong.")
        if model.fit_score < 0.45 and preset == "aggressive":
            kp *= 0.85
            ki *= 0.9
            rationale.append("Aggressive preset was tempered because identification confidence is limited.")
        if preset == "conservative":
            ki *= 0.95
        elif preset == "aggressive":
            kp *= 1.05
            ki *= 1.03

        kp = max(kp, 0.001)
        ki = max(ki, 0.0)
        kd = max(kd, 0.0)

        recommendations.append(
            PIDRecommendation(
                preset=preset,
                kp=round(kp, 5),
                ki=round(ki, 5),
                kd=round(kd, 5),
                risk=risk,
                rationale=rationale,
            )
        )

    return recommendations
