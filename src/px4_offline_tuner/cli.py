from __future__ import annotations

import argparse
from pathlib import Path

from streamlit import config as streamlit_config
from streamlit.web import bootstrap

from .pipeline import PX4OfflineTuner
from .streamlit_runner import create_bootstrap_script


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PX4 offline log auto tuning tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run an offline tuning session")
    run_parser.add_argument("--input", nargs="+", required=True, help="One or more input CSV or ULog paths")
    run_parser.add_argument("--output", required=True, help="Directory for reports and plots")
    run_parser.add_argument("--rate-hz", type=float, default=200.0, help="Resample rate")

    ui_parser = subparsers.add_parser("ui", help="Launch the visual dashboard")
    ui_parser.add_argument("--port", type=int, default=8501, help="Port for the Streamlit app")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        tuner = PX4OfflineTuner(target_rate_hz=args.rate_hz)
        input_paths = [Path(path) for path in args.input]
        report = tuner.run_many(input_paths, Path(args.output))
        print("PX4 offline tuning completed.")
        print(f"Report directory: {report.output_dir}")
        print(f"Input logs: {len(report.input_paths)}")
        for item in report.summary:
            print(f"- {item}")
    elif args.command == "ui":
        app_path = create_bootstrap_script()
        streamlit_config.set_option("global.developmentMode", False)
        streamlit_config.set_option("server.port", args.port)
        streamlit_config.set_option("browser.gatherUsageStats", False)
        streamlit_config.set_option("server.headless", True)
        bootstrap.run(
            str(app_path),
            False,
            [],
            {},
        )


if __name__ == "__main__":
    main()
