#!/usr/bin/env python3
"""Optional local Chromium A4 layout QA for #206; NOT a LIVE or CI gate.

Run from a repository checkout after installing locally: playwright, pypdf and
Chromium. Example:
    python3 tests/manual/qa_basket_print_layout.py --chromium /usr/bin/chromium
    python3 tests/manual/qa_basket_print_layout.py --pdf-dir /tmp/a4-qa

Exercises the actual checked-out print CSS, canvas and text-footer modules
on synthetic in-memory 1/3/5-sheet native A4 images; verifies PDF paper sizes,
page order, footer text and disposal. No network, production images or print
button. Cannot substitute for real PNG, Firefox, mobile/physical printer QA.
"""
import argparse
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A4_PT = {"P": (595.28, 841.89), "L": (841.89, 595.28)}
DRAW = r"""
async ({canvasSource, footerSource, sequence}) => {
  const urls = [], bitmaps = [];
  const load = async source => {
    const url = URL.createObjectURL(new Blob([source], {type:'text/javascript'}));
    urls.push(url);
    return import(url);
  };
  try {
    const {stageBasketPrintCanvases} = await load(canvasSource);
    const {stageBasketPrintTextFooters} = await load(footerSource);
    const sizes = {P:[2480,3508], L:[3508,2480]};
    const pages = [...sequence].map((orientation,i) => ({
      activityId:'qa-only', pageIndex:i+1, pageCount:sequence.length,
      printUrl:'/media/qa-only/print-'+(i+1)+'.png',
    }));
    const sheets = [];
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
    urls.forEach(url=>URL.revokeObjectURL(url));
    bitmaps.forEach(b=>{try{b.close();}catch{}});
  }
}
"""


def run_case(browser, css, canvas_source, footer_source, sequence, pdf_dir):
    from pypdf import PdfReader

    page = browser.new_page(viewport={"width": 1280, "height": 800})
    try:
        page.route("**/*", lambda route: route.abort())  # never use network
        page.set_content(
            '<!doctype html><html lang="de"><head><meta charset="utf-8">'
            '<style>' + css + '</style></head><body class="print-page">'
            '<main class="print-shell"><div class="print-pages" '
            'data-print-pages></div></main></body></html>',
            wait_until="load",
        )
        actual = page.evaluate(DRAW, {
            "canvasSource": canvas_source, "footerSource": footer_source,
            "sequence": sequence,
        })
        expected = {
            "count": len(sequence),
            "orientations": ["portrait" if x == "P" else "landscape" for x in sequence],
            "sizes": [[2480, 3508] if x == "P" else [3508, 2480] for x in sequence],
            "footers": len(sequence), "released": True,
        }
        if actual != expected:
            raise AssertionError(f"{sequence}: staged A4 mismatch: {actual}")
        page.emulate_media(media="print")
        pdf_bytes = page.pdf(print_background=True, prefer_css_page_size=True)
        pdf = PdfReader(BytesIO(pdf_bytes))
        if len(pdf.pages) != len(sequence):
            raise AssertionError(
                f"{sequence}: expected {len(sequence)} paper sheets, got {len(pdf.pages)}"
            )
        for index, (orientation, sheet) in enumerate(zip(sequence, pdf.pages), 1):
            got = (float(sheet.mediabox.width), float(sheet.mediabox.height))
            if any(abs(a - b) > 1 for a, b in zip(got, A4_PT[orientation])):
                raise AssertionError(f"{sequence}: page {index} paper mismatch {got}")
            text = sheet.extract_text() or ""
            if "Noch mehr Ausmalbilder?" not in text or "ausmalwiese.de" not in text:
                raise AssertionError(f"{sequence}: page {index} branding missing")
        if pdf_dir is not None:
            (pdf_dir / f"basket-a4-{sequence}.pdf").write_bytes(pdf_bytes)
        page.evaluate("window.__qaDispose()")
        if not page.evaluate(
            "[...document.querySelectorAll('canvas')].every(c=>c.width===0&&c.height===0)"
        ):
            raise AssertionError(f"{sequence}: A4 canvases not released")
        print(f"PASS Chromium: {sequence}, {len(pdf.pages)} A4 pages, footer and cleanup")
    finally:
        page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--no-sandbox", action="store_true",
                        help="only for disposable isolated root containers")
    parser.add_argument("--sequences", nargs="+", default=["P", "PLP", "PLPLP"])
    parser.add_argument("--pdf-dir", type=Path, help="optional local PDFs for visual inspection")
    args = parser.parse_args()
    for sequence in args.sequences:
        if not 1 <= len(sequence) <= 5 or any(ch not in "PL" for ch in sequence):
            parser.error("sequence must contain 1-5 portrait P or landscape L letters")
    css = (ROOT / "css/app.css").read_text(encoding="utf-8")
    canvas = (ROOT / "js/print-basket-print-canvas.mjs").read_text(encoding="utf-8")
    footer = (ROOT / "js/print-basket-print-footer.mjs").read_text(encoding="utf-8")
    if args.pdf_dir is not None:
        args.pdf_dir.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as driver:
        browser = driver.chromium.launch(
            executable_path=args.chromium,
            args=["--no-sandbox"] if args.no_sandbox else [],
        )
        try:
            for sequence in args.sequences:
                run_case(browser, css, canvas, footer, sequence, args.pdf_dir)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
