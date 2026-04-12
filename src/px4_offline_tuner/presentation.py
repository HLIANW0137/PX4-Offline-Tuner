from __future__ import annotations

from pathlib import Path

import pandas as pd

from .models import AxisReport, PIDRecommendation, RunReport
from .selection import best_recommendation, recommendation_rank


PX4_RATE_PARAM_MAP = {
    "roll": ("MC_ROLLRATE_P", "MC_ROLLRATE_I", "MC_ROLLRATE_D"),
    "pitch": ("MC_PITCHRATE_P", "MC_PITCHRATE_I", "MC_PITCHRATE_D"),
    "yaw": ("MC_YAWRATE_P", "MC_YAWRATE_I", "MC_YAWRATE_D"),
}
def build_overview_table(report: RunReport) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for axis_report in report.axis_reports:
        best = best_recommendation(axis_report)
        sim = axis_report.simulations[best.preset]
        rows.append(
            {
                "axis": axis_report.axis,
                "quality_score": round(axis_report.dataset.quality_score, 3),
                "fit_score": round(axis_report.model.fit_score, 3),
                "bandwidth_hz": round(axis_report.frequency.bandwidth_estimate_hz, 3),
                "latency_s": round(axis_report.frequency.latency_s, 4),
                "best_preset": best.preset,
                "overshoot_pct": round(sim.overshoot_pct, 3),
                "rise_time_s": round(sim.rise_time_s, 3),
                "settling_time_s": round(sim.settling_time_s, 3),
                "performance_score": round(sim.performance_score, 2),
                "stable": sim.stable,
            }
        )
    return pd.DataFrame(rows)


def build_recommendation_table(axis_report: AxisReport) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for recommendation in axis_report.recommendations:
        sim = axis_report.simulations[recommendation.preset]
        rows.append(
            {
                "preset": recommendation.preset,
                "kp": recommendation.kp,
                "ki": recommendation.ki,
                "kd": recommendation.kd,
                "risk": recommendation.risk,
                "rise_time_s": round(sim.rise_time_s, 3),
                "settling_time_s": round(sim.settling_time_s, 3),
                "overshoot_pct": round(sim.overshoot_pct, 3),
                "steady_state_error": round(sim.steady_state_error, 4),
                "control_effort_rms": round(sim.control_effort_rms, 3),
                "peak_control": round(sim.peak_control, 3),
                "performance_score": round(sim.performance_score, 2),
                "stable": sim.stable,
            }
        )
    return pd.DataFrame(rows)


def build_ranked_recommendation_table(axis_report: AxisReport) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rank, (recommendation, simulation, cost) in enumerate(recommendation_rank(axis_report), start=1):
        rows.append(
            {
                "rank": rank,
                "preset": recommendation.preset,
                "cost": round(cost, 3),
                "performance_score": round(simulation.performance_score, 2),
                "stable": simulation.stable,
            }
        )
    return pd.DataFrame(rows)


def build_px4_param_text(report: RunReport, preset: str) -> str:
    lines = [
        "# PX4 Offline Tuner parameter export",
        f"# Primary input: {report.input_path}",
        f"# Input count: {len(report.input_paths)}",
        f"# Preset: {preset}",
        "",
    ]
    for axis_report in report.axis_reports:
        recommendation = _find_preset(axis_report, preset)
        if recommendation is None:
            continue
        p_name, i_name, d_name = PX4_RATE_PARAM_MAP[axis_report.axis]
        lines.extend(
            [
                f"{p_name}\t{recommendation.kp}",
                f"{i_name}\t{recommendation.ki}",
                f"{d_name}\t{recommendation.kd}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def load_report_artifacts(report: RunReport) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    json_path = report.output_dir / "report.json"
    markdown_path = report.output_dir / "report.md"
    if json_path.exists():
        artifacts["json"] = json_path.read_text(encoding="utf-8")
    if markdown_path.exists():
        artifacts["markdown"] = markdown_path.read_text(encoding="utf-8")
    return artifacts


def available_sample_logs(root: Path) -> list[Path]:
    sample_dir = root / "sample_data"
    if not sample_dir.exists():
        return []
    return sorted(
        [path for path in sample_dir.iterdir() if path.suffix.lower() in {".csv", ".ulg"}],
        key=lambda path: path.name.lower(),
    )


def _find_preset(axis_report: AxisReport, preset: str) -> PIDRecommendation | None:
    for recommendation in axis_report.recommendations:
        if recommendation.preset == preset:
            return recommendation
    return None
