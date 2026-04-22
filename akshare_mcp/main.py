from __future__ import annotations

import argparse

from .server import build_mcp_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AKShare MCP server.")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport to run.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for streamable HTTP transport.")
    parser.add_argument("--port", default=8001, type=int, help="Port for streamable HTTP transport.")
    args = parser.parse_args()

    server = build_mcp_server("/mcp")
    server.settings.host = args.host
    server.settings.port = args.port
    server.run(transport=args.transport)
