#!/usr/bin/env python3
"""Pure source-only contract for the planned GoatCounter pageview adapter.

This module does not start a server, read LIVE content, send network requests,
or activate telemetry. It defines the narrow browser payload/catalog gate and
reporting-day semantics required by issue #376.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import re
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


CLIENT_ROUTE = "/api/pageview"
MAX_BODY_BYTES = 128
PAGE_ID_RE = re.compile(r"[0-9]{7}\Z")
REPORT_TIMEZONE_NAME = "Europe/Berlin"
REPORT_TIMEZONE = ZoneInfo(REPORT_TIMEZONE_NAME)
PERIOD_DAYS = {"today": 1, "7d": 7, "30d": 30}


class ContractStop(ValueError):
    """Stable fail-closed code; never include raw request/catalog data."""


def _stop(code: str) -> None:
    raise ContractStop(code)


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _stop("CLIENT_JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def _valid_origin(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and parsed.path == ""
        and parsed.query == ""
        and parsed.fragment == ""
        and parsed.port in (None, 443)
    )


def _valid_content_type(value: str) -> bool:
    if not isinstance(value, str):
        return False
    parts = [part.strip() for part in value.split(";")]
    if not parts or parts[0].casefold() != "application/json":
        return False
    if len(parts) == 1:
        return True
    if len(parts) != 2 or "=" not in parts[1]:
        return False
    key, raw = (piece.strip() for piece in parts[1].split("=", 1))
    return key.casefold() == "charset" and raw.strip('"').casefold() == "utf-8"


def _renderable_catalog_entry(entry: dict[str, Any]) -> bool:
    if entry.get("hidden") is True or entry.get("visible") is False:
        return False
    pages = entry.get("pages")
    if isinstance(pages, list) and pages:
        for page in pages:
            if not isinstance(page, dict):
                return False
            preview = page.get("preview")
            printable = page.get("print")
            if not (
                isinstance(preview, str) and preview
                and isinstance(printable, str) and printable
            ):
                return False
        return True
    return (
        isinstance(entry.get("preview"), str) and bool(entry["preview"])
        and isinstance(entry.get("print"), str) and bool(entry["print"])
    )


def published_page_ids(catalog: object) -> frozenset[str]:
    """Return only current visible/renderable seven-digit catalogue IDs.

    Legacy non-seven-digit IDs are ignored because #376 explicitly limits
    pageview measurement to the current seven-digit publication contract.
    Malformed catalogue shape and duplicate IDs fail closed.
    """
    if not isinstance(catalog, list):
        _stop("CATALOG_SHAPE")
    seen: set[str] = set()
    allowed: set[str] = set()
    for entry in catalog:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            _stop("CATALOG_SHAPE")
        page_id = entry["id"]
        if page_id in seen:
            _stop("CATALOG_DUPLICATE_ID")
        seen.add(page_id)
        if PAGE_ID_RE.fullmatch(page_id) and _renderable_catalog_entry(entry):
            allowed.add(page_id)
    return frozenset(allowed)


@dataclass(frozen=True)
class AcceptedPageview:
    page_id: str
    logical_path: str

    def goatcounter_payload(self) -> dict[str, object]:
        return {
            "no_sessions": True,
            "hits": [{"path": self.logical_path}],
        }

    def goatcounter_body(self) -> bytes:
        return json.dumps(
            self.goatcounter_payload(),
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")


def accept_client_event(
    *,
    method: str,
    request_target: str,
    content_type: str,
    origin: str,
    expected_origin: str,
    raw_body: bytes,
    catalog: object,
) -> AcceptedPageview:
    """Validate one proposed first-party pageview request.

    The function intentionally receives no IP, User-Agent, referrer, cookies,
    query parameters, campaign or arbitrary header map, so none can be copied
    into GoatCounter output by this contract.
    """
    if method != "POST" or request_target != CLIENT_ROUTE:
        _stop("CLIENT_ROUTE_OR_METHOD")
    if not _valid_origin(expected_origin) or origin != expected_origin:
        _stop("CLIENT_ORIGIN")
    if not _valid_content_type(content_type):
        _stop("CLIENT_CONTENT_TYPE")
    if not isinstance(raw_body, bytes) or not 2 <= len(raw_body) <= MAX_BODY_BYTES:
        _stop("CLIENT_BODY_SIZE")
    try:
        data = json.loads(
            raw_body.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        _stop("CLIENT_JSON")
    if not isinstance(data, dict) or set(data) != {"page_id"}:
        _stop("CLIENT_SCHEMA")
    page_id = data["page_id"]
    if not isinstance(page_id, str) or PAGE_ID_RE.fullmatch(page_id) is None:
        _stop("CLIENT_PAGE_ID")
    if page_id not in published_page_ids(catalog):
        _stop("CLIENT_PAGE_NOT_PUBLISHED")
    return AcceptedPageview(
        page_id=page_id,
        logical_path="/coloring-page/" + page_id,
    )


def reporting_date_bounds(
    now: datetime,
    period: str,
) -> tuple[date | None, date]:
    """Return inclusive Europe/Berlin calendar-day bounds.

    today = current local calendar day.
    7d    = today plus the six preceding local calendar days.
    30d   = today plus the 29 preceding local calendar days.
    all   = no lower date bound, through the current local calendar day.

    Calendar dates, not fixed 24-hour durations, deliberately survive DST.
    """
    if not isinstance(now, datetime) or now.tzinfo is None:
        _stop("REPORT_TIME_REQUIRED")
    local_day = now.astimezone(REPORT_TIMEZONE).date()
    if period == "all":
        return None, local_day
    days = PERIOD_DAYS.get(period)
    if days is None:
        _stop("REPORT_PERIOD")
    return local_day - timedelta(days=days - 1), local_day
