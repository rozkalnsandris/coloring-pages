"""Pure contract for the private origin-request channel; no runtime I/O."""
from __future__ import annotations

import json
import re

from goatcounter_pageview_contract import published_page_ids

ROUTE = "/internal/origin-count"
HOST = "origin-counter.invalid"
MAX_QUERY = 2048
KEY = re.compile(r"[A-Za-z0-9_.~-]+\Z")
VALUE = re.compile(r"(?:[A-Za-z0-9_.~!$'()*+,:@/?=-]|%[0-9A-Fa-f]{2})*\Z")
ID = re.compile(r"[0-9]{7}\Z")


def eligible_id(method: str, normalized_path: str, query: str) -> str | None:
    """Conservative eligibility, independent of Nginx's case-insensitive $arg_id.

    Only literal ASCII query keys are measured. Encoded keys (including aliases),
    malformed percent escapes, empty fields, bare keys and case aliases drop the
    measurement. Other values are discarded, never decoded or forwarded.
    """
    if method != "GET" or normalized_path != "/detail.html":
        return None
    if not 1 <= len(query) <= MAX_QUERY:
        return None
    found = None
    for field in query.split("&"):
        key, sep, value = field.partition("=")
        if not sep or not KEY.fullmatch(key) or not VALUE.fullmatch(value):
            return None
        if key.lower() == "id":
            if key != "id" or found is not None or not ID.fullmatch(value):
                return None
            found = value
    return found


def backend_message(method: str, target: str, headers: list[tuple[str, str]],
                    body: bytes, catalog: object) -> bytes:
    """Validate the complete minimized wire shape, then independently gate catalog.

    Unix peer identity/access is a separate mandatory listener responsibility.
    A Host header alone never authenticates a caller. Only a fresh backend body
    is returned; no caller header or original query can be copied through it.
    """
    expected = {"host": HOST, "content-type": "application/json",
                "content-length": "21", "connection": "close"}
    normalized = [(k.lower(), v) for k, v in headers]
    if (method != "POST" or target != ROUTE or len(normalized) != len(expected)
            or dict(normalized) != expected or len(body) != 21):
        raise ValueError("ORIGIN_WIRE_SHAPE")
    # Require the canonical fixed-width wire body, not arbitrary JSON.
    match = re.fullmatch(rb'\{"page_id":"([0-9]{7})"\}', body)
    if not match:
        raise ValueError("ORIGIN_BODY")
    page_id = match[1].decode("ascii")
    if page_id not in published_page_ids(catalog):
        raise ValueError("ORIGIN_UNPUBLISHED")
    return json.dumps({"no_sessions": True,
                       "hits": [{"path": "/origin-detail-request/" + page_id}]},
                      separators=(",", ":")).encode("ascii")
