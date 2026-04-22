from __future__ import annotations

from pathlib import Path
import re

TABLE_RULE_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def parse_docs_directory(root: Path) -> dict[str, dict]:
    """
    Parse the bundled markdown docs into a function metadata index.
    """
    if not root.exists():
        return {}

    docs_index: dict[str, dict] = {}
    for path in sorted(root.rglob("*.md")):
        for name, record in parse_docs_file(path).items():
            existing = docs_index.get(name)
            if existing is None or _score_record(record) > _score_record(existing):
                docs_index[name] = record
    return docs_index


def parse_docs_file(path: Path) -> dict[str, dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings: list[str] = []
    records: dict[str, dict] = {}
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line:
            index += 1
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            depth = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            headings = headings[: depth - 1]
            headings.append(title)
            index += 1
            continue

        if line.startswith("接口:"):
            interface_name = line.split("接口:", 1)[1].strip()
            record = {
                "name": interface_name,
                "title": headings[-1] if headings else interface_name,
                "breadcrumbs": headings[:],
                "section": " / ".join(headings),
                "doc_path": path.as_posix(),
                "target_url": "",
                "description": "",
                "limit": "",
                "documentation": "",
                "input_parameters": [],
                "output_parameters": [],
            }
            cursor = index + 1
            while cursor < len(lines):
                current = lines[cursor].strip()
                if current.startswith("接口:"):
                    break
                if HEADING_RE.match(current):
                    break
                if current.startswith("目标地址:"):
                    record["target_url"] = current.split("目标地址:", 1)[1].strip()
                    cursor += 1
                    continue
                if current.startswith("描述:"):
                    record["description"] = current.split("描述:", 1)[1].strip()
                    cursor += 1
                    continue
                if current.startswith("限量:"):
                    record["limit"] = current.split("限量:", 1)[1].strip()
                    cursor += 1
                    continue
                if current.startswith("输入参数"):
                    rows, cursor = _parse_markdown_table(lines, cursor + 1)
                    record["input_parameters"] = _normalize_rows(rows)
                    continue
                if current.startswith("输出参数"):
                    rows, cursor = _parse_markdown_table(lines, cursor + 1)
                    record["output_parameters"] = _normalize_rows(rows)
                    continue
                cursor += 1
            record["documentation"] = _clean_doc_block(lines[index + 1 : cursor])
            records[interface_name] = record
            index = cursor
            continue

        index += 1

    return records


def _parse_markdown_table(lines: list[str], start: int) -> tuple[list[dict[str, str]], int]:
    cursor = start
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1

    if cursor >= len(lines) or not lines[cursor].lstrip().startswith("|"):
        return [], cursor

    header = _split_markdown_row(lines[cursor])
    cursor += 1
    if cursor < len(lines) and TABLE_RULE_RE.match(lines[cursor].strip()):
        cursor += 1

    rows: list[dict[str, str]] = []
    while cursor < len(lines):
        line = lines[cursor].strip()
        if not line.startswith("|"):
            break
        cells = _split_markdown_row(line)
        if len(cells) < len(header):
            cells.extend([""] * (len(header) - len(cells)))
        row = {
            header_item: cells[position].strip()
            for position, header_item in enumerate(header)
        }
        rows.append(row)
        cursor += 1
    return rows, cursor


def _split_markdown_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def _normalize_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append(
            {
                "name": row.get("名称", "").strip(),
                "type": row.get("类型", "").strip(),
                "description": row.get("描述", "").strip(),
            }
        )
    return normalized


def _clean_doc_block(lines: list[str]) -> str:
    start = 0
    end = len(lines)

    while start < end and not lines[start].strip():
        start += 1

    while end > start and not lines[end - 1].strip():
        end -= 1

    return "\n".join(line.rstrip() for line in lines[start:end]).strip()


def _score_record(record: dict) -> int:
    return (
        (1 if record.get("description") else 0)
        + (1 if record.get("target_url") else 0)
        + (1 if record.get("limit") else 0)
        + len(record.get("input_parameters", []))
        + len(record.get("output_parameters", []))
    )
