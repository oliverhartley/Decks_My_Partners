import json
import csv
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

PARTNERS = [
    {"partner": "Comercializadora Zenta Group SPA", "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q", "default_pid": "0014M00001h39BLQAY", "country": "Chile", "tier_level": "Premier"},
    {"partner": "Tech Pulse SPA (Axmos)", "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI", "default_pid": "0014M00002JmizDQAR", "country": "Chile", "tier_level": "Premier"},
    {"partner": "Devaid SPA", "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8", "default_pid": "0014M00001h38aiQAA", "country": "Chile", "tier_level": "Premier"},
    {"partner": "UCLOUD STORE COLOMBIA S A S", "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI", "default_pid": "0014M00002M7lcJQAR", "country": "Colombia", "tier_level": "Premier"},
    {"partner": "TIVIT COLOMBIA S A S", "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o", "default_pid": "0014M00001kxZPMQA2", "country": "Colombia / Regional", "tier_level": "Premier"},
    {"partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)", "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo", "default_pid": "0014M00001uFlbSQAS", "country": "Brazil", "tier_level": "Premier"},
    {"partner": "MadeinWeb S/A", "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI", "default_pid": "0014M00002GGNRCQA5", "country": "Brazil", "tier_level": "Premier"},
    {"partner": "CU2 CLOUD TEC STORE SL", "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew", "default_pid": "0014M00001h35nAQAQ", "country": "Regional / Spain & LATAM", "tier_level": "Premier"},
    {"partner": "Consiti (Consultoría y Soluciones Informáticas)", "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo", "default_pid": "001Kf000013fuVXIAY", "country": "El Salvador / Central America", "tier_level": "Premier"}
]

def make_hyperlink(url, label):
    if not url or not label:
        return label or ""
    clean_label = str(label).replace('"', '""')
    return f'=HYPERLINK("{url}", "{clean_label}")'

summary_headers = [
    "Partner Name",
    "Country / Headquarters",
    "Partner Advantage Track",
    "Uncommitted Tier 2 & 3 Workloads (#)",
    "Total Pipeline ARR ($ USD)",
    "DRP Profile Capacities (#)",
    "Active Accreditations / Certs (#)",
    "Partner Action Tracker Spreadsheet"
]

summary_rows = [summary_headers]
total_wkl = 0
total_arr = 0.0
total_drp = 0
total_accred = 0

for p in PARTNERS:
    pname = p["partner"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    
    # 1. Workloads & ARR
    wkl_csv = f"followup_data_synced/{safe_name}_synced.csv"
    p_wkl = 0
    p_arr = 0.0
    if os.path.exists(wkl_csv):
        with open(wkl_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    p_wkl += 1
                    try:
                        p_arr += float(row[12].replace(",", ""))
                    except:
                        pass
                        
    # 2. DRP
    drp_csv = f"drp_data_full/{safe_name}_drp_full.csv"
    p_drp = 0
    if os.path.exists(drp_csv):
        with open(drp_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row:
                    try:
                        p_drp += int(row[5])
                    except:
                        pass
                        
    # 3. Accreditations
    accred_csv = f"accred_data/{safe_name}_accred.csv"
    p_accred = 0
    if os.path.exists(accred_csv):
        with open(accred_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if row and not "No active" in row[0]:
                    p_accred += 1
                    
    total_wkl += p_wkl
    total_arr += p_arr
    total_drp += p_drp
    total_accred += p_accred
    
    p_url = f"https://vector.lightning.force.com/lightning/r/Account/{p['default_pid']}/view"
    p_link = make_hyperlink(p_url, pname)
    tracker_url = f"https://docs.google.com/spreadsheets/d/{p['sheet_id']}/edit#gid=0"
    tracker_link = make_hyperlink(tracker_url, "Open Partner Tracker ↗")
    
    summary_rows.append([
        p_link,
        p["country"],
        p["tier_level"],
        str(p_wkl),
        f"{p_arr:,.2f}",
        str(p_drp),
        str(p_accred),
        tracker_link
    ])

summary_rows.append([
    "TOTAL (All 9 Partners)",
    "-",
    "-",
    str(total_wkl),
    f"{total_arr:,.2f}",
    str(total_drp),
    str(total_accred),
    "-"
])

csv_out = "global_dashboard_data/executive_summary.csv"
with open(csv_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(summary_rows)

tab1 = "Executive_Summary"
res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", GLOBAL_SSID, "--json"], capture_output=True, text=True)
sheets = json.loads(res_meta.stdout) if res_meta.returncode == 0 else []
sid1 = None
for s in sheets:
    if s.get("title") == tab1:
        sid1 = s.get("id")
        break

subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, f"'{tab1}'!A1:Z500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", f"'{tab1}'!2:500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, csv_out, "--sheet", tab1], capture_output=True)

if sid1 is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid1), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid1),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#1A73E8",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid1),
        "--start-row", str(len(summary_rows)-1), "--end-row", str(len(summary_rows)),
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#E8F0FE"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid1),
        "--start-row", "1", "--end-row", str(len(summary_rows)),
        "--start-col", "3", "--end-col", "7",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid1), "--start-col", "0", "--end-col", "8"], capture_output=True)

print("Executive Summary refreshed successfully.")
