#!/usr/bin/env python3
"""WebKit synthetic print-CSS layout QA for #508; NOT Safari/print-to-file evidence.

Requires Playwright 1.64.0 and the installed Playwright-managed WebKit browser.
    python3 -m playwright install --with-deps webkit
    python3 tests/manual/qa_basket_print_webkit.py

Loads the checked-out print CSS and A4 canvas/footer JS modules using locally
generated in-memory native-A4 test images. Checks Playwright WebKit print media layout,
mixed orientation, safe artwork/footer geometry and resource cleanup.
No network requests, real published PNGs, print job, PDF, LIVE, or UI activation.
The actual Safari/WebKit print preview, paper/PDF page count, and print margins must
still be independently inspected before enabling visitor printing.
"""
import argparse
from pathlib import Path

from qa_basket_print_layout import ROOT

DRAW_WEBKIT = r"""
async ({canvasSource, footerSource, sequence}) => {
  const load = (source, names) => {
    const body = source.replaceAll('export ', '');
    return Function(body + '\nreturn {' + names.join(',') + '};')();
  };
  const {stageBasketPrintCanvases} = load(canvasSource, ['stageBasketPrintCanvases']);
  const {stageBasketPrintTextFooters} = load(footerSource, ['stageBasketPrintTextFooters']);
  const sizes = {P:[2480,3508], L:[3508,2480]};
  const pages = [...sequence].map((orientation,i) => ({
    activityId:'qa-only', pageIndex:i+1, pageCount:sequence.length,
    printUrl:'/media/qa-only/print-'+(i+1)+'.png',
  }));
  const bitmaps = [];
  const sheets = [];
  try {
    for (const [i,orientation] of [...sequence].entries()) {
      const [width,height] = sizes[orientation];
      const source = document.createElement('canvas');
      source.width=width; source.height=height;
      const ctx=source.getContext('2d',{alpha:false});
      ctx.fillStyle='#fff'; ctx.fillRect(0,0,width,height);
      ctx.lineWidth=8; ctx.strokeStyle='#000';
      ctx.strokeRect(230,250,width-460,height-740);
      ctx.fillStyle='#000'; ctx.font='45px sans-serif';
      ctx.fillText('A4 QA '+(i+1)+' '+orientation,260,350);
      const bitmap=await createImageBitmap(source);
      bitmaps.push(bitmap); source.width=0; source.height=0;
      sheets.push({
        page:pages[i], width,height,
        orientation:orientation==='P'?'portrait':'landscape',bitmap,
      });
    }
    let released=false;
    const decoded = {
      plan:{pages,imageUrls:pages.map(p=>p.printUrl),sheetCount:pages.length},
      sheets,
      get released(){return released;},
      release(){
        if(released)return;
        released=true;bitmaps.forEach(b=>b.close());
      },
    };
    const canvases=stageBasketPrintCanvases(decoded,{documentRef:document});
    const branded=stageBasketPrintTextFooters(canvases,{documentRef:document});
    document.querySelector('[data-print-pages]')
      .replaceChildren(...branded.sheets.map(x=>x.element));
    window.__qaDispose=()=>branded.dispose();
    return {
      count:branded.sheets.length,
      orientations:branded.sheets.map(s=>s.orientation),
      sizes:branded.sheets.map(s=>{
        const c=s.element.querySelector('canvas');
        return [c.width,c.height];
      }),
      footers:document.querySelectorAll('.print-branding.text-only').length,
      released,
    };
  } finally {
    bitmaps.forEach(b=>{try{b.close();}catch{}});
  }
}
"""

PX_PER_MM = 96 / 25.4
PRINT_LAYOUT = r"""
() => [...document.querySelectorAll('.print-sheet')].map((sheet) => {
  const artwork = sheet.querySelector('.print-artwork');
  const footer = sheet.querySelector('.print-branding.text-only');
  const canvas = artwork && artwork.querySelector('canvas');
  if (!artwork || !footer || !canvas) throw Error('Incomplete staged A4 sheet');
  const rect = element => {
    const b = element.getBoundingClientRect();
    return {left:b.left, right:b.right, top:b.top, bottom:b.bottom,
            width:b.width, height:b.height};
  };
  const box=rect(sheet), art=rect(artwork), brand=rect(footer);
  return {
    orientation: sheet.classList.contains('is-landscape') ? 'L' : 'P',
    box, art, brand,
    footerText:footer.textContent,
    footerDisplay:getComputedStyle(footer).display,
    canvas:[canvas.width,canvas.height],
    label:sheet.getAttribute('aria-label'),
  };
})
"""


def near(actual, expected, label, tolerance=2.0):
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{label}: expected {expected:.2f}px, got {actual:.2f}px")


