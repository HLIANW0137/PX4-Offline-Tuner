from pathlib import Path

import pandas as pd

from px4_offline_tuner.frequency import compute_power_spectrum
from px4_offline_tuner.pipeline import PX4OfflineTuner
from px4_offline_tuner.presentation import build_overview_table, build_px4_param_text


def test_px4_export_contains_rate_params(tmp_path: Path) -> None:
    report = PX4OfflineTuner(target_rate_hz=50.0).run(Path("sample_data/demo_log.csv"), tmp_path / "report")
    export_text = build_px4_param_text(report, "balanced")

    assert "MC_ROLLRATE_P" in export_text
    assert "MC_PITCHRATE_I" in export_text
    assert "MC_YAWRATE_D" in export_text


def test_overview_table_has_axis_rows(tmp_path: Path) -> None:
    report = PX4OfflineTuner(target_rate_hz=50.0).run(Path("sample_data/demo_log.csv"), tmp_path / "report")
    overview = build_overview_table(report)

    assert set(overview["axis"]) == {"roll", "pitch", "yaw"}
    assert "best_preset" in overview.columns
    assert "performance_score" in overview.columns


def test_power_spectrum_accepts_pandas_series() -> None:
    signal = pd.Series([0.0, 1.0, 0.5, -0.25, 0.0, 0.3, -0.1, 0.0, 0.2, -0.05])
    freqs, power = compute_power_spectrum(signal, 50.0)

    assert len(freqs) == len(power)
    assert len(freqs) > 0
