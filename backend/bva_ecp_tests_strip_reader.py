import sys, numpy as np, cv2, itertools
import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
sys.path.insert(0, os.getcwd())
from app.colorimetry import nearest_reference, extract_pad_color, analyze_strip, read_image_from_bytes
from app.reference_data import REFERENCE_CHART, PAD_POSITIONS

res = []
def rec(i, desc, got, exp, ok): res.append((i, desc, got, exp, ok)); print(i, desc, "|", got, "|", exp, "|", "PASS" if ok else "FAIL")

# ECP: each reference colour maps to itself (representative of every class)
bad = 0; n = 0
for p, opts in REFERENCE_CHART.items():
    for lab, rgb in opts:
        n += 1
        if nearest_reference(rgb, p)["result"] != lab: bad += 1
rec("ECP-1", f"Exact reference colour for all {n} classes (5 params)", f"{n-bad}/{n} correct", "all correct", bad == 0)

# BVA on class boundary: walk along the line between two adjacent reference colours
# and find the exact colour where the result flips, then test the colour on each side of it.
def boundary(param, i, j):
    a = np.array(REFERENCE_CHART[param][i][1], float); b = np.array(REFERENCE_CHART[param][j][1], float)
    prev = None
    for k in range(0, 1001):
        rgb = tuple(int(round(x)) for x in a + (b - a) * (k / 1000))
        r = nearest_reference(rgb, param)["result"]
        if prev and r != prev[1]: return prev, (rgb, r)
        prev = (rgb, r)
(lo_rgb, lo_lab), (hi_rgb, hi_lab) = boundary("pH", 1, 2)
r1 = nearest_reference(lo_rgb, "pH")["result"]; r2 = nearest_reference(hi_rgb, "pH")["result"]
rec("BVA-1", f"pH colour {lo_rgb} (last colour before boundary)", r1, "6.0", r1 == "6.0")
rec("BVA-2", f"pH colour {hi_rgb} (first colour after boundary)", r2, "6.5", r2 == "6.5")
(lo_rgb, lo_lab), (hi_rgb, hi_lab) = boundary("Glucose", 0, 1)
r1 = nearest_reference(lo_rgb, "Glucose")["result"]; r2 = nearest_reference(hi_rgb, "Glucose")["result"]
rec("BVA-3", f"Glucose colour {lo_rgb} (last colour before boundary)", r1, "Negative", r1 == "Negative")
rec("BVA-4", f"Glucose colour {hi_rgb} (first colour after boundary)", r2, "Trace", r2 == "Trace")

# BVA on RGB channel limits
for rgb, name in (((0,0,0), "RGB min (0,0,0)"), ((255,255,255), "RGB max (255,255,255)"), ((1,1,1), "RGB min+1"), ((254,254,254), "RGB max-1")):
    r = nearest_reference(rgb, "pH"); rec("BVA-RGB", name, r["result"], "valid class returned", r["result"] in [l for l, _ in REFERENCE_CHART["pH"]])
for rgb, name in (((256, 256, 256), "RGB 256 (above max, invalid)"), ((-1, -1, -1), "RGB -1 (below min, invalid)")):
    try:
        r = nearest_reference(rgb, "pH"); rec("BVA-RGB", name, f"accepted -> {r['result']}", "rejected / error", False)
    except ValueError as e: rec("BVA-RGB", name, "ValueError raised", "rejected / error", True)

# Image-level inputs
def png(w, h, bgr): 
    img = np.full((h, w, 3), bgr, np.uint8); ok, buf = cv2.imencode(".png", img); return buf.tobytes()
for (w, h) in ((1, 1), (2, 2), (20, 20), (21, 21), (100, 30)):
    try:
        out = analyze_strip(png(w, h, (60, 190, 240))); rec("BVA-IMG", f"Image {w}x{h} px", f"analysed {len(out)} params", "analysed 5 params", len(out) == 5)
    except Exception as e: rec("BVA-IMG", f"Image {w}x{h} px", f"{type(e).__name__}", "analysed 5 params", False)
for name, data in (("Empty bytes", b""), ("Random text bytes", b"not an image"), ("Truncated PNG", png(50, 50, (1,2,3))[:30])):
    try: analyze_strip(data); rec("ECP-INV", name, "no error", "ValueError", False)
    except ValueError as e: rec("ECP-INV", name, "ValueError raised", "ValueError", True)
    except Exception as e: rec("ECP-INV", name, type(e).__name__, "ValueError", False)

# Full strip: build a strip image whose pads are exact reference colours at the pad positions
W, H = 500, 100
img = np.zeros((H, W, 3), np.uint8)
for p, x in PAD_POSITIONS.items():
    rgb = REFERENCE_CHART[p][0][1]
    img[:, int(W*x)-30:int(W*x)+30] = rgb[::-1]
ok, buf = cv2.imencode(".png", img); out = analyze_strip(buf.tobytes())
rec("ECP-FULL", "Synthetic strip, all pads 'Negative'-level colours", ", ".join(f"{k}:{v['result']}" for k, v in out.items()), "all first-level", all(v["result"] == REFERENCE_CHART[k][0][0] for k, v in out.items()))
# Dark / blank image (no strip) still returns a confident result?
for name, bgr in (("All-black image (no strip present)", (0, 0, 0)), ("All-white image (no strip present)", (255, 255, 255))):
    try:
        out = analyze_strip(png(500, 100, bgr)); rec("ERR-GUESS", name, ", ".join(f"{k}:{v['result']}" for k, v in out.items()), "error / no result", False)
    except ValueError as e: rec("ERR-GUESS", name, "ValueError raised", "error / no result", True)
print(sum(1 for r in res if r[4]), "pass /", len(res))
