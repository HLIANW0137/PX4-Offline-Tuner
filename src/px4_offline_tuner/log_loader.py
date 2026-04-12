from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation


REQUIRED_COLUMNS = {
    "timestamp_s",
    "axis",
    "rate_setpoint",
    "rate",
    "control_output",
}


def load_log(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _load_csv(path)
    if suffix == ".ulg":
        return _load_ulog(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def _load_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"CSV is missing required columns: {missing_text}")
    frame["axis"] = frame["axis"].str.lower()
    return frame


def _load_ulog(path: Path) -> pd.DataFrame:
    try:
        from pyulog import ULog
    except ImportError as exc:
        raise RuntimeError("ULog support requires pyulog to be installed.") from exc

    ulog = ULog(str(path))
    datasets = _group_datasets(ulog)

    rates_df = _extract_vehicle_angular_velocity(datasets)
    setpoint_df = _extract_rate_setpoints(datasets)
    actuator_df = _extract_actuator_controls(datasets)
    attitude_df = _extract_attitude(datasets)
    attitude_sp_df = _extract_attitude_setpoint(datasets)
    battery_df = _extract_battery(datasets)

    merged = rates_df.sort_values("timestamp_us")
    for frame in [setpoint_df, actuator_df, attitude_df, attitude_sp_df, battery_df]:
        if frame is not None:
            merged = pd.merge_asof(
                merged.sort_values("timestamp_us"),
                frame.sort_values("timestamp_us"),
                on="timestamp_us",
                direction="nearest",
                tolerance=25_000,
            )

    if not {"roll_rate", "pitch_rate", "yaw_rate"}.issubset(merged.columns):
        raise ValueError("ULog does not contain a usable vehicle_angular_velocity topic.")
    if not {"roll_sp", "pitch_sp", "yaw_sp"}.issubset(merged.columns):
        raise ValueError("ULog does not contain a usable vehicle_rates_setpoint topic.")
    if not {"roll_control", "pitch_control", "yaw_control"}.issubset(merged.columns):
        raise ValueError("ULog does not contain usable actuator control outputs.")

    merged["timestamp_s"] = (merged["timestamp_us"] - merged["timestamp_us"].min()) / 1e6

    axis_frames = []
    for axis, rate_col, sp_col, control_col, attitude_col, attitude_sp_col in [
        ("roll", "roll_rate", "roll_sp", "roll_control", "roll", "roll_body"),
        ("pitch", "pitch_rate", "pitch_sp", "pitch_control", "pitch", "pitch_body"),
        ("yaw", "yaw_rate", "yaw_sp", "yaw_control", "yaw", "yaw_body"),
    ]:
        payload = {
            "timestamp_s": merged["timestamp_s"],
            "axis": axis,
            "rate_setpoint": merged[sp_col],
            "rate": merged[rate_col],
            "control_output": merged[control_col],
            "source_path": str(path),
        }
        if attitude_col in merged.columns:
            payload["attitude"] = merged[attitude_col]
        if attitude_sp_col in merged.columns:
            payload["attitude_setpoint"] = merged[attitude_sp_col]
        if "battery_voltage" in merged.columns:
            payload["battery_voltage"] = merged["battery_voltage"]
        axis_frames.append(pd.DataFrame(payload))

    return pd.concat(axis_frames, ignore_index=True)


def _group_datasets(ulog) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for dataset in ulog.data_list:
        grouped.setdefault(dataset.name, []).append(dataset)
    return grouped


def _extract_vehicle_angular_velocity(datasets: dict[str, list]) -> pd.DataFrame:
    dataset = _first_dataset(datasets, "vehicle_angular_velocity")
    if dataset is None:
        raise ValueError("Missing PX4 topic: vehicle_angular_velocity")
    frame = pd.DataFrame(dataset.data)
    renamed = _rename_first_match(
        frame,
        {
            "timestamp_us": ["timestamp"],
            "roll_rate": ["xyz[0]", "rollspeed", "roll_rate"],
            "pitch_rate": ["xyz[1]", "pitchspeed", "pitch_rate"],
            "yaw_rate": ["xyz[2]", "yawspeed", "yaw_rate"],
        },
    )
    return renamed[["timestamp_us", "roll_rate", "pitch_rate", "yaw_rate"]]


def _extract_rate_setpoints(datasets: dict[str, list]) -> pd.DataFrame | None:
    dataset = _first_dataset(datasets, "vehicle_rates_setpoint")
    if dataset is None:
        return None
    frame = pd.DataFrame(dataset.data)
    renamed = _rename_first_match(
        frame,
        {
            "timestamp_us": ["timestamp"],
            "roll_sp": ["roll", "roll_body"],
            "pitch_sp": ["pitch", "pitch_body"],
            "yaw_sp": ["yaw", "yaw_body"],
        },
    )
    return renamed[["timestamp_us", "roll_sp", "pitch_sp", "yaw_sp"]]


def _extract_actuator_controls(datasets: dict[str, list]) -> pd.DataFrame | None:
    dataset = _first_dataset(datasets, "actuator_controls_0", "actuator_motors", "actuator_servos")
    if dataset is None:
        return None
    frame = pd.DataFrame(dataset.data)
    renamed = _rename_first_match(
        frame,
        {
            "timestamp_us": ["timestamp"],
            "roll_control": ["control[0]", "control.0", "control_0"],
            "pitch_control": ["control[1]", "control.1", "control_1"],
            "yaw_control": ["control[2]", "control.2", "control_2"],
        },
    )
    if "roll_control" not in renamed:
        outputs = _normalize_motor_outputs(frame)
        renamed["roll_control"] = outputs[:, 0]
        renamed["pitch_control"] = outputs[:, 1]
        renamed["yaw_control"] = outputs[:, 2]
        renamed["timestamp_us"] = frame["timestamp"]
    return renamed[["timestamp_us", "roll_control", "pitch_control", "yaw_control"]]


def _extract_attitude(datasets: dict[str, list]) -> pd.DataFrame | None:
    dataset = _first_dataset(datasets, "vehicle_attitude")
    if dataset is None:
        return None
    frame = pd.DataFrame(dataset.data)
    if {"q[0]", "q[1]", "q[2]", "q[3]"}.issubset(frame.columns):
        quat = frame[["q[1]", "q[2]", "q[3]", "q[0]"]].to_numpy(dtype=float)
        euler = Rotation.from_quat(quat).as_euler("xyz", degrees=False)
        return pd.DataFrame(
            {
                "timestamp_us": frame["timestamp"],
                "roll": euler[:, 0],
                "pitch": euler[:, 1],
                "yaw": euler[:, 2],
            }
        )
    return None


def _extract_attitude_setpoint(datasets: dict[str, list]) -> pd.DataFrame | None:
    dataset = _first_dataset(datasets, "vehicle_attitude_setpoint")
    if dataset is None:
        return None
    frame = pd.DataFrame(dataset.data)
    renamed = _rename_first_match(
        frame,
        {
            "timestamp_us": ["timestamp"],
            "roll_body": ["roll_body"],
            "pitch_body": ["pitch_body"],
            "yaw_body": ["yaw_body"],
        },
    )
    required = {"timestamp_us", "roll_body", "pitch_body", "yaw_body"}
    if not required.issubset(renamed.columns):
        return None
    return renamed[["timestamp_us", "roll_body", "pitch_body", "yaw_body"]]


def _extract_battery(datasets: dict[str, list]) -> pd.DataFrame | None:
    dataset = _first_dataset(datasets, "battery_status")
    if dataset is None:
        return None
    frame = pd.DataFrame(dataset.data)
    renamed = _rename_first_match(
        frame,
        {
            "timestamp_us": ["timestamp"],
            "battery_voltage": ["voltage_v", "voltage_filtered_v"],
        },
    )
    required = {"timestamp_us", "battery_voltage"}
    if not required.issubset(renamed.columns):
        return None
    return renamed[["timestamp_us", "battery_voltage"]]


def _first_dataset(datasets: dict[str, list], *names: str):
    for name in names:
        if name in datasets and datasets[name]:
            return datasets[name][0]
    return None


def _rename_first_match(frame: pd.DataFrame, mapping: dict[str, list[str]]) -> pd.DataFrame:
    renamed = frame.copy()
    for target, candidates in mapping.items():
        for candidate in candidates:
            if candidate in renamed.columns:
                renamed = renamed.rename(columns={candidate: target})
                break
    return renamed


def _normalize_motor_outputs(frame: pd.DataFrame) -> np.ndarray:
    motor_cols = [column for column in frame.columns if column.startswith("control[") or column.startswith("output[")]
    if len(motor_cols) < 4:
        raise ValueError("Unable to derive actuator controls from ULog motor outputs.")
    values = frame[motor_cols[:4]].to_numpy(dtype=float)
    centered = values - values.mean(axis=1, keepdims=True)
    roll = centered[:, 0] - centered[:, 1] - centered[:, 2] + centered[:, 3]
    pitch = centered[:, 0] + centered[:, 1] - centered[:, 2] - centered[:, 3]
    yaw = centered[:, 0] - centered[:, 1] + centered[:, 2] - centered[:, 3]
    stacked = np.column_stack([roll, pitch, yaw])
    max_abs = np.maximum(np.max(np.abs(stacked), axis=0), 1e-6)
    return stacked / max_abs
