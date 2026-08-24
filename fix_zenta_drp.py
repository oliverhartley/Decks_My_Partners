import json
import subprocess
import os
import csv

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
ssid = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q"
tab_title = "DRP_Status"
csv_file = "drp_data/Comercializadora_Zenta_Group_SPA_drp.csv"

# 1. Unmerge all cells first in DRP_Status
res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
sheets = json.loads(res_meta.stdout)
sheet_id = None
for s in sheets:
    if s["title"] == tab_title:
        sheet_id = s["id"]
        break

# Clear and reimport CSV
subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_title}'!A1:Z1000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_title}'!2:1000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", ssid, csv_file, "--sheet", tab_title], capture_output=True)

# Read clean rows
res = subprocess.run([GSHEETS, "readonly", "read", ssid, f"'{tab_title}'!A1:F20", "--json"], capture_output=True, text=True)
data = json.loads(res.stdout)

# Find pillar blocks
pillar_blocks = []
current_pillar = None
start_r = 1

for r_idx in range(1, len(data)):
    p = data[r_idx][0] if len(data[r_idx]) > 0 else ""
    if current_pillar is None:
        current_pillar = p
        start_r = r_idx
    elif p != current_pillar:
        if r_idx - start_r > 1:
            pillar_blocks.append((current_pillar, start_r, r_idx))
        current_pillar = p
        start_r = r_idx

if current_pillar and (len(data) - start_r > 1):
    pillar_blocks.append((current_pillar, start_r, len(data)))

print("Pillar blocks for Zenta:", pillar_blocks)
for p, s_r, e_r in pillar_blocks:
    subprocess.run([
        GSHEETS, "mutate", "merge", ssid,
        "--sheet-id", str(sheet_id),
        "--start-row", str(s_r),
        "--end-row", str(e_r),
        "--start-col", "0",
        "--end-col", "1",
        "--merge-type", "MERGE_ALL"
    ], capture_output=True)

# Solution blocks
solution_blocks = []
current_sol = None
current_sol_pillar = None
start_sol_r = 1

for r_idx in range(1, len(data)):
    p = data[r_idx][0] if len(data[r_idx]) > 0 else ""
    sol = data[r_idx][1] if len(data[r_idx]) > 1 else ""
    if current_sol is None:
        current_sol = sol
        current_sol_pillar = p
        start_sol_r = r_idx
    elif sol != current_sol or p != current_sol_pillar:
        if r_idx - start_sol_r > 1:
            solution_blocks.append((current_sol, start_sol_r, r_idx))
        current_sol = sol
        current_sol_pillar = p
        start_sol_r = r_idx

if current_sol and (len(data) - start_sol_r > 1):
    solution_blocks.append((current_sol, start_sol_r, len(data)))

print("Solution blocks for Zenta:", solution_blocks)
for sol, s_r, e_r in solution_blocks:
    subprocess.run([
        GSHEETS, "mutate", "merge", ssid,
        "--sheet-id", str(sheet_id),
        "--start-row", str(s_r),
        "--end-row", str(e_r),
        "--start-col", "1",
        "--end-col", "2",
        "--merge-type", "MERGE_ALL"
    ], capture_output=True)

# Formatting
subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sheet_id), "--rows", "1"], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", ssid,
    "--sheet-id", str(sheet_id),
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "6",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", ssid,
    "--sheet-id", str(sheet_id),
    "--start-row", "1", "--end-row", str(len(data)),
    "--start-col", "0", "--end-col", "1",
    "--bold"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", ssid,
    "--sheet-id", str(sheet_id),
    "--start-row", "1", "--end-row", str(len(data)),
    "--start-col", "3", "--end-col", "6",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sheet_id), "--start-col", "0", "--end-col", "6"], capture_output=True)
print("Zenta DRP cleanly merged and formatted!")
