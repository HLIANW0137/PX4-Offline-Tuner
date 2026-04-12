from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .io_utils import atomic_write_text
from .models import AxisDataset, AxisReport, RunReport


def save_axis_dataset(axis_report: AxisReport) -> Path:
    axis_dir = axis_report.output_dir
    axis_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = axis_dir / f"{axis_report.axis}_dataset.csv"
    csv_text = axis_report.dataset.data.to_csv(index=False)
    atomic_write_text(dataset_path, csv_text)
    return dataset_path


def load_run_report(output_dir: str | Path) -> RunReport:
    output_dir = Path(output_dir)
    report_path = output_dir / "report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    axis_reports: list[AxisReport] = []
    for axis_payload in payload["axis_reports"]:
        axis = axis_payload["axis"]
        dataset_path = output_dir / axis / f"{axis}_dataset.csv"
        data = pd.read_csv(dataset_path)
        numeric_columns = data.select_dtypes(include=["float64", "int64"]).columns
        if len(numeric_columns):
            data[numeric_columns] = data[numeric_columns].astype("float32")
        dataset = AxisDataset.from_dict(axis_payload["dataset"], data=data)
        axis_reports.append(AxisReport.from_dict(axis_payload, dataset))

    return RunReport.from_dict(payload, axis_reports)
