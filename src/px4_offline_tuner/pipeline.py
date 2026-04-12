from __future__ import annotations

from pathlib import Path

import pandas as pd

from .frequency import analyze_frequency
from .identification import identify_system
from .log_loader import load_log
from .models import AxisDataset, AxisReport, FrequencyMetrics, IdentifiedModel, RunReport
from .preprocessing import build_axis_dataset
from .reporting import write_run_report
from .selection import best_recommendation
from .simulation import simulate_closed_loop
from .tuning import generate_pid_recommendations


class PX4OfflineTuner:
    def __init__(self, target_rate_hz: float = 200.0) -> None:
        self.target_rate_hz = target_rate_hz

    def run(self, input_path: str | Path, output_dir: str | Path) -> RunReport:
        return self.run_many([input_path], output_dir)

    def run_many(self, input_paths: list[str | Path], output_dir: str | Path) -> RunReport:
        normalized_paths = [Path(path) for path in input_paths]
        if not normalized_paths:
            raise ValueError("At least one input log is required.")

        axis_dataset_groups: dict[str, list[AxisDataset]] = {"roll": [], "pitch": [], "yaw": []}
        for input_path in normalized_paths:
            frame = load_log(input_path)
            for axis in ["roll", "pitch", "yaw"]:
                try:
                    dataset = build_axis_dataset(frame, axis, target_rate_hz=self.target_rate_hz)
                except ValueError:
                    continue
                axis_dataset_groups[axis].append(dataset)

        output_dir = Path(output_dir)
        axis_reports: list[AxisReport] = []
        for axis in ["roll", "pitch", "yaw"]:
            datasets = axis_dataset_groups[axis]
            if not datasets:
                continue

            dataset = _merge_axis_datasets(datasets)
            frequency, model = _aggregate_axis_analysis(datasets)
            recommendations = generate_pid_recommendations(model, frequency)
            simulations = {
                item.preset: simulate_closed_loop(model, item, sample_rate_hz=dataset.sample_rate_hz)
                for item in recommendations
            }

            axis_reports.append(
                AxisReport(
                    axis=axis,
                    dataset=dataset,
                    frequency=frequency,
                    model=model,
                    recommendations=recommendations,
                    simulations=simulations,
                    output_dir=output_dir / axis,
                )
            )

        if not axis_reports:
            raise ValueError("No valid roll/pitch/yaw samples were found in the input logs.")

        summary = _build_summary(axis_reports)
        report = RunReport(
            input_path=normalized_paths[0],
            input_paths=normalized_paths,
            output_dir=output_dir,
            axis_reports=axis_reports,
            summary=summary,
        )
        write_run_report(report)
        return report


def _build_summary(axis_reports: list[AxisReport]) -> list[str]:
    lines: list[str] = []
    for item in axis_reports:
        best = best_recommendation(item)
        best_sim = item.simulations[best.preset]
        lines.append(
            f"{item.axis.title()} best preset is '{best.preset}' "
            f"(quality={item.dataset.quality_score:.2f}, fit={item.model.fit_score:.2f}, score={best_sim.performance_score:.1f})."
        )
    return lines


def _merge_axis_datasets(datasets: list[AxisDataset]) -> AxisDataset:
    merged_frames: list[pd.DataFrame] = []
    quality_notes: list[str] = []
    timestamp_offset = 0.0

    for idx, dataset in enumerate(datasets):
        frame = dataset.data.copy()
        frame["timestamp_s"] = frame["timestamp_s"] - float(frame["timestamp_s"].iloc[0]) + timestamp_offset
        frame["source_index"] = idx
        timestamp_offset = float(frame["timestamp_s"].iloc[-1]) + (1.0 / dataset.sample_rate_hz)
        merged_frames.append(frame)
        quality_notes.extend(dataset.quality_notes)

    merged = pd.concat(merged_frames, ignore_index=True)
    mean_quality = sum(item.quality_score for item in datasets) / len(datasets)
    unique_notes = list(dict.fromkeys(quality_notes))
    unique_notes.append(f"Joint analysis combines {len(datasets)} logs for this axis.")
    return AxisDataset(
        axis=datasets[0].axis,
        data=merged,
        sample_rate_hz=datasets[0].sample_rate_hz,
        quality_score=mean_quality,
        quality_notes=unique_notes,
    )


def _aggregate_axis_analysis(datasets: list[AxisDataset]) -> tuple[FrequencyMetrics, IdentifiedModel]:
    frequencies: list[FrequencyMetrics] = []
    models: list[IdentifiedModel] = []
    weights: list[float] = []
    for dataset in datasets:
        frequency = analyze_frequency(dataset)
        model = identify_system(dataset, frequency)
        weight = max(dataset.quality_score, 0.2) * max(model.fit_score, 0.2)
        frequencies.append(frequency)
        models.append(model)
        weights.append(weight)

    total_weight = sum(weights) or float(len(weights))
    normalized_weights = [weight / total_weight for weight in weights]

    aggregate_frequency = FrequencyMetrics(
        dominant_frequency_hz=sum(freq.dominant_frequency_hz * weight for freq, weight in zip(frequencies, normalized_weights, strict=False)),
        noise_frequency_hz=sum(freq.noise_frequency_hz * weight for freq, weight in zip(frequencies, normalized_weights, strict=False)),
        bandwidth_estimate_hz=sum(freq.bandwidth_estimate_hz * weight for freq, weight in zip(frequencies, normalized_weights, strict=False)),
        rms_error=sum(freq.rms_error * weight for freq, weight in zip(frequencies, normalized_weights, strict=False)),
        latency_s=sum(freq.latency_s * weight for freq, weight in zip(frequencies, normalized_weights, strict=False)),
        diagnosis=_merge_notes([freq.diagnosis for freq in frequencies]),
    )

    gains = [model.gain for model in models]
    taus = [model.time_constant_s for model in models]
    delays = [model.dead_time_s for model in models]
    fit_scores = [model.fit_score for model in models]
    aggregate_model = IdentifiedModel(
        gain=sum(value * weight for value, weight in zip(gains, normalized_weights, strict=False)),
        time_constant_s=sum(value * weight for value, weight in zip(taus, normalized_weights, strict=False)),
        dead_time_s=sum(value * weight for value, weight in zip(delays, normalized_weights, strict=False)),
        fit_score=sum(value * weight for value, weight in zip(fit_scores, normalized_weights, strict=False)),
        damping_ratio=sum(model.damping_ratio * weight for model, weight in zip(models, normalized_weights, strict=False)),
        notes=_merge_notes([model.notes for model in models]) + [_consistency_note(gains, taus, delays)],
    )
    return aggregate_frequency, aggregate_model


def _merge_notes(note_groups: list[list[str]]) -> list[str]:
    merged: list[str] = []
    for group in note_groups:
        for note in group:
            if note not in merged:
                merged.append(note)
    return merged


def _consistency_note(gains: list[float], taus: list[float], delays: list[float]) -> str:
    if len(gains) <= 1:
        return "Single-log identification used for this axis."
    gain_spread = _relative_spread(gains)
    tau_spread = _relative_spread(taus)
    delay_spread = _relative_spread(delays)
    score = max(0.0, 1.0 - (gain_spread + tau_spread + delay_spread) / 3.0)
    return f"Cross-log consistency score is {score:.2f}; lower values indicate more variation between flights."


def _relative_spread(values: list[float]) -> float:
    if not values:
        return 0.0
    mean_value = sum(values) / len(values)
    if abs(mean_value) < 1e-6:
        return 0.0
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return min((variance ** 0.5) / abs(mean_value), 1.0)
