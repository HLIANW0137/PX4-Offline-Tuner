from __future__ import annotations

import numpy as np

from .models import IdentifiedModel, PIDRecommendation, SimulationMetrics


def simulate_closed_loop(model: IdentifiedModel, recommendation: PIDRecommendation, duration_s: float = 2.5, sample_rate_hz: float = 200.0) -> SimulationMetrics:
    dt = 1.0 / sample_rate_hz
    steps = int(duration_s * sample_rate_hz)
    setpoint = np.ones(steps)
    y = np.zeros(steps)
    u = np.zeros(steps)
    e_prev = 0.0
    integral = 0.0
    delay_steps = int(model.dead_time_s / dt)
    delayed_u = np.zeros(steps + delay_steps + 1)
    integral_limit = 4.0 / max(recommendation.ki, 0.1)

    for idx in range(1, steps):
        error = setpoint[idx] - y[idx - 1]
        integral += error * dt
        integral = float(np.clip(integral, -integral_limit, integral_limit))
        derivative = (error - e_prev) / dt
        u[idx] = (
            recommendation.kp * error
            + recommendation.ki * integral
            + recommendation.kd * derivative
        )
        u[idx] = float(np.clip(u[idx], -5.0, 5.0))

        plant_u = delayed_u[idx - delay_steps] if idx >= delay_steps else 0.0
        y_dot = (-y[idx - 1] + model.gain * plant_u) / max(model.time_constant_s, dt)
        y[idx] = y[idx - 1] + y_dot * dt
        delayed_u[idx] = u[idx]
        e_prev = error

    return _compute_metrics(y, u, dt)


def _compute_metrics(response: np.ndarray, control: np.ndarray, dt: float) -> SimulationMetrics:
    final_value = float(response[-1])
    target = 1.0
    duration_s = len(response) * dt
    if final_value == 0.0:
        rise_time = duration_s
    else:
        rise_candidates = np.where(response >= 0.9 * target)[0]
        rise_time = float(rise_candidates[0] * dt) if len(rise_candidates) else duration_s

    settling_candidates = np.where(np.abs(response - target) <= 0.02)[0]
    settling_time = float(settling_candidates[0] * dt) if len(settling_candidates) else duration_s
    overshoot_pct = float(max(0.0, (response.max() - target) / target * 100.0))
    steady_state_error = float(abs(target - final_value))
    control_effort_rms = float(np.sqrt(np.mean(control ** 2)))
    peak_control = float(np.max(np.abs(control)))
    stable = bool(np.all(np.isfinite(response)) and response.max() < 3.0 and response.min() > -1.5)
    performance_score = _performance_score(
        rise_time=rise_time,
        settling_time=settling_time,
        overshoot_pct=overshoot_pct,
        steady_state_error=steady_state_error,
        control_effort_rms=control_effort_rms,
        peak_control=peak_control,
        stable=stable,
    )

    return SimulationMetrics(
        rise_time_s=rise_time,
        settling_time_s=settling_time,
        overshoot_pct=overshoot_pct,
        steady_state_error=steady_state_error,
        control_effort_rms=control_effort_rms,
        peak_control=peak_control,
        performance_score=performance_score,
        stable=stable,
    )


def _performance_score(
    rise_time: float,
    settling_time: float,
    overshoot_pct: float,
    steady_state_error: float,
    control_effort_rms: float,
    peak_control: float,
    stable: bool,
) -> float:
    score = 100.0
    if not stable:
        score -= 60.0
    score -= min(rise_time, 10.0) * 8.0
    score -= min(settling_time, 10.0) * 6.0
    score -= overshoot_pct * 0.8
    score -= steady_state_error * 45.0
    score -= control_effort_rms * 2.5
    score -= max(0.0, peak_control - 4.0) * 10.0
    return float(max(score, 0.0))
