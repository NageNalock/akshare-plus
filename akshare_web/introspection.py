from __future__ import annotations

from pathlib import Path
import ast
import inspect
import json
from threading import Lock
from time import perf_counter
from typing import Any, get_args, get_origin

from .docs_parser import parse_docs_directory
from .serialization import make_jsonable, serialize_result


class AkshareRegistry:
    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[1]
        self.docs_root = self.repo_root / "docs" / "data"
        self._lock = Lock()
        self._docs_index: dict[str, dict] | None = None
        self._functions: dict[str, dict] | None = None
        self._last_error = ""

    def health(self) -> dict[str, Any]:
        try:
            functions = self.load_functions()
            return {
                "ready": True,
                "function_count": len(functions),
                "category_count": len({item["category"] for item in functions.values()}),
                "docs_count": len(self.docs_index),
                "error": "",
            }
        except RuntimeError as exc:
            return {
                "ready": False,
                "function_count": 0,
                "category_count": 0,
                "docs_count": len(self.docs_index),
                "error": str(exc),
            }

    @property
    def docs_index(self) -> dict[str, dict]:
        if self._docs_index is None:
            self._docs_index = parse_docs_directory(self.docs_root)
        return self._docs_index

    def load_functions(self) -> dict[str, dict]:
        with self._lock:
            if self._functions is not None:
                return self._functions

            try:
                import akshare as ak
            except Exception as exc:  # pragma: no cover - depends on runtime env
                self._last_error = (
                    "无法导入 akshare，请先安装项目依赖。"
                    f" 详细错误: {type(exc).__name__}: {exc}"
                )
                raise RuntimeError(self._last_error) from exc

            exports = parse_public_exports(Path(ak.__file__).resolve())
            functions: dict[str, dict] = {}
            seen: set[str] = set()

            for export in exports:
                public_name = export["name"]
                if public_name in seen:
                    continue
                obj = getattr(ak, public_name, None)
                if obj is None or inspect.isclass(obj) or not callable(obj):
                    continue

                module_name = getattr(obj, "__module__", export["module"])
                doc_record = self.docs_index.get(public_name, {})
                signature = safe_signature(obj)
                parameters = build_parameter_schema(signature, doc_record)
                functions[public_name] = {
                    "name": public_name,
                    "module": module_name,
                    "category": module_name.split(".")[1] if "." in module_name else "misc",
                    "signature": signature_to_text(signature),
                    "summary": inspect.getdoc(obj).splitlines()[0].strip()
                    if inspect.getdoc(obj)
                    else "",
                    "description": doc_record.get("description")
                    or (inspect.getdoc(obj) or "").split("\n\n")[0].strip(),
                    "title": doc_record.get("title") or public_name,
                    "section": doc_record.get("section", ""),
                    "documentation": doc_record.get("documentation")
                    or (inspect.getdoc(obj) or "").strip(),
                    "doc_path": doc_record.get("doc_path", ""),
                    "target_url": doc_record.get("target_url", ""),
                    "limit": doc_record.get("limit", ""),
                    "parameters": parameters,
                    "output_parameters": doc_record.get("output_parameters", []),
                    "_callable": obj,
                }
                seen.add(public_name)

            self._functions = functions
            self._last_error = ""
            return self._functions

    def list_functions(self, query: str = "", category: str = "") -> dict[str, Any]:
        functions = self.load_functions()
        query = query.strip().lower()
        category = category.strip().lower()
        items: list[dict[str, Any]] = []

        for item in functions.values():
            if category and item["category"].lower() != category:
                continue

            haystack = " ".join(
                filter(
                    None,
                    [
                        item["name"],
                        item["module"],
                        item["category"],
                        item["description"],
                        item["section"],
                    ],
                )
            ).lower()
            if query and query not in haystack:
                continue

            items.append(self._public_summary(item))

        items.sort(key=lambda current: current["name"])
        category_counts: dict[str, int] = {}
        for function in functions.values():
            category_counts[function["category"]] = (
                category_counts.get(function["category"], 0) + 1
            )

        return {
            "total": len(items),
            "items": items,
            "categories": [
                {"name": name, "count": category_counts[name]}
                for name in sorted(category_counts)
            ],
        }

    def get_function(self, name: str) -> dict[str, Any]:
        functions = self.load_functions()
        try:
            item = functions[name]
        except KeyError as exc:
            raise KeyError(f"未找到函数: {name}") from exc
        return self._public_detail(item)

    def execute(self, name: str, parameters: dict[str, Any], preview_rows: int = 100) -> dict[str, Any]:
        functions = self.load_functions()
        if name not in functions:
            raise KeyError(f"未找到函数: {name}")

        function_meta = functions[name]
        coerced_parameters = coerce_parameters(parameters or {}, function_meta["parameters"])
        started_at = perf_counter()
        result = function_meta["_callable"](**coerced_parameters)
        elapsed_ms = round((perf_counter() - started_at) * 1000, 2)

        return {
            "name": function_meta["name"],
            "module": function_meta["module"],
            "elapsed_ms": elapsed_ms,
            "parameters": make_jsonable(coerced_parameters),
            "result": serialize_result(result, preview_rows=preview_rows),
        }

    def _public_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": item["name"],
            "title": item["title"],
            "category": item["category"],
            "module": item["module"],
            "signature": item["signature"],
            "description": item["description"],
            "section": item["section"],
        }

    def _public_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in item.items()
            if not key.startswith("_")
        }


