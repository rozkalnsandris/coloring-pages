#!/usr/bin/env python3
"""Cross-engine real-media STAGING QA for print basket issue #508.

This test deliberately stubs window.print(). It validates the reviewed
real-media staging/lifecycle path with fresh public print PNGs in Chromium,
Firefox and WebKit, but it is NOT evidence for a native print dialog, Safari,
physical paper, constrained-device memory, LIVE deployment identity or release
approval. Production BOOK_OUTPUT_RELEASE flags remain untouched.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"
PORT = 8765
LOOPBACK = f"http://{HOST}:{PORT}"
TARGET_SHEETS = (1, 2, 5)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=("chromium", "firefox", "webkit"), required=True)
    parser.add_argument("--origin", default="https://ausmalwiese.de")
    return parser.parse_args()


def get_json(url: str, timeout: float = 10.0):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"unexpected HTTP {response.status}: {url}")
        return json.load(response)


def wait_for_server(process: subprocess.Popen[str], timeout: float = 30.0):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"QA server exited early ({process.returncode}): {output}")
        try:
            context = get_json(LOOPBACK + "/qa/context.json", timeout=2)
            if context.get("status") == "STAGING ONLY":
                return context
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"QA server did not become ready: {last_error}")


def sheet_count(entry: object) -> int | None:
    if not isinstance(entry, dict):
        return None
    activity_id = entry.get("id")
    title = entry.get("title")
    if not isinstance(activity_id, str) or not activity_id:
        return None
    if not isinstance(title, str) or not title.strip():
        return None
    if "pages" in entry:
        pages = entry.get("pages")
        if not isinstance(pages, list) or not 1 <= len(pages) <= 5:
            return None
        if any(not isinstance(page, dict) or not isinstance(page.get("print"), str) for page in pages):
            return None
        return len(pages)
    return 1 if isinstance(entry.get("print"), str) else None


def eligible_entries(catalog: object):
    if not isinstance(catalog, list):
        raise RuntimeError("catalogue must be an array")
    counts = {}
    for entry in catalog:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            counts[entry["id"]] = counts.get(entry["id"], 0) + 1
    values = []
    for entry in catalog:
        count = sheet_count(entry)
        activity_id = entry.get("id") if isinstance(entry, dict) else None
        if count and counts.get(activity_id) == 1:
            values.append((activity_id, count))
    if not values:
        raise RuntimeError("no eligible public print activities")
    return values


def choose_case(entries, target: int):
    # Prefer fewer activities (including atomic multi-page activities), then
    # deterministic catalogue order. The browser receipt records exact IDs and
    # actual PNG orientations for reproducibility.
    bounded = entries[:120]
    for size in range(1, min(5, len(bounded)) + 1):
        for combo in itertools.combinations(bounded, size):
            if sum(item[1] for item in combo) == target:
                return [item[0] for item in combo]
    raise RuntimeError(f"no public activity combination for {target} sheet(s)")


def wait_status(page, prefixes, timeout=120_000):
    page.wait_for_function(
        """prefixes => {
          const value = document.querySelector('#qa-status')?.textContent || '';
          return prefixes.some(prefix => value.startsWith(prefix));
        }""",
        arg=prefixes,
        timeout=timeout,
    )
    value = page.locator("#qa-status").inner_text()
    if value.startswith("FAIL/BLOCKED:"):
        raise AssertionError(value)
    return value


def receipt(page):
    raw = page.locator("#qa-evidence").inner_text().strip()
    if not raw:
        raise AssertionError("QA receipt missing")
    return json.loads(raw)


def validate_receipt(value, target):
    if value.get("schema") != "ausmalwiese.book-real-media-qa-receipt.v1":
        raise AssertionError(f"unexpected receipt schema: {value.get('schema')}")
    outcome = value.get("outcome") or {}
    public = value.get("evidence") or {}
    if outcome.get("result") != "STAGING PASS":
        raise AssertionError(f"unexpected outcome: {outcome}")
    if public.get("totalSheetCount") != target:
        raise AssertionError(f"sheet-count mismatch: {public.get('totalSheetCount')} != {target}")
    return public


def run_browser(browser_name: str, context_info):
    from playwright.sync_api import sync_playwright

    catalog = get_json(LOOPBACK + "/catalog.json", timeout=20)
    entries = eligible_entries(catalog)
    cases = {target: choose_case(entries, target) for target in TARGET_SHEETS}

    with sync_playwright() as driver:
        browser_type = getattr(driver, browser_name)
        browser = browser_type.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.add_init_script(
                """() => {
                  globalThis.__qaPrintCalls = 0;
                  globalThis.print = () => { globalThis.__qaPrintCalls += 1; };
                }"""
            )
            page.goto(LOOPBACK + "/qa/", wait_until="domcontentloaded")
            user_agent = page.evaluate("navigator.userAgent")

            print(
                "ENV",
                json.dumps(
                    {
                        "browserEngine": browser_name,
                        "browserVersion": browser.version,
                        "userAgent": user_agent,
                        "sourceSha": context_info.get("sourceSha"),
                        "publicOrigin": context_info.get("publicOrigin"),
                        "status": "STAGING ONLY",
                    },
                    sort_keys=True,
                ),
            )

            for target, ids in cases.items():
                page.goto(LOOPBACK + "/qa/", wait_until="domcontentloaded")
                page.evaluate("globalThis.__qaPrintCalls = 0")
                page.locator("#qa-ids").fill(" ".join(ids))

                page.locator("#qa-validate").click()
                validate_status = wait_status(page, ("STAGING CHECK:", "FAIL/BLOCKED:"))
                validated = validate_receipt(receipt(page), target)
                media = validated.get("publicMedia") or []
                if len(media) != target:
                    raise AssertionError(f"public-media count mismatch for {target}: {len(media)}")
                orientations = [item.get("orientation") for item in media]
                if any(value not in ("portrait", "landscape") for value in orientations):
                    raise AssertionError(f"invalid orientation evidence: {orientations}")
                for item in media:
                    if item.get("httpStatus") != 200 or item.get("mime") != "image/png":
                        raise AssertionError(f"invalid media receipt: {item}")
                    if (item.get("width"), item.get("height")) not in (
                        (2480, 3508),
                        (3508, 2480),
                    ):
                        raise AssertionError(f"non-canonical A4 geometry: {item}")

                page.locator("#qa-print").click()
                print_status = wait_status(
                    page,
                    ("STAGING PRINT DIALOG CLOSED:", "FAIL/BLOCKED:"),
                )
                staged = validate_receipt(receipt(page), target)
                calls = page.evaluate("globalThis.__qaPrintCalls")
                if calls != 1:
                    raise AssertionError(f"expected one explicit print call, got {calls}")
                if staged.get("totalSheetCount") != target:
                    raise AssertionError("staged sheet count changed")

                print(
                    "PASS",
                    json.dumps(
                        {
                            "targetSheets": target,
                            "activityIds": ids,
                            "orientations": orientations,
                            "validateStatus": validate_status,
                            "printStatus": print_status,
                            "printCalls": calls,
                            "evidenceClass": "STAGING ONLY",
                        },
                        sort_keys=True,
                    ),
                )
        finally:
            browser.close()


def main():
    args = parse_args()
    gate = (ROOT / "js/book-output-release-gate.mjs").read_text(encoding="utf-8")
    if "combinedPrint: false" not in gate or "coveredZip: false" not in gate:
        raise SystemExit("STOP: production release flags are not fail-closed")

    command = [
        sys.executable,
        str(ROOT / "tools/print-basket-real-media-qa-server.py"),
        "--origin",
        args.origin,
        "--port",
        str(PORT),
        "--repo-root",
        str(ROOT),
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    try:
        context = wait_for_server(process)
        run_browser(args.browser, context)
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
