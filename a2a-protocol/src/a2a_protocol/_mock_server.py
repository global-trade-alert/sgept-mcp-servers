"""Tiny mock-backend server entry point — for demos / local smoke tests.

Run:
    uv run python -m a2a_protocol._mock_server   # uses default port 8081
    PORT=9000 uv run python -m a2a_protocol._mock_server

The MockBackend defined in tests/mock_backend.py is the echo agent. This
module re-uses it (imports from the tests package) so we have ONE definition
of the mock-echo behaviour. Keep the test running against the same code path
the demo uses.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow importing from tests/ which is a sibling of src/
TESTS_DIR = Path(__file__).resolve().parents[2] / "tests"
if str(TESTS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR.parent))

from tests.mock_backend import MockBackend  # noqa: E402

from a2a_protocol import create_app  # noqa: E402


def main() -> None:
    import uvicorn

    backend = MockBackend()
    app = create_app(backend)
    port = int(os.environ.get("PORT", "8081"))
    print(f"Mock A2A agent serving at http://127.0.0.1:{port}")
    print(f"  Agent card: http://127.0.0.1:{port}/.well-known/agent-card.json")
    print(f"  Healthz:    http://127.0.0.1:{port}/healthz")
    print(f"  JSON-RPC:   POST http://127.0.0.1:{port}/v1/jsonrpc")
    print(f"  Bearer key: mock-key")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
