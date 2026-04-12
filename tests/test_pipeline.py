from pathlib import Path

import pandas as pd

from px4_offline_tuner.persistence import load_run_report
from px4_offline_tuner.pipeline import PX4OfflineTuner


def test_pipeline_generates_report(tmp_path: Path) -> None:
    input_path = Path("sample_data/demo_log.csv")
    output_dir = tmp_path / "report"

    report = PX4OfflineTuner(target_rate_hz=50.0).run(input_path, output_dir)

    assert report.axis_reports
    assert (output_dir / "report.json").exists()
    assert (output_dir / "report.md").exists()

    roll_report = next(item for item in report.axis_reports if item.axis == "roll")
    presets = {item.preset for item in roll_report.recommendations}
    assert presets == {"conservative", "balanced", "aggressive"}


def test_pipeline_can_merge_multiple_logs(tmp_path: Path) -> None:
    input_path = Path("sample_data/demo_log.csv")
    second_input = tmp_path / "demo_log_2.csv"
    frame = pd.read_csv(input_path)
    frame["rate"] = frame["rate"] * 0.97
    frame.to_csv(second_input, index=False)

    output_dir = tmp_path / "multi_report"
    report = PX4OfflineTuner(target_rate_hz=50.0).run_many([input_path, second_input], output_dir)

    assert len(report.input_paths) == 2
    assert report.axis_reports
    assert any("Joint analysis combines 2 logs" in note for note in report.axis_reports[0].dataset.quality_notes)


def test_persisted_report_can_be_reloaded(tmp_path: Path) -> None:
    output_dir = tmp_path / "persisted_report"
    PX4OfflineTuner(target_rate_hz=50.0).run(Path("sample_data/demo_log.csv"), output_dir)
    reloaded = load_run_report(output_dir)

    assert reloaded.axis_reports
    assert reloaded.input_paths
