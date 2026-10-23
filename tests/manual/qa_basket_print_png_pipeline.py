#!/usr/bin/env python3
"""Offline Chromium end-to-end PNG preflight for print basket issue #206.

Every PNG is a newly generated, fully decodable 8-bit RGB native-A4 test
image. A local Playwright route serves ONLY those PNG bytes, a synthetic
catalogue, and actual checked-out JS modules. There is no public internet,
production media, source PNG write, actual print click or LIVE access.

Exercises real fetch streams, canonical PNG CRC/dimensions, ImageBitmap decode,
ordered A4 canvas/footer staging, Chromium PDF mixed-orientation page sizes,
and cleanup. Repeats a mixed A4 stage/PDF/dispose cycle within one Chromium
page to catch stale canvases or print-page duplication between requests.
This is NOT mobile-memory, production-image, Firefox PDF, physical
printer, visitor button, or real LIVE evidence. A 375px viewport is
only browser emulation; not a physical-phone or mobile-memory test.
"""
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
import json
import struct
import zlib

from pypdf import PdfReader
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "http://ausmalwiese.invalid"
A4 = {"P": (2480, 3508), "L": (3508, 2480)}
PAPER = {"P": (595.28, 841.89), "L": (841.89, 595.28)}
HTML = (
    '<!doctype html><html lang="de"><head><meta charset="utf-8"></head>'
    '<body class="print-page"><main class="print-shell">'
    '<div class="print-pages" data-print-pages></div></main></body></html>'
)
CATALOG = [
    {"id": "cut-1", "title": "A4 Testaktivität", "pages": [
        {"print": "/media/cut-1/print-1.png"},
        {"print": "/media/cut-1/print-2.png"},
    ]},
    {"id": "flower-2", "title": "A4 Testblume",
     "print": "/media/flower-2/print.png"},
    {"id": "forest-3", "title": "A4 Testwald", "pages": [
        {"print": "/media/forest-3/print-1.png"},
        {"print": "/media/forest-3/print-2.png"},
    ]},
]
PATHS = [
    "/media/cut-1/print-1.png",
    "/media/cut-1/print-2.png",
    "/media/flower-2/print.png",
    "/media/forest-3/print-1.png",
    "/media/forest-3/print-2.png",
]
ORIENTATIONS = "PLPLP"
CASES = [
    ("P", ["flower-2"], [2]),
    ("PLP", ["cut-1", "flower-2"], [0, 1, 2]),
    ("PLPLP", ["cut-1", "flower-2", "forest-3"], [0, 1, 2, 3, 4]),
]

# No Pillow, external fixtures, third-party PNG, binary checkout, or CDN.
def png_chunk(name, payload):
    chunk = name + payload
    return (struct.pack(">I", len(payload)) + chunk +
            struct.pack(">I", zlib.crc32(chunk) & 0xffffffff))


def valid_a4_png(orientation, marker):
    width, height = A4[orientation]
    row = bytearray(b"\xff" * (1 + width * 3))
    row[0] = 0  # standard no-filter scanline
    marked = bytearray(row)
    x0 = 200 + 200 * marker
    marked[1 + 3 * x0:1 + 3 * (x0 + 90)] = b"\0" * (90 * 3)
    compressor = zlib.compressobj(level=2)
    packed = bytearray()
    for y in range(height):
        packed.extend(compressor.compress(marked if 295 <= y < 345 else row))
    packed.extend(compressor.flush())
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) +
            png_chunk(b"IDAT", packed) + png_chunk(b"IEND", b""))


# Real browser imports fetch actual linked JS modules from checked-out source.
# Every request is served locally or blocked; none can reach the public site.
def serve(route, pngs, requests, missing=None, corrupt=None):
    url = route.request.url
    path = urlsplit(url).path
    if not url.startswith(ORIGIN + "/"):
        route.abort()
    elif path == "/":
        route.fulfill(status=200, content_type="text/html", body=HTML)
    elif path == "/catalog.json":
        requests.append(path)
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps(CATALOG))
    elif path in pngs:
        requests.append(path)
        if path == missing:
            route.fulfill(status=404, content_type="text/plain", body="missing")
        else:
            data = pngs[path]
            if path == corrupt:
                data = bytearray(data)
                data[42] ^= 1  # IDAT byte changed, original CRC unchanged
                data = bytes(data)
            route.fulfill(status=200, content_type="image/png", body=data)
    elif path.startswith("/js/") and path.endswith(".mjs"):
        asset = (ROOT / path.lstrip("/")).resolve()
        if asset.is_relative_to((ROOT / "js").resolve()) and asset.is_file():
            route.fulfill(status=200, content_type="text/javascript",
                          body=asset.read_text(encoding="utf-8"))
        else:
            route.abort()
    else:
        route.abort()


