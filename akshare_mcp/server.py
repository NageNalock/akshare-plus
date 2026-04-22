from __future__ import annotations

import inspect
from typing import Annotated, Any, Literal

from pydantic import Field

from akshare_web.introspection import AkshareRegistry


def build_mcp_server(streamable_http_path: str = "/mcp"):
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env
        raise RuntimeError(
            "缺少 MCP 依赖，请先执行: pip install -e '.[mcp]'"
        ) from exc

    registry = AkshareRegistry()
    server = FastMCP(
        "AKShare MCP",
        instructions=(
            "AKShare financial data server. Use helper tools to search interfaces, "
            "or call AKShare function tools directly by name."
        ),
        json_response=True,
        streamable_http_path=streamable_http_path,
    )

    _register_helper_tools(server, registry)
    _register_resources(server, registry)
    _register_dynamic_tools(server, registry)
    return server


def _register_helper_tools(server, registry: AkshareRegistry) -> None:
    @server.tool(
        name="akshare_health",
        title="AKShare Health",
        description="Return AKShare registry health and MCP availability summary.",
        structured_output=True,
    )
    def akshare_health() -> dict[str, Any]:
        return registry.health()

    @server.tool(
        name="akshare_search_functions",
        title="Search AKShare Functions",
        description="Search AKShare public interfaces by keyword and category.",
        structured_output=True,
    )
    def akshare_search_functions(
        query: Annotated[str, Field(description="Keyword to search in function names and docs")] = "",
        category: Annotated[str, Field(description="Optional category such as stock, bond, macro")] = "",
        limit: Annotated[int, Field(description="Maximum number of items to return")] = 50,
    ) -> dict[str, Any]:
        payload = registry.list_functions(query=query, category=category)
        items = payload["items"][: max(1, limit)]
        return {
            "total": payload["total"],
            "returned": len(items),
            "items": items,
            "categories": payload["categories"],
        }

    @server.tool(
        name="akshare_get_function",
        title="Get AKShare Function Detail",
        description="Fetch one AKShare function's metadata, parameter schema, and docs.",
        structured_output=True,
    )
    def akshare_get_function(
        name: Annotated[str, Field(description="Exact AKShare function name")]
    ) -> dict[str, Any]:
        return registry.get_function(name)

    @server.tool(
        name="akshare_execute",
        title="Execute AKShare Function",
        description="Execute any AKShare function by name with a JSON parameters object.",
        structured_output=True,
    )
    def akshare_execute(
        name: Annotated[str, Field(description="Exact AKShare function name")],
        parameters: Annotated[
            dict[str, Any],
            Field(description="JSON object containing function parameters"),
        ] | None = None,
        preview_rows: Annotated[
            int,
            Field(description="Maximum number of rows to preview in the structured result"),
        ] = 100,
    ) -> dict[str, Any]:
        return registry.execute(
            name=name,
            parameters=parameters or {},
            preview_rows=preview_rows,
        )


def _register_resources(server, registry: AkshareRegistry) -> None:
    @server.resource(
        "akshare://catalog",
        name="AKShare Catalog",
        description="Browse the AKShare public function catalog.",
    )
    def akshare_catalog() -> dict[str, Any]:
        return registry.list_functions()

    @server.resource(
        "akshare://function/{name}",
        name="AKShare Function Detail",
        description="Read metadata for a single AKShare function.",
    )
    def akshare_function_detail(name: str) -> dict[str, Any]:
        return registry.get_function(name)


def _register_dynamic_tools(server, registry: AkshareRegistry) -> None:
    for meta in registry.load_functions().values():
        wrapper = _build_tool_wrapper(meta, registry)
        server.tool(
            name=meta["name"],
            title=meta["title"],
            description=_tool_description(meta),
            structured_output=True,
        )(wrapper)


def _build_tool_wrapper(meta: dict[str, Any], registry: AkshareRegistry):
    tool_name = meta["name"]
    signature = _build_tool_signature(meta.get("parameters", []))

    def tool_wrapper(**kwargs):
        preview_rows = kwargs.pop("preview_rows", 100)
        return registry.execute(
            name=tool_name,
            parameters=kwargs,
            preview_rows=preview_rows,
        )

    tool_wrapper.__name__ = tool_name
    tool_wrapper.__qualname__ = tool_name
    tool_wrapper.__doc__ = _tool_description(meta)
    tool_wrapper.__signature__ = signature
    tool_wrapper.__annotations__ = _signature_annotations(signature)
    return tool_wrapper


def _build_tool_signature(parameters: list[dict[str, Any]]) -> inspect.Signature:
    signature_parameters: list[inspect.Parameter] = []
    for definition in parameters:
        parameter_kind = definition.get("parameter_kind")
        if parameter_kind in {"var_keyword", "var_positional"}:
            continue

        signature_parameters.append(
            inspect.Parameter(
                name=definition["name"],
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=_annotation_for_parameter(definition),
                default=inspect._empty
                if definition.get("required")
                else definition.get("default"),
            )
        )

    signature_parameters.append(
        inspect.Parameter(
            name="preview_rows",
            kind=inspect.Parameter.KEYWORD_ONLY,
            annotation=Annotated[
                int,
                Field(
                    description="Maximum number of rows to preview in the structured result"
                ),
            ],
            default=100,
        )
    )

    return inspect.Signature(
        parameters=signature_parameters,
        return_annotation=dict[str, Any],
    )


def _annotation_for_parameter(definition: dict[str, Any]):
    choices = definition.get("choices") or []
    description = definition.get("description") or definition.get("annotation") or definition.get("doc_type") or ""

    if choices:
        base_annotation = Literal.__getitem__(tuple(choices))
    else:
        kind = definition.get("kind")
        if kind == "boolean":
            base_annotation = bool
        elif kind == "integer":
            base_annotation = int
        elif kind == "number":
            base_annotation = float
        elif kind == "json":
            base_annotation = dict[str, Any] | list[Any] | str | int | float | bool | None
        else:
            base_annotation = str

    if description:
        return Annotated[base_annotation, Field(description=description)]
    return base_annotation


def _signature_annotations(signature: inspect.Signature) -> dict[str, Any]:
    annotations: dict[str, Any] = {"return": dict[str, Any]}
    for parameter in signature.parameters.values():
        annotations[parameter.name] = parameter.annotation
    return annotations


def _tool_description(meta: dict[str, Any]) -> str:
    parts = [
        meta.get("description") or meta.get("summary") or meta["name"],
        f"Module: {meta.get('module', '-')}",
    ]
    if meta.get("section"):
        parts.append(f"Section: {meta['section']}")
    parts.append("Returns structured preview data; use preview_rows to control output size.")
    return " | ".join(parts)