def verify_sheet(sequence, index, value):
    letter = sequence[index]
    mm_width, mm_height = (297, 210) if letter == "L" else (210, 297)
    box, art, brand = value["box"], value["art"], value["brand"]
    if value["orientation"] != letter:
        raise AssertionError(f"{sequence}: sheet {index+1} orientation differs")
    near(box["width"], mm_width * PX_PER_MM, "A4 page width")
    near(box["height"], mm_height * PX_PER_MM, "A4 page height")
    if value["canvas"] != (
        [3508, 2480] if letter == "L" else [2480, 3508]
    ):
        raise AssertionError(f"{sequence}: native A4 pixels differ on page {index+1}")
    expected_label = f"A4-Druckseite {index+1} von {len(sequence)}"
    if value["label"] != expected_label:
        raise AssertionError(f"{sequence}: page order/ARIA label differs")
    near(art["left"] - box["left"], 15 * PX_PER_MM, "artwork left 15mm")
    near(box["right"] - art["right"], 15 * PX_PER_MM, "artwork right 15mm")
    near(art["top"] - box["top"], 15 * PX_PER_MM, "artwork top 15mm")
    near(box["bottom"] - art["bottom"], 39 * PX_PER_MM, "reserved footer space")
    near(brand["left"] - box["left"], 15 * PX_PER_MM, "footer left 15mm")
    near(box["right"] - brand["right"], 15 * PX_PER_MM, "footer right 15mm")
    near(box["bottom"] - brand["bottom"], 15 * PX_PER_MM, "footer bottom 15mm")
    near(brand["height"], 22 * PX_PER_MM, "footer height 22mm")
    if art["bottom"] > brand["top"] - PX_PER_MM:
        raise AssertionError(f"{sequence}: artwork overlaps text footer")
    if value["footerDisplay"] == "none" or not all(
        part in value["footerText"]
        for part in ("Noch mehr Ausmalbilder?", "ausmalwiese.de")
    ):
        raise AssertionError(f"{sequence}: footer invisible or incomplete")


def run_case(browser, css, canvas_source, footer_source, sequence, viewport_width):
    page = browser.new_page(viewport={"width": viewport_width, "height": 780})
    try:
        page.route("**/*", lambda route: route.abort())  # block site/network
        page.set_content(
            '<!doctype html><html lang="de"><head><meta charset="utf-8">'
            '<style>' + css + '</style></head><body class="print-page">'
            '<main class="print-shell"><div class="print-pages" '
            'data-print-pages></div></main></body></html>',
            wait_until="load",
        )
        page.emulate_media(media="print")
        staged = page.evaluate(DRAW_WEBKIT, {
            "canvasSource": canvas_source, "footerSource": footer_source,
            "sequence": sequence,
        })
        if (staged != {
            "count": len(sequence),
            "orientations": [
                "landscape" if value == "L" else "portrait" for value in sequence
            ],
            "sizes": [
                [3508, 2480] if value == "L" else [2480, 3508]
                for value in sequence
            ],
            "footers": len(sequence), "released": True,
        }):
            raise AssertionError(f"{sequence}: bad staged A4 pages: {staged}")
        boxes = page.evaluate(PRINT_LAYOUT)
        if len(boxes) != len(sequence):
            raise AssertionError(f"{sequence}: wrong number of WebKit DOM sheets")
        for i, value in enumerate(boxes):
            verify_sheet(sequence, i, value)
        page.evaluate("window.__qaDispose()")
        if not page.evaluate(
            "[...document.querySelectorAll('canvas')].every("
            "c=>c.width===0&&c.height===0)"
        ):
            raise AssertionError(f"{sequence}: canvases retained after dispose")
        print(
            f"PASS WebKit print CSS: {sequence} / {len(sequence)} sheets, "
            f"{viewport_width}px viewport, footer and cleanup"
        )
    finally:
        page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--webkit", default=None,
                        help="override Playwright-managed WebKit executable")
    parser.add_argument("--sequences", nargs="+", default=["P", "L", "PP", "LL", "PL", "PPPPP", "LLLLL", "PLPLP"])
    parser.add_argument("--viewports", nargs="+", type=int, default=[375, 1280])
    args = parser.parse_args()
    for sequence in args.sequences:
        if not 1 <= len(sequence) <= 5 or any(ch not in "PL" for ch in sequence):
            parser.error("each test sequence must contain 1-5 P/L A4 sheets")
    for width in args.viewports:
        if width < 320 or width > 1800:
            parser.error("viewport widths must be between 320 and 1800")
    css = (ROOT / "css/app.css").read_text(encoding="utf-8")
    canvas = (ROOT / "js/print-basket-print-canvas.mjs").read_text(encoding="utf-8")
    footer = (ROOT / "js/print-basket-print-footer.mjs").read_text(encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as driver:
        browser = driver.webkit.launch(executable_path=args.webkit)
        try:
            for width in args.viewports:
                for sequence in args.sequences:
                    run_case(browser, css, canvas, footer, sequence, width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
