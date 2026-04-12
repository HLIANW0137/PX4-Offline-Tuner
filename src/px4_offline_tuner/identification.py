from __future__ import annotations

import numpy as np

from .models import AxisDataset, FrequencyMetrics, IdentifiedModel


def identify_system(dataset: AxisDataset, frequency: FrequencyMetrics) -> IdentifiedModel:
    data = dataset.data
    control = data["control_output"].to_numpy()
    rate = data["rate"].to_numpy()
    setpoint = data["rate_setpoint"].to_numpy()
    time_s = data["timestamp_s"].to_numpy()
    sample_rate = dataset.sample_rate_hz

    notes: list[str] = []
    gain, time_constant_s, dead_time_s, predicted = _fit_fopdt(control, rate, sample_rate, frequency.latency_s)
    gain = _safe_clip(gain, 0.05, 20.0, fallback=1.0)
    time_constant_s = _safe_clip(time_constant_s, 0.02, 1.5, fallback=0.12)
    dead_time_s = _safe_clip(dead_time_s, 0.0, 0.2, fallback=0.01)

    step_idx = int(np.argmax(np.abs(np.diff(setpoint, prepend=setpoint[0]))))
    pre_value = float(np.mean(rate[max(0, step_idx - 10) : step_idx + 1]))
    post_window = rate[min(len(rate) - 1, step_idx + 10) :]
    post_value = float(np.mean(post_window[-max(10, int(sample_rate * 0.2)) :])) if len(post_window) else float(rate[-1])
    damping_ratio = _estimate_damping(rate, post_value)

    residual = rate - predicted
    denom = float(np.var(rate))
    fit_score = float(max(0.0, 1.0 - np.var(residual) / denom)) if denom > 1e-8 else 0.0

    if dead_time_s > time_constant_s * 0.8:
        notes.append("Estimated delay is large relative to plant time constant; robustness margin is limited.")
    if abs(np.mean(predicted - rate)) > max(0.05, np.std(rate) * 0.15):
        notes.append("Model bias is noticeable; the recommendation engine will lean conservative.")
    if fit_score < 0.45:
        notes.append("Model fit is modest; use conservative or balanced recommendations first.")
    else:
        notes.append("Model fit is acceptable for offline comparative tuning.")

    return IdentifiedModel(
        gain=gain,
        time_constant_s=time_constant_s,
        dead_time_s=dead_time_s,
        fit_score=fit_score,
        damping_ratio=damping_ratio,
        notes=notes,
    )


def _fit_fopdt(control: np.ndarray, rate: np.ndarray, sample_rate: float, latency_hint_s: float) -> tuple[float, float, float, np.ndarray]:
    if len(control) < 8 or np.std(control) < 1e-8:
        predicted = np.zeros_like(rate, dtype=float)
        return 1.0, 0.12, max(latency_hint_s, 0.01), predicted

    dt = 1.0 / sample_rate
    max_delay_s = float(min(0.2, max(0.02, latency_hint_s * 2.5 + 0.02)))
    delay_candidates = np.arange(0.0, max_delay_s + dt, dt)
    tau_candidates = np.geomspace(0.02, 1.5, num=32)

    best_error = float("inf")
    best_gain = 1.0
    best_tau = 0.12
    best_delay = max(latency_hint_s, 0.01)
    best_prediction = np.zeros_like(rate, dtype=float)

    centered_rate = rate - np.mean(rate)
    for delay_s in delay_candidates:
        for tau_s in tau_candidates:
            base_response = _simulate_fopdt(control, sample_rate, 1.0, float(tau_s), float(delay_s))
            denom = float(np.dot(base_response, base_response))
            if denom < 1e-8:
                continue
            gain = float(np.dot(base_response, centered_rate) / denom)
            gain = float(np.clip(gain, 0.02, 25.0))
            predicted = _simulate_fopdt(control, sample_rate, gain, float(tau_s), float(delay_s))
            error = float(np.mean((rate - predicted) ** 2))
            if error < best_error:
                best_error = error
                best_gain = gain
                best_tau = float(tau_s)
                best_delay = float(delay_s)
                best_prediction = predicted

    return best_gain, best_tau, best_delay, best_prediction


def _estimate_time_constant(rate: np.ndarray, time_s: np.ndarray, step_idx: int, target: float) -> float:
    tail = rate[step_idx:]
    if not len(tail):
        return 0.12
    idx_candidates = np.where((tail - target) >= 0 if tail[-1] >= tail[0] else (tail - target) <= 0)[0]
    if not len(idx_candidates):
        return 0.12
    idx = step_idx + int(idx_candidates[0])
    return float(max(time_s[idx] - time_s[step_idx], 0.02))


def _estimate_damping(rate: np.ndarray, final_value: float) -> float:
    peak = float(np.max(rate))
    if abs(final_value) < 1e-6 or peak <= final_value:
        return 0.9
    overshoot = max((peak - final_value) / max(abs(final_value), 1e-6), 1e-6)
    log_dec = np.log(overshoot)
    return float(abs(log_dec) / np.sqrt(np.pi ** 2 + log_dec ** 2))


def _simulate_fopdt(control: np.ndarray, sample_rate: float, gain: float, tau: float, delay: float) -> np.ndarray:
    dt = 1.0 / sample_rate
    delay_steps = int(delay / dt)
    delayed_control = np.concatenate([np.full(delay_steps, control[0]), control[:-delay_steps] if delay_steps else control])
    output = np.zeros_like(control, dtype=float)
    alpha = dt / max(tau, dt)
    for idx in range(1, len(control)):
        output[idx] = output[idx - 1] + alpha * (gain * delayed_control[idx] - output[idx - 1])
    return output


def _safe_clip(value: float, lower: float, upper: float, fallback: float) -> float:
    if np.isnan(value) or np.isinf(value):
        return fallback
    return float(np.clip(value, lower, upper))