def parse_public_exports(init_path: Path) -> list[dict[str, str]]:
    root = ast.parse(init_path.read_text(encoding="utf-8"))
    exports: list[dict[str, str]] = []
    for node in root.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if not node.module or not node.module.startswith("akshare."):
            continue
        for alias in node.names:
            public_name = alias.asname or alias.name
            if public_name.startswith("_"):
                continue
            exports.append(
                {
                    "name": public_name,
                    "source_name": alias.name,
                    "module": node.module,
                }
            )
    return exports


def safe_signature(obj: Any) -> inspect.Signature | None:
    try:
        return inspect.signature(obj)
    except Exception:
        return None


def signature_to_text(signature: inspect.Signature | None) -> str:
    return str(signature) if signature is not None else "(...)"


def build_parameter_schema(signature: inspect.Signature | None, doc_record: dict) -> list[dict[str, Any]]:
    if signature is None:
        return []

    doc_params = {
        row.get("name", ""): row
        for row in doc_record.get("input_parameters", [])
        if row.get("name")
    }
    parameters: list[dict[str, Any]] = []

    for param in signature.parameters.values():
        doc_param = doc_params.get(param.name, {})
        annotation = format_annotation(param.annotation)
        default_value = None if param.default is inspect._empty else make_jsonable(param.default)
        parameters.append(
            {
                "name": param.name,
                "required": param.default is inspect._empty
                and param.kind
                not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL),
                "kind": infer_parameter_kind(param.annotation, param.default, doc_param.get("type", "")),
                "annotation": annotation,
                "doc_type": doc_param.get("type", ""),
                "description": doc_param.get("description", ""),
                "default": default_value,
                "has_default": param.default is not inspect._empty,
                "choices": extract_literal_choices(param.annotation),
                "parameter_kind": param.kind.name.lower(),
            }
        )
    return parameters


def format_annotation(annotation: Any) -> str:
    if annotation is inspect._empty:
        return ""
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation).replace("typing.", "")


def extract_literal_choices(annotation: Any) -> list[Any]:
    origin = get_origin(annotation)
    if origin is None:
        return []

    if getattr(origin, "__qualname__", "") == "Literal" or str(origin).endswith(".Literal"):
        return [make_jsonable(item) for item in get_args(annotation)]
    return []


def infer_parameter_kind(annotation: Any, default: Any, doc_type: str) -> str:
    hint = f"{format_annotation(annotation)} {doc_type}".lower()

    if "bool" in hint or isinstance(default, bool):
        return "boolean"
    if "int" in hint or (isinstance(default, int) and not isinstance(default, bool)):
        return "integer"
    if "float" in hint or "decimal" in hint or isinstance(default, float):
        return "number"
    if any(token in hint for token in ("list", "dict", "tuple", "set", "json")):
        return "json"
    if isinstance(default, (list, dict, tuple, set)):
        return "json"
    return "text"


def coerce_parameters(payload: dict[str, Any], definitions: list[dict[str, Any]]) -> dict[str, Any]:
    definition_map = {item["name"]: item for item in definitions}
    coerced: dict[str, Any] = {}

    for key, value in payload.items():
        if key not in definition_map:
            raise ValueError(f"未知参数: {key}")
        coerced[key] = coerce_parameter_value(value, definition_map[key])

    missing = [
        item["name"]
        for item in definitions
        if item["required"] and item["name"] not in coerced
    ]
    if missing:
        raise ValueError(f"缺少必填参数: {', '.join(missing)}")

    return coerced


def coerce_parameter_value(value: Any, definition: dict[str, Any]) -> Any:
    kind = definition.get("kind", "text")
    if value is None:
        return None

    if kind == "boolean":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        raise ValueError(f"参数 {definition['name']} 需要布尔值")

    if kind == "integer":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return int(str(value).strip())

    if kind == "number":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(str(value).strip())

    if kind == "json":
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, tuple):
            return list(value)
        text = str(value).strip()
        if not text:
            return None
        parsed = json.loads(text)
        if "tuple" in definition.get("annotation", "").lower():
            return tuple(parsed)
        if "set" in definition.get("annotation", "").lower():
            return set(parsed)
        return parsed

    return value
