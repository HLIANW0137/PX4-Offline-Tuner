from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def default_output_root() -> Path:
    base = Path.home() / "PX4OfflineTuner" / "outputs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def log_root() -> Path:
    base = Path.home() / "PX4OfflineTuner" / "logs"
    base.mkdir(parents=True, exist_ok=True)
    return base
