from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

from .models import AxisDataset


def build_axis_dataset(frame: pd.DataFrame, axis: str, target_rate_hz: float = 200.0) -> AxisDataset:
    axis_frame = frame.loc[frame["axis"] == axis].copy()
    if axis_frame.empty:
        raise ValueError(f"No samples were found for axis '{axis}'.")

    axis_frame = axis_frame.sort_values("timestamp_s").dropna()
    axis_frame = axis_frame.drop_duplicates(subset="timestamp_s")

    start = float(axis_frame["timestamp_s"].min())
    stop = float(axis_frame["timestamp_s"].max())
    if stop <= start:
        raise ValueError(f"Axis '{axis}' has invalid timestamps.")

    timeline = np.arange(start, stop, 1.0 / target_rate_hz)
    resampled = pd.DataFrame({"timestamp_s": timeline})

    for column in ["rate_setpoint", "rate", "control_output"]:
        resampled[column] = np.interp(timeline, axis_frame["timestamp_s"], axis_frame[column])

    cutoff_hz = min(target_rate_hz * 0.35, 40.0)
    if cutoff_hz > 2.0:
        b, a = butter(2, cutoff_hz / (target_rate_hz / 2.0), btype="low")
        for column in ["rate_setpoint", "rate", "control_output"]:
            resampled[column] = filtfilt(b, a, resampled[column])

    resampled["tracking_error"] = resampled["rate_setpoint"] - resampled["rate"]
    resampled["setpoint_step"] = resampled["rate_setpoint"].diff().fillna(0.0)

    quality_notes: list[str] = []
    excitation = float(resampled["setpoint_step"].abs().mean())
    noise = float(resampled["tracking_error"].std())
    command_span = float(resampled["control_output"].max() - resampled["control_output"].min())
    duration_s = float(resampled["timestamp_s"].iloc[-1] - resampled["timestamp_s"].iloc[0])
    saturation_ratio = float((resampled["control_output"].abs() >= 0.95).mean())
    tracking_std = float(resampled["rate"].std())
    quality_score = 1.0

    if excitation < 0.01:
        quality_score -= 0.35
        quality_notes.append("Setpoint excitation is weak; identification confidence will be limited.")
    elif excitation > 0.05:
        quality_notes.append("Setpoint excitation is rich enough for useful offline identification.")
    if command_span < 0.1:
        quality_score -= 0.2
        quality_notes.append("Control output span is narrow; the log may not be rich enough for robust tuning.")
    if duration_s < 1.0:
        quality_score -= 0.2
        quality_notes.append("Effective axis duration is short; the tuning result may be overly sensitive to noise.")
    if noise > max(0.05, excitation * 10.0):
        quality_score -= 0.15
        quality_notes.append("Tracking error is noisy; derivative recommendations should be treated carefully.")
    if saturation_ratio > 0.15:
        quality_score -= 0.1
        quality_notes.append("Actuator command saturation is noticeable; aggressive recommendations may not transfer well.")
    if tracking_std < 0.03:
        quality_score -= 0.1
        quality_notes.append("Measured rate variation is limited; the log may under-excite the actual dynamics.")
    if not quality_notes:
        quality_notes.append("Signal quality looks suitable for offline rate-loop tuning.")

    quality_score = max(0.0, min(1.0, quality_score))

    return AxisDataset(
        axis=axis,
        data=resampled,
        sample_rate_hz=target_rate_hz,
        quality_score=quality_score,
        quality_notes=quality_notes,
    )
