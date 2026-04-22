from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
import math
from pathlib import Path
from typing import Any


def make_jsonable(value: Any) -> Any:
    try:
        import numpy as np
    except Exception:  # pragma: no cover - optional dependency
        np = None

    try:
        import pandas as pd
    except Exception:  # pragma: no cover - optional dependency
        pd = None

    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return make_jsonable(value.value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if np is not None and isinstance(value, np.generic):
        return make_jsonable(value.item())
    if pd is not None:
        if value is pd.NA:
            return None
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        if isinstance(value, pd.Timedelta):
            return str(value)
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
    if isinstance(value, Mapping):
        return {str(key): make_jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [make_jsonable(item) for item in value]
    return str(value)


def serialize_result(result: Any, preview_rows: int = 100) -> dict[str, Any]:
    preview_rows = max(1, min(preview_rows, 2000))

    try:
        import pandas as pd
    except Exception:  # pragma: no cover - optional dependency
        pd = None

    if pd is not None and isinstance(result, pd.DataFrame):
        preview = result.head(preview_rows).to_dict(orient="records")
        return {
            "kind": "dataframe",
            "total_rows": int(len(result)),
            "total_columns": int(len(result.columns)),
            "columns": [str(column) for column in result.columns],
            "dtypes": {str(column): str(dtype) for column, dtype in result.dtypes.items()},
            "truncated": len(result) > preview_rows,
            "preview_rows": make_jsonable(preview),
        }

    if pd is not None and isinstance(result, pd.Series):
        preview_series = result.head(preview_rows)
        preview = [
            {"index": index, "value": value}
            for index, value in preview_series.to_dict().items()
        ]
        return {
            "kind": "series",
            "name": str(result.name) if result.name is not None else "",
            "total_rows": int(len(result)),
            "truncated": len(result) > preview_rows,
            "preview_rows": make_jsonable(preview),
        }

    if isinstance(result, Mapping):
        return {
            "kind": "mapping",
            "size": len(result),
            "value": make_jsonable(result),
        }

    if isinstance(result, Sequence) and not isinstance(result, (str, bytes, bytearray)):
        sequence = list(result)
        return {
            "kind": "sequence",
            "size": len(sequence),
            "truncated": len(sequence) > preview_rows,
            "value": make_jsonable(sequence[:preview_rows]),
        }

    return {
        "kind": "scalar",
        "value": make_jsonable(result),
    }
