"""Source-only Cut & Paste vector geometry and A4 ink QA (issue #221).

Limited SVG path vocabulary: absolute M/L/C/Q/Z, one simple closed contour.
Unsupported shapes stop rather than falling back to a cosmetic dashed outline.
"""
import math
import re
from itertools import combinations
from PIL import Image
from shapely import affinity
from shapely.geometry import Point, Polygon, box

TOKENS = re.compile(r"[MLCQZmlcqz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
INK = (17, 17, 193, 256)


def polygon_of(path):
    seq = TOKENS.findall(path)
    if re.sub(r"[\s,]", "", path) != "".join(seq) or not seq or seq[0] != "M" or seq[-1] != "Z":
        raise ValueError("SVG silhouette must be one closed absolute M/L/C/Q/Z contour")
    i, current, points, moves = 0, None, [], 0
    count = {"M": 2, "L": 2, "C": 6, "Q": 4}
    while i < len(seq):
        op = seq[i]
        i += 1
        if op == "Z":
            if i != len(seq):
                raise ValueError("Multiple paths unsupported")
            break
        if op not in count:
            raise ValueError("Unsupported SVG path command")
        if i + count[op] > len(seq) or any(t in "MLCQZmlcqz" for t in seq[i:i+count[op]]):
            raise ValueError("Incomplete SVG path command")
        nums = list(map(float, seq[i:i+count[op]]))
        i += count[op]
        if not all(math.isfinite(x) for x in nums):
            raise ValueError("Invalid path coordinate")
        end = (nums[-2], nums[-1])
        if op == "M":
            moves += 1
            if moves != 1:
                raise ValueError("Multiple contours unsupported")
            points.append(end)
        elif op == "L":
            points.append(end)
        else:
            if current is None:
                raise ValueError("Missing SVG move")
            controls = [(nums[k], nums[k+1]) for k in range(0, len(nums)-2, 2)]
            chain = [current, *controls, end]
            length = sum(math.dist(u,v) for u,v in zip(chain,chain[1:]))
            steps = max(8, min(1024, math.ceil(length/0.12)))
            for j in range(1, steps+1):
                t = j/steps
                s = 1-t
                if op == "C":
                    a,b,c,d = chain
                    points.append((s**3*a[0]+3*s*s*t*b[0]+3*s*t*t*c[0]+t**3*d[0],
                                   s**3*a[1]+3*s*s*t*b[1]+3*s*t*t*c[1]+t**3*d[1]))
                else:
                    a,b,c = chain
                    points.append((s*s*a[0]+2*s*t*b[0]+t*t*c[0],
                                   s*s*a[1]+2*s*t*b[1]+t*t*c[1]))
        current = end
    poly = Polygon(points)
    if moves != 1 or len(points) < 3 or not poly.is_valid or poly.area < 1:
        raise ValueError("Invalid, self-crossing or tiny cut silhouette")
    return poly


def guide_polygon(part):
    p = polygon_of(part["art"]["outer_path_d"])
    guide = p.buffer(part["cut"]["offset_mm"], quad_segs=16, join_style="round")
    if guide.geom_type != "Polygon" or not guide.is_valid or guide.interiors or not guide.covers(p):
        raise ValueError("Outward cut contour cannot be generated")
    return guide


def outline_d(part):
    guide = guide_polygon(part)
    return "M " + " L ".join("%.3f %.3f" % (x,y) for x,y in list(guide.exterior.coords)[:-1]) + " Z"


def place(part, geom):
    t = part["assembly"]
    rad = math.radians(t["rotate_deg"])
    scale = t["scale"]
    c, s = scale*math.cos(rad), scale*math.sin(rad)
    x,y = t["translate_mm"]
    return affinity.affine_transform(geom,[c,-s,s,c,x,y])


def anchor(part, local):
    return place(part, Point(*local))


def validate_cuts(cuts, style):
    outlines = []
    for part,x,y in cuts:
        guide = guide_polygon(part).buffer(style["stroke_width_mm"]/2, quad_segs=8)
        guide = affinity.translate(guide,xoff=x,yoff=y)
        l,t,r,b = guide.bounds
        if l < INK[0]-0.1 or t < INK[1]-0.1 or r > INK[2]+0.1 or b > INK[3]+0.1:
            raise ValueError("Cut guide outside A4 ink box: "+part["id"])
        for prev_name,prev in outlines:
            if prev.distance(guide) < 4:
                raise ValueError("Cut guides too close: "+prev_name+" / "+part["id"])
        outlines.append((part["id"], guide))


def validate_scene(parts, cuts, style, preview_box, origin):
    if list(origin) != [0,0]:
        raise ValueError("Nonzero assembled origin unsupported")
    geom = {p["id"]:polygon_of(p["art"]["outer_path_d"]) for p in parts}
    world = {p["id"]:place(p, geom[p["id"]]) for p in parts}
    by_id = {p["id"]:p for p in parts}
    for p in parts:
        l,t,r,b = geom[p["id"]].bounds
        w,h = p["art"]["size_mm"]
        if l < -0.2 or t < -0.2 or r > w+0.2 or b > h+0.2:
            raise ValueError("Part artwork outside declared dimensions: "+p["id"])
        if p["role"] != "cutout":
            continue
        g = p["glue"]
        target = by_id[g["target_id"]]
        if g["side"]!="front" or target["assembly"]["z_index"]>=p["assembly"]["z_index"]:
            raise ValueError("Glue order is not front-accessible: "+p["id"])
        a,b = anchor(p,g["piece_anchor_mm"]),anchor(target,g["target_anchor_mm"])
        if a.distance(b) > 0.3:
            raise ValueError("Mismatched glue anchors: "+p["id"])
        if world[p["id"]].distance(a)>0.3 or world[target["id"]].distance(b)>0.3:
            raise ValueError("Glue anchor outside its silhouette: "+p["id"])
        if world[p["id"]].intersection(world[target["id"]]).area < g["minimum_contact_area_mm2"]:
            raise ValueError("Insufficient glue contact: "+p["id"])
    assembly = None
    for piece in world.values():
        assembly = piece if assembly is None else assembly.union(piece)
    if assembly.buffer(2).intersects(box(*preview_box)):
        raise ValueError("Finished preview collides with assembly")
    validate_cuts(cuts,style)
    return {"vector_offset":"buffer-of-sampled-original", "cut_gap_mm":4,
            "glue_contact":"checked", "physical_assembly":"PENDING"}


def validate_png(path):
    with Image.open(path) as img:
        if img.format!="PNG" or img.mode!="RGB" or img.size!=(2480,3508):
            raise ValueError("Invalid A4 PNG")
        dpi = img.info.get("dpi")
        if not dpi or any(abs(v-300)>1 for v in dpi):
            raise ValueError("Invalid A4 DPI")
        # JavaScript considers a pixel white iff all RGB channels >=250.
        mask = img.point(lambda v: 0 if v >= 250 else 255)
        rect = mask.getbbox()
    if rect is None:
        raise ValueError("Empty A4 page")
    l,t,r,b = rect
    mm = (l*210/2480,t*297/3508,r*210/2480,b*297/3508)
    if mm[0] < 16.8 or mm[1] < 16.8 or mm[2] > 193.2 or mm[3] > 256.2:
        raise ValueError("A4 footer-safe ink region exceeded")
    return list(mm)
