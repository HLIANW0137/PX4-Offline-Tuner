from __future__ import annotations

import socket
import threading
import webbrowser

from streamlit import config as streamlit_config
from streamlit.web import bootstrap

from px4_offline_tuner.streamlit_runner import create_bootstrap_script


def main() -> None:
    port = _pick_available_port(8501)
    app_path = create_bootstrap_script()

    # Open the browser shortly after the embedded Streamlit server starts.
    threading.Timer(1.8, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    streamlit_config.set_option("global.developmentMode", False)
    streamlit_config.set_option("server.port", port)
    streamlit_config.set_option("browser.gatherUsageStats", False)
    streamlit_config.set_option("server.headless", True)

    bootstrap.run(
        str(app_path),
        False,
        [],
        {},
    )


def _pick_available_port(default_port: int) -> int:
    for port in range(default_port, default_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return default_port


if __name__ == "__main__":
    main()
