from __future__ import annotations

import numpy as np
from scipy.signal import welch

from .models import AxisDataset, FrequencyMetrics


def analyze_frequency(dataset: AxisDataset) -> FrequencyMetrics:
    rate = dataset.data["rate"].to_numpy()
    setpoint = dataset.data["rate_setpoint"].to_numpy()
    error = dataset.data["tracking_error"].to_numpy()
    sample_rate = dataset.sample_rate_hz

    freqs, pxx = compute_power_spectrum(rate, sample_rate)
    err_freqs, err_pxx = compute_power_spectrum(error, sample_rate)

    dominant_frequency_hz = float(freqs[np.argmax(pxx[1:]) + 1]) if len(freqs) > 1 else 0.0
    noise_frequency_hz = float(err_freqs[np.argmax(err_pxx[1:]) + 1]) if len(err_freqs) > 1 else 0.0

    power_cumsum = np.cumsum(pxx)
    total_power = float(power_cumsum[-1]) if len(power_cumsum) else 0.0
    if total_power > 0.0:
        bandwidth_idx = int(np.searchsorted(power_cumsum, total_power * 0.9))
        bandwidth_estimate_hz = float(freqs[min(bandwidth_idx, len(freqs) - 1)])
    else:
        bandwidth_estimate_hz = 0.0

    rms_error = float(np.sqrt(np.mean(error ** 2)))
    latency_s = _estimate_latency_s(setpoint, rate, sample_rate)

    diagnosis: list[str] = []
    if bandwidth_estimate_hz < 3.0:
        diagnosis.append("Bandwidth looks low; the loop is likely too conservative.")
    if noise_frequency_hz > max(1.0, bandwidth_estimate_hz * 1.5):
        diagnosis.append("High-frequency tracking noise is visible; derivative action or filtering may need care.")
    if rms_error > max(0.1, np.std(setpoint) * 0.4):
        diagnosis.append("Tracking RMS error is elevated; consider more authority in the balanced preset.")
    if latency_s > 0.05:
        diagnosis.append("Estimated delay is meaningful; aggressive tuning may reduce robustness.")
    if not diagnosis:
        diagnosis.append("Frequency response looks healthy for automated offline tuning.")

    return FrequencyMetrics(
        dominant_frequency_hz=dominant_frequency_hz,
        noise_frequency_hz=noise_frequency_hz,
        bandwidth_estimate_hz=bandwidth_estimate_hz,
        rms_error=rms_error,
        latency_s=latency_s,
        diagnosis=diagnosis,
    )


def compute_power_spectrum(signal: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(signal, dtype=float)
    if array.ndim != 1:
        array = np.ravel(array)
    if len(array) < 8:
        freqs = np.linspace(0.0, sample_rate / 2.0, num=max(2, len(array)))
        power = np.zeros_like(freqs)
        return freqs, power
    freqs, power = welch(array, fs=sample_rate, nperseg=min(1024, len(array)))
    return freqs, power


def _estimate_latency_s(setpoint: np.ndarray, rate: np.ndarray, sample_rate: float) -> float:
    centered_sp = setpoint - np.mean(setpoint)
    centered_rate = rate - np.mean(rate)
    corr = np.correlate(centered_rate, centered_sp, mode="full")
    lag_index = int(np.argmax(corr) - (len(setpoint) - 1))
    lag_index = max(0, lag_index)
    return float(lag_index / sample_rate)
