#!/usr/bin/env python3
from pathlib import Path
import re
from datetime import datetime

TOP = "tt_um_c0d3d1_ldo"
DEV = "DEV_OPAMP"

layout_path = Path("lvs/tt_um_c0d3d1_ldo_layout.spice")
schem_path  = Path("lvs/tt_um_c0d3d1_ldo_schematic.spice")

backup = Path(f"lvs/tt_um_c0d3d1_ldo_schematic_auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.spice")
backup.write_text(schem_path.read_text())

def get_subckt_header(path: Path, cell: str):
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^\s*\.subckt\s+{re.escape(cell)}\b", line, re.I):
            header = [line]
            j = i + 1
            while j < len(lines) and lines[j].lstrip().startswith("+"):
                header.append(lines[j])
                j += 1
            return header
    raise SystemExit(f"ERROR: could not find .subckt {cell} in {path}")

def replace_top_header(lines, header, cell):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(rf"^\s*\.subckt\s+{re.escape(cell)}\b", line, re.I):
            out.extend(header)
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("+"):
                i += 1
            continue
        out.append(line)
        i += 1
    return out

def set_param(line: str, param: str, value: str):
    # Replace param=value token if it exists; otherwise append it.
    pat = rf"(?i)\b{re.escape(param)}=([^\s]+)"
    if re.search(pat, line):
        return re.sub(pat, f"{param}={value}", line)
    return line + f" {param}={value}"

layout_header = get_subckt_header(layout_path, TOP)

lines = schem_path.read_text().splitlines()
lines = replace_top_header(lines, layout_header, TOP)

out = []
current = None

for line in lines:
    stripped = line.strip()

    m = re.match(r"^\s*\.subckt\s+(\S+)", stripped, re.I)
    if m:
        current = m.group(1)
        out.append(line)
        continue

    if re.match(r"^\s*\.ends\b", stripped, re.I):
        out.append(line)
        current = None
        continue

    # -----------------------------
    # Top-level patches
    # -----------------------------
    if current == TOP:
        # Pass PMOS: layout merged W = 1056, schematic W = 88 nf=12.
        if re.match(r"^XM2\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8" in line:
            line = set_param(line, "W", "1056")
            line = set_param(line, "nf", "1")

        # Bandgap/top-level LVT devices M1 and M13: layout merged W = 120.
        elif re.match(r"^XM1\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8_lvt" in line:
            line = set_param(line, "W", "120")
            line = set_param(line, "nf", "1")

        elif re.match(r"^XM13\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8_lvt" in line:
            line = set_param(line, "W", "120")
            line = set_param(line, "nf", "1")

        # New 1p41 resistor extracted lengths from layout property errors.
        # Only patch top-level / bandgap resistors, not DEV_OPAMP resistors.
        elif re.match(r"^XR1\b", stripped, re.I) and "res_xhigh_po_1p41" in line:
            line = set_param(line, "L", "5.12")

        elif re.match(r"^XR8\b", stripped, re.I) and "res_xhigh_po_1p41" in line:
            line = set_param(line, "L", "5.6")

        elif re.match(r"^XR3\b", stripped, re.I) and "res_xhigh_po_1p41" in line:
            line = set_param(line, "L", "2.65")

    # -----------------------------
    # DEV_OPAMP patches
    # -----------------------------
    elif current == DEV:
        # Extracted merged widths from layout:
        # M11: 36, M13: 240, M14: 270, M15/M16: 144.
        if re.match(r"^XM11\b", stripped, re.I) and "sky130_fd_pr__nfet_01v8" in line:
            line = set_param(line, "W", "36")
            line = set_param(line, "nf", "1")

        elif re.match(r"^XM13\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8_lvt" in line:
            line = set_param(line, "W", "240")
            line = set_param(line, "nf", "1")

        elif re.match(r"^XM14\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8_lvt" in line:
            line = set_param(line, "W", "270")
            line = set_param(line, "nf", "1")

        elif re.match(r"^XM15\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8_lvt" in line:
            line = set_param(line, "W", "144")
            line = set_param(line, "nf", "1")

        elif re.match(r"^XM16\b", stripped, re.I) and "sky130_fd_pr__pfet_01v8_lvt" in line:
            line = set_param(line, "W", "144")
            line = set_param(line, "nf", "1")

    out.append(line)

schem_path.write_text("\n".join(out) + "\n")

print(f"Wrote patched LVS schematic: {schem_path}")
print(f"Backup saved as: {backup}")
print("\nCopied top header from layout:")
print("\n".join(layout_header))
