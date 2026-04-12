from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile


def atomic_write_text(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=destination.parent, encoding=encoding, newline="") as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(destination)


def atomic_write_json(path: str | Path, payload: object) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2), encoding="utf-8")