STAGE = r"""
async ({ids, indices, failed, drift, abortMedia}) => {
  const {reconcileBasket} = await import('/js/print-basket-selection.mjs');
  const {stageCurrentBasketPrintSession} =
    await import('/js/print-basket-print-session.mjs');
  const catalog = [
    {id:'cut-1',title:'A4 Testaktivität',pages:[
      {print:'/media/cut-1/print-1.png'},
      {print:'/media/cut-1/print-2.png'}]},
    {id:'flower-2',title:'A4 Testblume',print:'/media/flower-2/print.png'},
    {id:'forest-3',title:'A4 Testwald',pages:[
      {print:'/media/forest-3/print-1.png'},
      {print:'/media/forest-3/print-2.png'}]},
  ];
  const basket = reconcileBasket(ids, catalog);
  const host = document.querySelector('[data-print-pages]');
  if (basket.droppedIds.length || basket.sheetCount !== indices.length) {
    throw Error('Bad test selection');
  }
  let staged;
  const controller = new AbortController();
  let reads = 0;
  // Deliberately change the second tab-scoped snapshot read only AFTER
  // the whole staged media set is decoded; it must reject before DOM mount.
  const readIds = () => {
    reads++;
    return drift && reads > 1 ? [...ids].reverse() : [...ids];
  };
  // Abort immediately after the first PNG fetch resolves, before any
  // streaming/decode/mount. The real fetch and signal still take effect.
  const fetcher = async (url, options) => {
    const response = await fetch(url, options);
    if (abortMedia && url.endsWith('/media/cut-1/print-1.png')) {
      controller.abort();
    }
    return response;
  };
  try {
    staged = await stageCurrentBasketPrintSession(basket, {
      origin: location.origin, readIds, fetcher, signal: controller.signal,
    });
    if (failed) throw Error('invalid PNG was incorrectly accepted');
    if (staged.plan.sheetCount !== indices.length) throw Error('Sheet count');
    host.replaceChildren(...staged.sheets.map(sheet => sheet.element));
    const values = staged.sheets.map((sheet, i) => {
      const canvas = sheet.element.querySelector('canvas');
      const ctx = canvas.getContext('2d');
      const x = 220 + indices[i] * 200;
      const pixel = [...ctx.getImageData(x, 310, 1, 1).data];
      const white = [...ctx.getImageData(10, 10, 1, 1).data];
      return {
        orientation: sheet.orientation,
        nativePixels: [canvas.width, canvas.height],
        marker: pixel.slice(0, 3).every(color => color === 0),
        white: white.slice(0, 3).every(color => color === 255),
        label: sheet.element.getAttribute('aria-label'),
      };
    });
    window.__disposeA4 = () => staged.dispose();
    return {failed:false, values};
  } catch (error) {
    staged?.dispose();
    if (!failed || host.childElementCount !== 0) throw error;
    return {failed:true, message:String(error), children:host.childElementCount};
  }
}
"""


