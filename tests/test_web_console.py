#!/usr/bin/env python
# -*- coding:utf-8 -*-

from pathlib import Path

from akshare_web.docs_parser import parse_docs_directory
from akshare_web.introspection import (
    coerce_parameter_value,
    parse_public_exports,
)


ROOT = Path(__file__).resolve().parents[1]


def test_docs_parser_finds_known_interface():
    docs_index = parse_docs_directory(ROOT / "docs" / "data")
    assert "spot_price_qh" in docs_index
    record = docs_index["spot_price_qh"]
    assert record["description"] == "99 期货-数据-期现-现货走势"
    assert "目标地址: https://www.99qh.com/data/spotTrend" in record["documentation"]
    assert "接口示例" in record["documentation"]
    assert any(item["name"] == "symbol" for item in record["input_parameters"])


def test_public_exports_cover_main_surface():
    exports = parse_public_exports(ROOT / "akshare" / "__init__.py")
    export_names = {item["name"] for item in exports}
    assert "stock_zh_a_hist" in export_names
    assert len(export_names) > 1000


def test_parameter_coercion():
    assert (
        coerce_parameter_value("true", {"name": "adjust", "kind": "boolean"}) is True
    )
    assert coerce_parameter_value("42", {"name": "limit", "kind": "integer"}) == 42
    assert abs(
        coerce_parameter_value("3.14", {"name": "ratio", "kind": "number"}) - 3.14
    ) < 1e-9
    assert coerce_parameter_value(
        '{"symbol": "000001"}',
        {"name": "payload", "kind": "json", "annotation": "dict"},
    ) == {"symbol": "000001"}
