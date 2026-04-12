from __future__ import annotations

import tempfile
from pathlib import Path


def create_bootstrap_script() -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="px4_offline_tuner_"))
    script_path = temp_dir / "streamlit_app.py"
    script_path.write_text(
        "import runpy\n"
        "runpy.run_module('px4_offline_tuner.webapp', run_name='__main__')\n",
        encoding="utf-8",
    )
    return script_path
