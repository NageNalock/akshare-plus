#!/usr/bin/env python
# -*- coding:utf-8 -*-

from akshare_mcp.server import _build_tool_signature


def test_build_tool_signature_contains_preview_rows():
    signature = _build_tool_signature(
        [
            {
                "name": "symbol",
                "required": True,
                "kind": "text",
                "description": "股票代码",
                "parameter_kind": "positional_or_keyword",
            },
            {
                "name": "adjust",
                "required": False,
                "kind": "boolean",
                "description": "是否复权",
                "default": False,
                "parameter_kind": "positional_or_keyword",
            },
        ]
    )

    assert "symbol" in signature.parameters
    assert signature.parameters["symbol"].default is signature.empty
    assert signature.parameters["adjust"].default is False
    assert "preview_rows" in signature.parameters
    assert signature.parameters["preview_rows"].default == 100
