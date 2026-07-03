"""Shared helpers for structured JSON AI output workflows."""

from __future__ import annotations

import json
from typing import Any

from backend.app.services.ai.exceptions import AIResponseError


def _extract_json_object(candidate: str) -> str | None:
    """Extract the first balanced JSON object from arbitrary model text."""

    in_string = False
    escape_next = False
    depth = 0
    start_index: int | None = None

    for index, char in enumerate(candidate):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            if depth == 0:
                start_index = index
            depth += 1
            continue

        if char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start_index is not None:
                return candidate[start_index : index + 1]

    return None


def parse_json_response(
    *,
    raw_text: str,
    empty_error_message: str,
    invalid_json_error_message: str,
) -> dict[str, Any]:
    """Normalize Gemini output text and parse strict JSON payload."""

    candidate = raw_text.strip()
    if not candidate:
        raise AIResponseError(empty_error_message)

    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            candidate = "\n".join(lines[1:-1]).strip()

    parse_candidates = [candidate]
    extracted = _extract_json_object(candidate)
    if extracted and extracted != candidate:
        parse_candidates.append(extracted)

    parsed: Any = None
    parse_error: json.JSONDecodeError | None = None
    for parse_candidate in parse_candidates:
        try:
            parsed = json.loads(parse_candidate)
            break
        except json.JSONDecodeError as exc:
            parse_error = exc

    if parsed is None:
        raise AIResponseError(invalid_json_error_message) from parse_error

    if not isinstance(parsed, dict):
        raise AIResponseError(invalid_json_error_message)

    return parsed
