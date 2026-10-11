"""Source-only landscape print native A4 ink fit and safety tests."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is required")
class LandscapeInkFitTests(unittest.TestCase):
    def test_native_scale_and_clearance(self):
        harness = r"""
const fs=require("fs"),vm=require("vm");
const source=fs.readFileSync("js/print.js","utf8").replace(/\nloadPrintPage\(\);\s*$/,"");
const context={document:{querySelector(){return null}},
  window:{location:{search:""},origin:"https://example.org"},
  URLSearchParams,Uint8ClampedArray,console};
vm.runInNewContext(source+"\nglobalThis.api={visibleInkBounds,fitLandscapeInkBounds,applyLandscapeInkFit};",context);
const {visibleInkBounds,fitLandscapeInkBounds,applyLandscapeInkFit}=context.api;
function check(x,m){if(!x)throw Error(m)}
const data=new Uint8ClampedArray(6*5*4).fill(255);
function ink(x,y,r,g,b){let i=(y*6+x)*4;data[i]=r;data[i+1]=g;data[i+2]=b}
ink(1,2,0,0,0);ink(4,3,45,180,200);
let test={width:6,height:5,getContext(){return {getImageData(){return {data}}}}};
let bounds=visibleInkBounds(test);
check(bounds.left===1&&bounds.right===4&&bounds.top===2&&bounds.bottom===3,"ink bbox");
let blank={width:6,height:5,getContext(){return {getImageData(){return {data:new Uint8ClampedArray(120).fill(255)}}}}};
check(visibleInkBounds(blank)===null,"blank should keep fallback");
function within(ink,fit) {
  let x=297/3508,y=210/2480;
  check(ink.left*x*fit.scale+fit.offsetX>=16.99,"left 2mm guard");
  check((ink.right+1)*x*fit.scale+fit.offsetX<=280.01,"right 2mm guard");
  check(ink.top*y*fit.scale+fit.offsetY>=16.99,"top 2mm guard");
  check((ink.bottom+1)*y*fit.scale+fit.offsetY<=169.01,"footer gap");
}
const police={left:199,top:536,right:3306,bottom:1945};
const good=fitLandscapeInkBounds(police,3508,2480);
const width=(police.right-police.left+1)*(297/3508)*good.scale;
check(good.scale<=1&&good.scale>0.99&&width>260,"police should print >260mm without upscale");
within(police,good);
const tall={left:190,top:177,right:3330,bottom:2330};
const reduced=fitLandscapeInkBounds(tall,3508,2480);
check(reduced.scale<0.85,"tall ink must shrink to clear footer");
within(tall,reduced);
check(fitLandscapeInkBounds(police,1024,1536)===null,"portrait unchanged");
check(fitLandscapeInkBounds(police,1500,1000)===null,"legacy unchanged");
const events=[], sheet={style:{setProperty(n,v){events.push(n+v)}},classList:{add(v){events.push(v)}}};
const blocked={width:3508,height:2480,getContext(){throw Error("blocked")}};
applyLandscapeInkFit(sheet,blocked);
check(events.length===0,"readback failure keeps old contain");
console.log("LANDSCAPE_INK_FIT=PASS");
"""
        result = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("LANDSCAPE_INK_FIT=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
