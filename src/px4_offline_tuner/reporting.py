from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go

from .io_utils import atomic_write_json, atomic_write_text
from .models import AxisReport, RunReport
from .persistence import save_axis_dataset


def write_axis_artifacts(axis_report: AxisReport) -> None:
    axis_dir = axis_report.output_dir
    axis_dir.mkdir(parents=True, exist_ok=True)
    frame = axis_report.dataset.data
    save_axis_dataset(axis_report)

    tracking_fig = go.Figure()
    tracking_fig.add_scatter(x=frame["timestamp_s"], y=frame["rate_setpoint"], name="rate_setpoint")
    tracking_fig.add_scatter(x=frame["timestamp_s"], y=frame["rate"], name="rate")
    tracking_path = axis_dir / f"{axis_report.axis}_tracking.html"
    tracking_fig.write_html(tracking_path, include_plotlyjs="cdn")
    axis_report.figures["tracking"] = tracking_path

    control_fig = go.Figure()
    control_fig.add_scatter(x=frame["timestamp_s"], y=frame["control_output"], name="control_output")
    control_path = axis_dir / f"{axis_report.axis}_control.html"
    control_fig.write_html(control_path, include_plotlyjs="cdn")
    axis_report.figures["control"] = control_path


def write_run_report(report: RunReport) -> None:
    report.output_dir.mkdir(parents=True, exist_ok=True)

    for axis_report in report.axis_reports:
        write_axis_artifacts(axis_report)

    json_path = report.output_dir / "report.json"
    atomic_write_json(json_path, report.to_dict())

    markdown_path = report.output_dir / "report.md"
    atomic_write_text(markdown_path, _render_markdown(report), encoding="utf-8")


def _render_markdown(report: RunReport) -> str:
    lines = [
        "# PX4 Offline Tuner Report",
        "",
        f"- Primary input: `{report.input_path}`",
        f"- Input count: `{len(report.input_paths)}`",
        f"- Output: `{report.output_dir}`",
        "",
        "## Summary",
    ]
    if len(report.input_paths) > 1:
        lines.extend(["", "## Input Logs"])
        lines.extend([f"- `{path}`" for path in report.input_paths])
    lines.extend([f"- {line}" for line in report.summary])

    for axis in report.axis_reports:
        lines.extend(
            [
                "",
                f"## Axis: {axis.axis}",
                "",
                f"- Quality score: `{axis.dataset.quality_score:.2f}`",
                f"- Dominant frequency: `{axis.frequency.dominant_frequency_hz:.2f} Hz`",
                f"- Noise frequency: `{axis.frequency.noise_frequency_hz:.2f} Hz`",
                f"- Estimated bandwidth: `{axis.frequency.bandwidth_estimate_hz:.2f} Hz`",
                f"- Estimated delay: `{axis.frequency.latency_s:.4f} s`",
                f"- Model gain: `{axis.model.gain:.3f}`",
                f"- Model time constant: `{axis.model.time_constant_s:.4f} s`",
                f"- Model dead time: `{axis.model.dead_time_s:.4f} s`",
                f"- Model fit score: `{axis.model.fit_score:.2f}`",
                "",
                "### Diagnostics",
            ]
        )
        lines.extend([f"- {note}" for note in axis.dataset.quality_notes])
        lines.extend([f"- {note}" for note in axis.frequency.diagnosis])
        lines.extend([f"- {note}" for note in axis.model.notes])
        lines.extend(["", "### Recommendations"])

        for recommendation in axis.recommendations:
            sim = axis.simulations[recommendation.preset]
            lines.extend(
                [
                    f"- `{recommendation.preset}`: Kp={recommendation.kp}, Ki={recommendation.ki}, Kd={recommendation.kd}, risk={recommendation.risk}",
                    f"  - Simulated rise={sim.rise_time_s:.3f}s, settle={sim.settling_time_s:.3f}s, overshoot={sim.overshoot_pct:.2f}%, score={sim.performance_score:.2f}, stable={sim.stable}",
                ]
            )
            lines.extend([f"  - {item}" for item in recommendation.rationale])

    return "\n".join(lines) + "\n"
