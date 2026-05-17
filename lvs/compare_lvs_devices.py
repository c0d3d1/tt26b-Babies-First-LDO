#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import sys
import re

if len(sys.argv) != 3:
    print("Usage: compare_lvs_devices.py layout.spice schematic.spice")
    sys.exit(1)

layout_file = Path(sys.argv[1])
schem_file = Path(sys.argv[2])

MODELS = [
    "sky130_fd_pr__nfet_01v8",
    "sky130_fd_pr__pfet_01v8_lvt",
    "sky130_fd_pr__pfet_01v8_hvt",
    "sky130_fd_pr__pfet_01v8",
    "sky130_fd_pr__cap_mim_m3_1",
    "sky130_fd_pr__res_high_po_5p73",
    "sky130_fd_pr__res_high_po_0p69",
    "sky130_fd_pr__pnp_05v5_W3p40L3p40",
    "sky130_fd_pr__rf_pnp_05v5_W3p40L3p40",
]

def join_continuations(text):
    out = []
    cur = ""
    start_line = 0
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        s = line.strip()
        if not s:
            continue
        if s.startswith("*"):
            continue
        if s.startswith("+"):
            cur += " " + s[1:].strip()
        else:
            if cur:
                out.append((start_line, cur))
            cur = line
            start_line = i
    if cur:
        out.append((start_line, cur))
    return out

def parse_devices(path):
    text = path.read_text(errors="ignore")
    lines = join_continuations(text)
    devs = defaultdict(list)

    for lineno, line in lines:
        tokens = line.split()
        if len(tokens) < 2:
            continue

        # Last token before params is usually model/subckt for X/M/R/C lines in these netlists.
        # Find known model anywhere on line.
        for model in MODELS:
            if model in tokens:
                idx = tokens.index(model)
                name = tokens[0]
                nodes = tokens[1:idx]
                params = tokens[idx+1:]
                devs[model].append((lineno, name, nodes, params, line))
                break

    return devs

def print_report(label, devs):
    print(f"\n================ {label} ================")
    for model in MODELS:
        arr = devs.get(model, [])
        if not arr:
            continue
        print(f"\n--- {model}: {len(arr)} occurrences ---")
        for lineno, name, nodes, params, line in arr:
            print(f"{lineno:5d}: {name:18s} nodes={nodes}")
            # print useful geometry params only
            useful = [p for p in params if p.lower().startswith(("w=", "l=", "m=", "mult=", "mf="))]
            if useful:
                print(f"       params={' '.join(useful)}")

layout = parse_devices(layout_file)
schem = parse_devices(schem_file)

print_report("LAYOUT", layout)
print_report("SCHEMATIC", schem)

print("\n================ COUNT DIFF ================")
for model in MODELS:
    lc = len(layout.get(model, []))
    sc = len(schem.get(model, []))
    if lc != sc:
        print(f"{model:45s} layout={lc:3d} schematic={sc:3d} diff={lc-sc:+d}")
