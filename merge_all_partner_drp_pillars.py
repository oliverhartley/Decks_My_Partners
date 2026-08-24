import json
import subprocess
import os
import sys

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

PARTNER_SPREADSHEETS = [
    {"partner": "Comercializadora Zenta Group SPA", "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q"},
    {"partner": "Tech Pulse SPA (Axmos)", "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI"},
    {"partner": "Devaid SPA", "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8"},
    {"partner": "UCLOUD STORE COLOMBIA S A S", "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI"},
    {"partner": "TIVIT COLOMBIA S A S", "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o"},
    {"partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)", "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo"},
    {"partner": "MadeinWeb S/A", "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI"},
    {"partner": "CU2 CLOUD TEC STORE SL", "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew"},
    {"partner": "Consiti (Consultoría y Soluciones Informáticas)", "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo"}
]

for item in PARTNER_SPREADSHEETS:
    pname = item["partner"]
    ssid = item["sheet_id"]
    
    print(f"\n==========================================")
    print(f"Merging Pillar & Solution in DRP_Status for: {pname}")
    print(f"==========================================")
    
    # 1. Get sheet ID for DRP_Status
    res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res_meta.returncode != 0 or not res_meta.stdout.strip():
        print(f"Could not list sheets for {pname}")
        continue
        
    sheets = json.loads(res_meta.stdout)
    sheet_id = None
    for s in sheets:
        if s["title"] == "DRP_Status":
            sheet_id = s["id"]
            break
            
    if sheet_id is None:
        print(f"Tab 'DRP_Status' not found for {pname}")
        continue
        
    # 2. Read rows from DRP_Status
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, "'DRP_Status'!A1:F100", "--json"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        print(f"Could not read DRP_Status for {pname}")
        continue
        
    data = json.loads(res.stdout)
    if len(data) <= 1:
        print(f"No data rows in DRP_Status for {pname}")
        continue
        
    # First row is header (row 0), data starts at row 1
    # Find contiguous Pillar blocks
    pillar_blocks = []
    current_pillar = None
    start_r = 1
    
    for r_idx in range(1, len(data)):
        p = data[r_idx][0] if len(data[r_idx]) > 0 else ""
        if "no drp" in str(p).lower():
            continue
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
        
    print("Pillar blocks to merge:", pillar_blocks)
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
        
    # Find contiguous Solution blocks within each pillar block (or overall contiguous solutions)
    solution_blocks = []
    current_sol = None
    current_sol_pillar = None
    start_sol_r = 1
    
    for r_idx in range(1, len(data)):
        p = data[r_idx][0] if len(data[r_idx]) > 0 else ""
        sol = data[r_idx][1] if len(data[r_idx]) > 1 else ""
        if "no drp" in str(p).lower():
            continue
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
        
    print("Solution blocks to merge:", solution_blocks)
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
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", str(sheet_id),
        "--start-row", "1", "--end-row", str(len(data)),
        "--start-col", "0", "--end-col", "1",
        "--bold"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sheet_id), "--start-col", "0", "--end-col", "6"], capture_output=True)
    print(f"Pillars and Solutions merged and formatted for {pname}!")

print("\n==========================================")
print("ALL PARTNERS DRP_Status SHEETS HAVE PILLARS MERGED!")
print("==========================================")