def case(browser, css, pngs, sequence, ids, indices, missing=None,
         corrupt=None, drift=False, abort_media=False, viewport_width=1280,
         repeat_after_dispose=False):
    page = browser.new_page(viewport={"width": viewport_width, "height": 800})
    page.set_default_timeout(90000)
    requests = []
    page.route("**/*", lambda route: serve(route, pngs, requests, missing, corrupt))
    try:
        page.goto(ORIGIN + "/", wait_until="load")
        page.add_style_tag(content=css)
        failed = missing is not None or corrupt is not None or drift or abort_media
        result = page.evaluate(STAGE, {
            "ids": ids, "indices": indices, "failed": failed,
            "drift": drift, "abortMedia": abort_media,
        })
        expected_paths = [PATHS[index] for index in indices]
        # HTTP 404 and explicit abort stop at their first failing PNG;
        # CRC failure and late selection drift happen after all PNG fetches.
        expected_downloads = (
            expected_paths[:expected_paths.index(missing)+1] if missing
            else expected_paths[:1] if abort_media
            else expected_paths
        )
        if requests != ["/catalog.json"] + expected_downloads:
            raise AssertionError(f"unexpected requests {requests}")
        if failed:
            if result.get("failed") is not True or result["children"]:
                raise AssertionError("failed session must not mount any pages")
            message = result["message"]
            if corrupt and "CRC" not in message:
                raise AssertionError("corrupt PNG must be rejected by CRC validation")
            if drift and "selection changed" not in message.lower():
                raise AssertionError("late basket change must invalidate staged media")
            if abort_media and "abort" not in message.lower():
                raise AssertionError("abort must invalidate the entire media session")
            reason = ("CRC" if corrupt else "missing" if missing else
                      "selection drift" if drift else "abort")
            print(f"PASS native PNG failure: {reason} prevents partial stage")
            return
        if result.get("failed") or len(result.get("values", [])) != len(sequence):
            raise AssertionError(f"incomplete browser stage: {result}")
        for i, value in enumerate(result["values"]):
            letter = sequence[i]
            if value["orientation"] != ("P" == letter and "portrait" or "landscape"):
                raise AssertionError(f"orientation mismatch on sheet {i+1}")
            if value["nativePixels"] != list(A4[letter]) or not (
                value["marker"] and value["white"]
            ):
                raise AssertionError(f"decoded PNG pixel identity lost: {value}")
            if value["label"] != f"A4-Druckseite {i+1} von {len(sequence)}":
                raise AssertionError("print sheet order label drift")
        page.emulate_media(media="print")
        pdf = PdfReader(BytesIO(page.pdf(
            print_background=True, prefer_css_page_size=True,
        )))
        if len(pdf.pages) != len(sequence):
            raise AssertionError(f"expected {len(sequence)} print pages")
        for i, sheet in enumerate(pdf.pages):
            media_box = (float(sheet.mediabox.width), float(sheet.mediabox.height))
            if any(abs(a - b) > 1 for a, b in zip(
                media_box, PAPER[sequence[i]],
            )):
                raise AssertionError(f"page {i+1} is not correct A4: {media_box}")
            text = sheet.extract_text() or ""
            if "Noch mehr Ausmalbilder?" not in text or "ausmalwiese.de" not in text:
                raise AssertionError(f"missing text footer on page {i+1}")
        page.evaluate("window.__disposeA4()")
        if not page.evaluate(
            "[...document.querySelectorAll('canvas')].every("
            "c => c.width === 0 && c.height === 0)"
        ):
            raise AssertionError("native canvas not cleared after disposal")
        if repeat_after_dispose:
            # Keep the first document's zero-sized canvases as references even
            # after the second stage replaces the visible sheet collection.
            page.evaluate(
                "window.__previousA4 = [...document.querySelectorAll('canvas')]"
            )
            second = page.evaluate(STAGE, {
                "ids": ids, "indices": indices, "failed": False,
                "drift": False, "abortMedia": False,
            })
            if second.get("failed") or second.get("values") != result["values"]:
                raise AssertionError(
                    f"repeat stage changed ordered A4 pixels/sheets: {second}"
                )
            if requests != 2 * (["/catalog.json"] + expected_downloads):
                raise AssertionError(f"repeat stage did not revalidate PNGs: {requests}")
            if not page.evaluate(
                "window.__previousA4.every(c => c.width === 0 && c.height === 0)"
            ):
                raise AssertionError("prior print session retained native canvases")
            pdf_again = PdfReader(BytesIO(page.pdf(
                print_background=True, prefer_css_page_size=True,
            )))
            if len(pdf_again.pages) != len(sequence):
                raise AssertionError("repeat stage duplicated or omitted print sheets")
            for i, sheet in enumerate(pdf_again.pages):
                box = (float(sheet.mediabox.width), float(sheet.mediabox.height))
                if any(abs(a - b) > 1 for a, b in zip(box, PAPER[sequence[i]])):
                    raise AssertionError(f"repeat stage page {i+1} A4 mismatch: {box}")
                words = sheet.extract_text() or ""
                if ("Noch mehr Ausmalbilder?" not in words or
                        "ausmalwiese.de" not in words):
                    raise AssertionError(f"repeat stage page {i+1} footer missing")
            page.evaluate("window.__disposeA4()")
            if not page.evaluate(
                "[...document.querySelectorAll('canvas')].every("
                "c => c.width === 0 && c.height === 0)"
            ):
                raise AssertionError("repeated session did not release canvases")
            print(f"PASS repeat staging: {sequence}, new PNG preflight, "
                  "stable A4 order/footers, both canvas sets disposed")
        print(f"PASS decoded RGB PNGs: {sequence}, {len(sequence)} full-A4 pages, "
              f"{viewport_width}px viewport")
    finally:
        page.close()


def main():
    css = (ROOT / "css/app.css").read_text(encoding="utf-8")
    pngs = {
        path: valid_a4_png(ORIENTATIONS[i], i)
        for i, path in enumerate(PATHS)
    }
    assert all(0 < len(data) < 1024 * 1024 for data in pngs.values())
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        try:
            for viewport_width in (1280, 375):
                for sequence, ids, indices in CASES:
                    case(browser, css, pngs, sequence, ids, indices,
                         viewport_width=viewport_width)
            case(browser, css, pngs, "PLP", CASES[1][1], CASES[1][2],
                 missing=PATHS[1], viewport_width=375)
            case(browser, css, pngs, "PLP", CASES[1][1], CASES[1][2],
                 corrupt=PATHS[1], viewport_width=375)
            case(browser, css, pngs, "PLP", CASES[1][1], CASES[1][2],
                 drift=True, viewport_width=375)
            case(browser, css, pngs, "PLP", CASES[1][1], CASES[1][2],
                 abort_media=True, viewport_width=375)
            case(browser, css, pngs, "PLP", CASES[1][1], CASES[1][2],
                 repeat_after_dispose=True, viewport_width=375)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
