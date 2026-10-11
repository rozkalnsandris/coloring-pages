"""Regression checks for the source-only Ausmalwiese #168 print footer."""
import re
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PrintBrandingTests(unittest.TestCase):
    def test_approved_a4_footer_geometry_and_print_only(self):
        css = (ROOT / "css/app.css").read_text(encoding="utf-8")
        js = (ROOT / "js/print.js").read_text(encoding="utf-8")
        block = css[css.index("/* #168 – print-only"):css.index("/* Cloudflare-backed")]
        for invariant in (
            "left: 15mm;", "right: 15mm;", "bottom: 15mm;", "height: 22mm;",
            "top: 2mm;", "width: 20mm;", "height: 20mm;",
            "bottom: 39mm;", "top: 15mm;",
        ):
            self.assertIn(invariant, block)
        self.assertIn(".print-sheet .print-artwork {", block)
        self.assertNotIn(".print-sheet.has-brand-qr .print-artwork", block)
        self.assertNotIn("bottom: 3mm;", block)
        self.assertNotIn("height: 10mm;", block)
        self.assertNotIn(".print-branding.text-only .print-brand-prompt", block)
        self.assertIn("PRINT_QR_ROUTE_VERIFIED = true", js)
        self.assertIn('withQr ? "Einfach scannen!" : "auf ausmalwiese.de"', js)
        self.assertIn("buildPrintBrandFooter(qrReady)", js)
        self.assertIn("object-fit: contain", block)
        self.assertIn("margin-left: -4px;", block)
        self.assertIn("https://ausmalwiese.de/q", js)
        self.assertNotIn("ausmalwiese-qr-dots", (ROOT / "js/detail.js").read_text())
        self.assertNotIn("ausmalwiese-qr-dots", (ROOT / "tools/coloring-pages-import").read_text())

    def test_qr_svg_has_quiet_zone_and_dots_without_frame(self):
        root = ET.fromstring((ROOT / "assets/ausmalwiese-qr-dots.svg").read_text())
        self.assertEqual(root.attrib["viewBox"], "0 0 37 37")
        self.assertEqual(root.attrib["width"], "20mm")
        self.assertEqual(root.attrib["height"], "20mm")
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertIn("https://ausmalwiese.de/q", root.findtext("s:title", namespaces=ns))
        circles = root.findall(".//s:circle", ns)
        self.assertGreater(len(circles), 100)
        for circle in circles:
            x, y = float(circle.attrib["cx"]), float(circle.attrib["cy"])
            r = float(circle.attrib["r"])
            self.assertGreaterEqual(x - r, 4)
            self.assertGreaterEqual(y - r, 4)
            self.assertLessEqual(x + r, 33)
            self.assertLessEqual(y + r, 33)
        filled = [
            el for el in root.findall(".//s:rect", ns)
            if el.attrib.get("fill") != "#fff"
        ]
        self.assertTrue(filled)
        self.assertGreaterEqual(min(int(el.attrib["x"]) for el in filled), 4)
        self.assertLessEqual(max(int(el.attrib["x"]) for el in filled), 32)

    def test_multipage_artwork_wrapped_and_clean_fallback(self):
        if not shutil.which("node"):
            self.skipTest("Node needed for print DOM source test")
        harness = r"""
const fs = require("fs"), vm = require("vm");
const source = fs.readFileSync("js/print.js", "utf8").replace(/\nloadPrintPage\(\);\s*$/, "");
const pages = { children: [], replaceChildren(...els) { this.children=els; }};
const q = { "[data-print-pages]": pages, "[data-print-button]": { addEventListener(){} }};
const canvases = [];
function makeElement(tag) {
  const e = {tag, children: [], attrs:{}, className:"",
    classList: {add(v){e.className+=" "+v}},
    setAttribute(k,v){e.attrs[k]=v},
    append(...v){e.children.push(...v)},
    getContext() {return {clearRect(){},drawImage(){}}}
  };
  if(tag==="canvas")canvases.push(e);
  return e;
}
const document={querySelector:(s)=>q[s]||null,createElement:makeElement};
let qrLoadFails=false;
class ImageMock {set src(url){this.naturalWidth=url==="landscape"?3508:2480;this.naturalHeight=url==="landscape"?2480:3508;queueMicrotask(()=>url==="assets/ausmalwiese-qr-dots.svg"&&qrLoadFails?this.onerror():this.onload())}};
const window={location:{search:""},parent:null,addEventListener(){},print(){},origin:"https://example.org"};
window.parent=window;
const context={document,window,Image:ImageMock,URLSearchParams};
vm.runInNewContext(source+"\nglobalThis.run = renderPrintImages;",context);
context.run(["portrait","landscape"]).then(async()=>{
 const sheets=pages.children;
 if(sheets.length!==2)throw Error("multi-page count");
 if(!sheets[0].className.includes("is-portrait") || !sheets[1].className.includes("is-landscape")) throw Error("orientation");
 if(!sheets.every(s=>s.className.includes("has-brand-qr")))throw Error("QR-enabled sheet class");
 if(!sheets.every(s=>s.children[0].className==="print-artwork"))throw Error("artwork wrapper");
 if(!sheets.every(s=>s.children[1].className.includes("has-qr")))throw Error("QR-enabled footer");
 if(!sheets.every(s=>s.children[1].innerHTML.includes("Einfach scannen!")))throw Error("QR scan CTA");
 if(!sheets.every(s=>s.children[1].children.some(x=>x.tag==="img"&&x.src==="assets/ausmalwiese-qr-dots.svg")))throw Error("shared QR SVG missing");
 if(canvases.length!==2 || canvases[0].width!==2480 || canvases[0].height!==3508 || canvases[1].width!==3508 || canvases[1].height!==2480)throw Error("canonical pixel geometry");
 qrLoadFails=true;
 await context.run(["portrait","landscape"]);
 if(!pages.children.every(s=>s.className.includes("has-text-footer")))throw Error("QR asset failure sheet fallback");
 if(!pages.children.every(s=>s.children[1].className.includes("text-only")))throw Error("QR asset failure footer fallback");
 if(!pages.children.every(s=>s.children[1].innerHTML.includes("auf ausmalwiese.de")))throw Error("honest fallback CTA");
 if(!pages.children.every(s=>!s.children[1].children.some(x=>x.tag==="img")))throw Error("QR visible after asset failure");
 console.log("PASS");
}).catch(e=>{console.error(e);process.exitCode=1});
"""
        outcome = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(outcome.returncode, 0, outcome.stderr)
        self.assertIn("PASS", outcome.stdout)


if __name__ == "__main__":
    unittest.main()
