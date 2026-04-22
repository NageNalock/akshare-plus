from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AKShare web console.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the HTTP server.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind the HTTP server.")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto reload for local development.",
    )
    args = parser.parse_args()

    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env
        raise SystemExit("缺少 uvicorn，请先执行: pip install -e '.[web]'") from exc

    uvicorn.run(
        "akshare_web.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
