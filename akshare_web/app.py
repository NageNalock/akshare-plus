from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any

from .introspection import AkshareRegistry

REGISTRY = AkshareRegistry()
PACKAGE_ROOT = Path(__file__).resolve().parent
FRONTEND_DIST_DIR = PACKAGE_ROOT / "static" / "dist"
FRONTEND_DIST_INDEX = FRONTEND_DIST_DIR / "index.html"
FRONTEND_FALLBACK_INDEX = PACKAGE_ROOT / "static" / "index.html"


def create_app():
    try:
        from fastapi import Body, FastAPI, HTTPException, Query
        from fastapi.responses import FileResponse
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env
        raise RuntimeError(
            "缺少 Web 依赖，请先执行: pip install -e '.[web]'"
        ) from exc

    mcp_app = None
    mcp_server = None
    mcp_error = ""
    try:
        from akshare_mcp.server import build_mcp_server

        mcp_server = build_mcp_server("/")
        mcp_app = mcp_server.streamable_http_app()
    except Exception as exc:  # pragma: no cover - depends on runtime env
        mcp_error = f"{type(exc).__name__}: {exc}"

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with AsyncExitStack() as stack:
            if mcp_server is not None:
                await stack.enter_async_context(mcp_server.session_manager.run())
            yield

    app = FastAPI(
        title="AKShare Dashboard",
        description="Discover, execute, and expose AKShare functions via HTTP, React UI, and MCP.",
        version="0.1.0",
        lifespan=lifespan,
    )
    if mcp_app is not None:
        app.mount("/mcp", mcp_app, name="mcp")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(_resolve_frontend_index())

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        payload = REGISTRY.health()
        payload.update(
            {
                "frontend_ready": FRONTEND_DIST_INDEX.exists(),
                "mcp_ready": mcp_app is not None,
                "mcp_path": "/mcp/" if mcp_app is not None else "",
                "mcp_error": mcp_error,
            }
        )
        return payload

    @app.get("/api/functions")
    async def list_functions(
        query: str = Query(default=""),
        category: str = Query(default=""),
    ) -> dict[str, Any]:
        try:
            return REGISTRY.list_functions(query=query, category=category)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/functions/{name}")
    async def get_function(name: str) -> dict[str, Any]:
        try:
            return REGISTRY.get_function(name)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/functions/{name}/execute")
    async def execute_function(
        name: str,
        payload: dict[str, Any] = Body(default=None),
    ) -> dict[str, Any]:
        payload = payload or {}
        try:
            return REGISTRY.execute(
                name=name,
                parameters=payload.get("parameters", {}),
                preview_rows=int(payload.get("preview_rows", 100)),
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}") from exc

    @app.get("/{full_path:path}")
    async def frontend(full_path: str) -> FileResponse:
        if full_path.startswith(("api/", "mcp", "docs", "openapi.json", "redoc")):
            raise HTTPException(status_code=404, detail="Not found")

        if FRONTEND_DIST_INDEX.exists():
            asset_path = FRONTEND_DIST_DIR / full_path
            if full_path and asset_path.exists() and asset_path.is_file():
                return FileResponse(asset_path)
            return FileResponse(FRONTEND_DIST_INDEX)

        return FileResponse(FRONTEND_FALLBACK_INDEX)

    return app


def _resolve_frontend_index() -> Path:
    if FRONTEND_DIST_INDEX.exists():
        return FRONTEND_DIST_INDEX
    return FRONTEND_FALLBACK_INDEX
