from __future__ import annotations

from .models import AxisReport, PIDRecommendation, SimulationMetrics


def simulation_cost(metrics: SimulationMetrics) -> float:
    penalty = 0.0
    if not metrics.stable:
        penalty += 50.0
    penalty += min(metrics.rise_time_s, 10.0) * 1.2
    penalty += min(metrics.settling_time_s, 10.0) * 1.5
    penalty += metrics.overshoot_pct * 0.08
    penalty += metrics.steady_state_error * 25.0
    penalty += metrics.control_effort_rms * 0.4
    penalty += max(0.0, metrics.peak_control - 4.0) * 8.0
    return float(penalty)


def best_recommendation(axis_report: AxisReport) -> PIDRecommendation:
    return min(
        axis_report.recommendations,
        key=lambda recommendation: simulation_cost(axis_report.simulations[recommendation.preset]),
    )


def recommendation_rank(axis_report: AxisReport) -> list[tuple[PIDRecommendation, SimulationMetrics, float]]:
    ranked: list[tuple[PIDRecommendation, SimulationMetrics, float]] = []
    for recommendation in axis_report.recommendations:
        simulation = axis_report.simulations[recommendation.preset]
        ranked.append((recommendation, simulation, simulation_cost(simulation)))
    ranked.sort(key=lambda item: item[2])
    return ranked
