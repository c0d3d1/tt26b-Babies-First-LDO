#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import re
import sys

if len(sys.argv) != 2:
    print("Usage: find_layout_shorts.py layout.spice")
    sys.exit(1)

path = Path(sys.argv[1])
text = path.read_text(errors="ignore").splitlines()

def join_continuations(lines):
    out = []
    cur = ""
    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if not s or s.startswith("*"):
            continue
        if s.startswith("+"):
            cur += " " + s[1:].strip()
        else:
            if cur:
                out.append(cur)
            cur = line
    if cur:
        out.append(cur)
    return out

stmts = join_continuations(text)

subckts = {}
current = None
for stmt in stmts:
    toks = stmt.split()
    if not toks:
        continue
    if toks[0].lower() == ".subckt":
        current = toks[1]
        subckts[current] = {"pins": toks[2:], "body": []}
    elif toks[0].lower() == ".ends":
        current = None
    elif current:
        subckts[current]["body"].append(stmt)

primitive_models = {
    "sky130_fd_pr__pfet_01v8",
    "sky130_fd_pr__pfet_01v8_lvt",
    "sky130_fd_pr__pfet_01v8_hvt",
    "sky130_fd_pr__nfet_01v8",
    "sky130_fd_pr__cap_mim_m3_1",
    "sky130_fd_pr__res_high_po_0p69",
    "sky130_fd_pr__res_high_po_5p73",
    "sky130_fd_pr__pnp_05v5_W3p40L3p40",
}

devices = []

def map_node(n, env, prefix):
    if n in env:
        return env[n]
    if n in ("VDPWR", "VGND", "ua[0]", "ua[1]", "ua[2]", "ua[3]", "ua[4]", "ua[5]", "ua[6]", "ua[7]", "clk", "ena", "rst_n"):
        return n
    if n == "0":
        return "0"
    return f"{prefix}/{n}" if prefix else n

def flatten(cell, actuals, prefix):
    if cell not in subckts:
        return

    pins = subckts[cell]["pins"]
    env = {}
    for p, a in zip(pins, actuals):
        env[p] = a

    for stmt in subckts[cell]["body"]:
        toks = stmt.split()
        if not toks or not toks[0].startswith("X"):
            continue

        name = toks[0]
        # Find model token. For this layout netlist, model is first token from end
        # that is either primitive or a known subckt.
        model_i = None
        model = None
        for i in range(len(toks) - 1, 0, -1):
            if toks[i] in primitive_models or toks[i] in subckts:
                model_i = i
                model = toks[i]
                break
        if model_i is None:
            continue

        raw_nodes = toks[1:model_i]
        nodes = [map_node(n, env, prefix) for n in raw_nodes]
        inst_path = f"{prefix}/{name}" if prefix else name

        if model in primitive_models:
            devices.append((inst_path, model, nodes, stmt))
        else:
            flatten(model, nodes, inst_path)

# Top cell
flatten("tt_um_c0d3d1_ldo", [], "")

print("\n=== HARD SHORTS / SUSPICIOUS DEVICES ===")

for inst, model, nodes, stmt in devices:
    if model in ("sky130_fd_pr__pfet_01v8", "sky130_fd_pr__pfet_01v8_lvt", "sky130_fd_pr__pfet_01v8_hvt", "sky130_fd_pr__nfet_01v8"):
        if len(nodes) >= 4:
            d, g, s, b = nodes[:4]
            if d == s:
                print(f"MOS_DRAIN_SOURCE_SHORT  {model:32s} {inst}")
                print(f"    D=S={d}  G={g}  B={b}")
            if g == d or g == s:
                print(f"MOS_GATE_TIED_TO_D_OR_S {model:32s} {inst}")
                print(f"    D={d}  G={g}  S={s}  B={b}")

    if model == "sky130_fd_pr__cap_mim_m3_1":
        if len(nodes) >= 2:
            c1, c2 = nodes[:2]
            if c1 == c2:
                print(f"CAP_PLATES_SHORTED      {inst}")
                print(f"    C1=C2={c1}")

print("\n=== MIM CAP GROUPS AFTER NET PAIRS ===")
cap_groups = defaultdict(list)
for inst, model, nodes, stmt in devices:
    if model == "sky130_fd_pr__cap_mim_m3_1" and len(nodes) >= 2:
        key = tuple(sorted(nodes[:2]))
        cap_groups[key].append(inst)

for key, arr in sorted(cap_groups.items(), key=lambda x: (x[0], x[1])):
    print(f"{key}:")
    for a in arr:
        print(f"    {a}")

print("\n=== LVT PMOS MERGE GROUPS ===")
mos_groups = defaultdict(list)
for inst, model, nodes, stmt in devices:
    if model == "sky130_fd_pr__pfet_01v8_lvt" and len(nodes) >= 4:
        d, g, s, b = nodes[:4]
        # D/S reversible for LVS
        key = (tuple(sorted([d, s])), g, b)
        mos_groups[key].append(inst)

for key, arr in sorted(mos_groups.items(), key=lambda x: (-len(x[1]), x[0])):
    ds, g, b = key
    print(f"D/S={ds}  G={g}  B={b}   count={len(arr)}")
    for a in arr:
        print(f"    {a}")

print("\n=== DEVICES TOUCHING ua[1] ===")
for inst, model, nodes, stmt in devices:
    if "ua[1]" in nodes:
        print(f"{model:32s} {inst}")
        print(f"    nodes={nodes}")

print("\n=== DEVICES TOUCHING X1_M16/B or X2_M16/B ===")
for inst, model, nodes, stmt in devices:
    if any(("X1_M16/B" in n or "X2_M16/B" in n) for n in nodes):
        print(f"{model:32s} {inst}")
        print(f"    nodes={nodes}")
