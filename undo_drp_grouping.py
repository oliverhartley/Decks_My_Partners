import json
import subprocess
import os
import sys

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

PARTNERS = [
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

print("\n==========================================")
print("1. Undoing DRP grouping on all 9 individual trackers")
print("==========================================")

for p in PARTNERS:
    pname = p["partner"]
    ssid = p["sheet_id"]
    tab_title = "DRP_Status"
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    csv_file = os.path.join("drp_data", f"{safe_name}_drp.csv")
    
    print(f"\nProcessing {pname}...")
    # Find sheet ID
    res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res_meta.returncode != 0 or not res_meta.stdout.strip():
        continue
    sheets = json.loads(res_meta.stdout)
    sheet_id = None
    for s in sheets:
        if s.get("title") == tab_title:
            sheet_id = s.get("id")
            break
            
    if sheet_id is None:
        print(f"Tab '{tab_title}' not found for {pname}")
        continue
        
    # Unmerge all cells in sheet
    subprocess.run([
        GSHEETS, "mutate", "unmerge", ssid,
        "--sheet-id", str(sheet_id),
        "--start-row", "0", "--end-row", "1000",
        "--start-col", "0", "--end-col", "10"
    ], capture_output=True)
    
    # Clear and re-import clean flat CSV
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_title}'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_title}'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, csv_file, "--sheet", tab_title], capture_output=True)
    
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
        "--start-row", "1", "--end-row", "1000",
        "--start-col", "3", "--end-col", "6",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sheet_id), "--start-col", "0", "--end-col", "6"], capture_output=True)
    print(f"Unmerged and restored flat table for {pname} DRP_Status.")

print("\n==========================================")
print("2. Undoing DRP grouping on Global Master Dashboard")
print("==========================================")

tab_global = "All_DRP_Status"
global_csv = "global_dashboard_data/all_drp_status.csv"

res_meta_g = subprocess.run([GSHEETS, "readonly", "list-sheets", GLOBAL_SSID, "--json"], capture_output=True, text=True)
if res_meta_g.returncode == 0 and res_meta_g.stdout.strip():
    sheets_g = json.loads(res_meta_g.stdout)
    sheet_id_g = None
    for s in sheets_g:
        if s.get("title") == tab_global:
            sheet_id_g = s.get("id")
            break
            
    if sheet_id_g is not None:
        # Unmerge
        subprocess.run([
            GSHEETS, "mutate", "unmerge", GLOBAL_SSID,
            "--sheet-id", str(sheet_id_g),
            "--start-row", "0", "--end-row", "2000",
            "--start-col", "0", "--end-col", "10"
        ], capture_output=True)
        
        # Clear and reimport flat CSV
        subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, f"'{tab_global}'!A1:Z2000"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", f"'{tab_global}'!2:2000"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_csv, "--sheet", tab_global], capture_output=True)
        
        # Formatting
        subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sheet_id_g), "--rows", "1"], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", GLOBAL_SSID,
            "--sheet-id", str(sheet_id_g),
            "--start-row", "0", "--end-row", "1",
            "--start-col", "0", "--end-col", "7",
            "--bold",
            "--bg-color", "#E8F0FE",
            "--align", "CENTER",
            "--wrap"
        ], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", GLOBAL_SSID,
            "--sheet-id", str(sheet_id_g),
            "--start-row", "1", "--end-row", "2000",
            "--start-col", "4", "--end-col", "7",
            "--align", "CENTER"
        ], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sheet_id_g), "--start-col", "0", "--end-col", "7"], capture_output=True)
        print("Unmerged and restored flat table for Global Master All_DRP_Status.")

print("\n==========================================")
print("ALL DRP_STATUS TABS SUCCESSFULLY UNMERGED / RESTORED TO FLAT TABLES!")
print("==========================================")
