"""Source-only portrait and landscape A4 ink placement safety tests."""
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
vm.runInNewContext(source+"\nglobalThis.api={visibleInkBounds,fitA4InkBounds,applyA4InkFit};",context);
const {visibleInkBounds,fitA4InkBounds,applyA4InkFit}=context.api;
function check(x,m){if(!x)throw Error(m)}
const data=new Uint8ClampedArray(6*5*4).fill(255);
function ink(x,y,r,g,b){let i=(y*6+x)*4;data[i]=r;data[i+1]=g;data[i+2]=b}
ink(1,2,0,0,0);ink(4,3,45,180,200);
let test={width:6,height:5,getContext(){return {getImageData(){return {data}}}}};
let bounds=visibleInkBounds(test);
check(bounds.left===1&&bounds.right===4&&bounds.top===2&&bounds.bottom===3,"ink bbox");
let blank={width:6,height:5,getContext(){return {getImageData(){return {data:new Uint8ClampedArray(120).fill(255)}}}}};
check(visibleInkBounds(blank)===null,"blank should keep fallback");
function within(ink,fit,width=3508,height=2480) {
  const landscape=width>height, pw=landscape?297:210, ph=landscape?210:297;
  const x=pw/width,y=ph/height;
  check(ink.left*x*fit.scale+fit.offsetX>=16.99,"left 2mm guard");
  check((ink.right+1)*x*fit.scale+fit.offsetX<=pw-16.99,"right 2mm guard");
  check(ink.top*y*fit.scale+fit.offsetY>=16.99,"top 2mm guard");
  check((ink.bottom+1)*y*fit.scale+fit.offsetY<=ph-40.99,"footer gap");
}
const police={left:199,top:536,right:3306,bottom:1945};
const good=fitA4InkBounds(police,3508,2480);
const width=(police.right-police.left+1)*(297/3508)*good.scale;
check(good.scale<=1&&good.scale>0.99&&width>260,"police should print >260mm without upscale");
within(police,good);
const tall={left:190,top:177,right:3330,bottom:2330};
const reduced=fitA4InkBounds(tall,3508,2480);
check(reduced.scale<0.85,"tall ink must shrink to clear footer");
within(tall,reduced);
const portrait={left:350,top:410,right:2080,bottom:3100};
const portraitFit=fitA4InkBounds(portrait,2480,3508);
check(portraitFit.scale===1,"portrait should keep full physical A4 scale");
within(portrait,portraitFit,2480,3508);
const tallPortrait={left:177,top:177,right:2300,bottom:3390};
const reducedPortrait=fitA4InkBounds(tallPortrait,2480,3508);
check(reducedPortrait.scale<0.9,"tall portrait ink must clear footer");
within(tallPortrait,reducedPortrait,2480,3508);
check(fitA4InkBounds(police,1024,1536)===null,"legacy portrait unchanged");
check(fitA4InkBounds(police,1500,1000)===null,"legacy unchanged");
const events=[], sheet={style:{setProperty(n,v){events.push(n+v)}},classList:{add(v){events.push(v)}}};
const blocked={width:3508,height:2480,getContext(){throw Error("blocked")}};
applyA4InkFit(sheet,blocked);
check(events.length===0,"readback failure keeps old contain");
console.log("A4_INK_FIT_BOTH=PASS");
"""
        result = subprocess.run(
            ["node", "-e", harness], cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("A4_INK_FIT_BOTH=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
