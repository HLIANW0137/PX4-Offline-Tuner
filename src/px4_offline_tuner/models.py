from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(slots=True)
class AxisDataset:
    axis: str
    data: pd.DataFrame
    sample_rate_hz: float
    quality_score: float
    quality_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        preview = self.data.head(20).round(6).to_dict(orient="records")
        return {
            "axis": self.axis,
            "sample_rate_hz": self.sample_rate_hz,
            "quality_score": self.quality_score,
            "quality_notes": self.quality_notes,
            "sample_count": int(len(self.data)),
            "data_preview": preview,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any], data: pd.DataFrame) -> "AxisDataset":
        return cls(
            axis=str(payload["axis"]),
            data=data,
            sample_rate_hz=float(payload["sample_rate_hz"]),
            quality_score=float(payload["quality_score"]),
            quality_notes=list(payload["quality_notes"]),
        )


@dataclass(slots=True)
class FrequencyMetrics:
    dominant_frequency_hz: float
    noise_frequency_hz: float
    bandwidth_estimate_hz: float
    rms_error: float
    latency_s: float
    diagnosis: list[str]


@dataclass(slots=True)
class IdentifiedModel:
    gain: float
    time_constant_s: float
    dead_time_s: float
    fit_score: float
    damping_ratio: float
    notes: list[str]


@dataclass(slots=True)
class PIDRecommendation:
    preset: str
    kp: float
    ki: float
    kd: float
    risk: str
    rationale: list[str]


@dataclass(slots=True)
class SimulationMetrics:
    rise_time_s: float
    settling_time_s: float
    overshoot_pct: float
    steady_state_error: float
    control_effort_rms: float
    peak_control: float
    performance_score: float
    stable: bool


@dataclass(slots=True)
class AxisReport:
    axis: str
    dataset: AxisDataset
    frequency: FrequencyMetrics
    model: IdentifiedModel
    recommendations: list[PIDRecommendation]
    simulations: dict[str, SimulationMetrics]
    output_dir: Path
    figures: dict[str, Path] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis": self.axis,
            "dataset": self.dataset.to_dict(),
            "frequency": asdict(self.frequency),
            "model": asdict(self.model),
            "recommendations": [asdict(item) for item in self.recommendations],
            "simulations": {key: asdict(value) for key, value in self.simulations.items()},
            "output_dir": str(self.output_dir),
            "figures": {key: str(value) for key, value in self.figures.items()},
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any], dataset: AxisDataset) -> "AxisReport":
        return cls(
            axis=str(payload["axis"]),
            dataset=dataset,
            frequency=FrequencyMetrics(**payload["frequency"]),
            model=IdentifiedModel(**payload["model"]),
            recommendations=[PIDRecommendation(**item) for item in payload["recommendations"]],
            simulations={key: SimulationMetrics(**value) for key, value in payload["simulations"].items()},
            output_dir=Path(payload["output_dir"]),
            figures={key: Path(value) for key, value in payload.get("figures", {}).items()},
        )


@dataclass(slots=True)
class RunReport:
    input_path: Path
    input_paths: list[Path]
    output_dir: Path
    axis_reports: list[AxisReport]
    summary: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_path": str(self.input_path),
            "input_paths": [str(path) for path in self.input_paths],
            "output_dir": str(self.output_dir),
            "axis_reports": [item.to_dict() for item in self.axis_reports],
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any], axis_reports: list[AxisReport]) -> "RunReport":
        input_paths_raw = payload.get("input_paths") or [payload["input_path"]]
        return cls(
            input_path=Path(payload["input_path"]),
            input_paths=[Path(path) for path in input_paths_raw],
            output_dir=Path(payload["output_dir"]),
            axis_reports=axis_reports,
            summary=list(payload["summary"]),
        )
