import json
import csv
import subprocess
import os
import sys

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

PARTNERS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q",
        "default_pid": "0014M00001h39BLQAY",
        "cert_pids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
        "drp_keys": ["P20220602109", "0014M00001h39BLQAY", "0014M00001m9woLQAQ"],
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "default_pid": "0014M00002JmizDQAR",
        "cert_pids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
        "drp_keys": ["P20260318001", "0014M00002JmizDQAR"],
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "default_pid": "0014M00001h38aiQAA",
        "cert_pids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
        "drp_keys": ["P20220923084", "0014M00001h38aiQAA"],
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "default_pid": "0014M00002M7lcJQAR",
        "cert_pids": ["0014M00002M7lcJQAR"],
        "drp_keys": ["0014M00002M7lcJQAR"],
        "country": "Colombia",
        "tier_level": "Premier"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "default_pid": "0014M00001kxZPMQA2",
        "cert_pids": ["0014M00001kxZPMQA2", "001Kf0000150rJ2IAI", "0014M00001m9v8HQAQ"],
        "drp_keys": ["P20220923297", "0014M00001kxZPMQA2", "001Kf0000150rJ2IAI"],
        "country": "Colombia / Regional",
        "tier_level": "Premier"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "default_pid": "0014M00001uFlbSQAS",
        "cert_pids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
        "drp_keys": ["P20220602104", "0014M00001uFlbSQAS"],
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "default_pid": "0014M00002GGNRCQA5",
        "cert_pids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
        "drp_keys": ["P20231208017", "0014M00002GGNRCQA5"],
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "default_pid": "0014M00001h35nAQAQ",
        "cert_pids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "0014M00002N5mLOQAZ"],
        "drp_keys": ["P20220923048", "0014M00001h35nAQAQ"],
        "country": "Regional / Spain & LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "default_pid": "001Kf000013fuVXIAY",
        "cert_pids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "drp_keys": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "country": "El Salvador / Central America",
        "tier_level": "Premier"
    }
]

def make_hyperlink(url, label):
    if not url or not label:
        return label or ""
    clean_label = str(label).replace('"', '""')
    return f'=HYPERLINK("{url}", "{clean_label}")'

def ensure_sheet_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        sheets = json.loads(res.stdout)
        for s in sheets:
            if s.get("title") == tab_title:
                return s.get("id")
    
    # Add sheet
    subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    
    # Check again
    res2 = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        sheets = json.loads(res2.stdout)
        for s in sheets:
            if s.get("title") == tab_title:
                return s.get("id")
    return None

os.makedirs("global_dashboard_data", exist_ok=True)

# =========================================================================
# 1. COMPILE CONSOLIDATED WORKLOADS (Follow_up)
# =========================================================================
print("\n--- 1. Compiling Global Workloads ---")
all_workload_rows = [[
    "Partner Name",
    "Customer Account Name",
    "Account Tier",
    "Workload Name",
    "Opportunity Name",
    "Expert Requests",
    "Customer Sub Region",
    "Customer Micro Region",
    "Primary Workload Pillar",
    "Workload Progress",
    "Begin Migration Date",
    "Production Date",
    "Annual Gross Revenue (ARR USD)",
    "Last Touch",
    "Link"
]]

total_arr_by_partner = {}
workload_counts_by_partner = {}

for p in PARTNERS:
    pname = p["partner"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    csv_file = os.path.join("followup_data_synced", f"{safe_name}_synced.csv")
    if not os.path.exists(csv_file):
        csv_file = os.path.join("followup_data_v4", f"{safe_name}_v4.csv")
    
    p_arr_total = 0.0
    p_wkl_count = 0
    
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                if row:
                    all_workload_rows.append(row)
                    p_wkl_count += 1
                    try:
                        arr_val = float(row[12].replace(",", ""))
                        p_arr_total += arr_val
                    except:
                        pass
                        
    total_arr_by_partner[pname] = p_arr_total
    workload_counts_by_partner[pname] = p_wkl_count

# Write Global Workloads CSV
global_wkl_csv = "global_dashboard_data/all_workloads_followup.csv"
with open(global_wkl_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_workload_rows)

# =========================================================================
# 2. COMPILE CONSOLIDATED DRP STATUS
# =========================================================================
print("\n--- 2. Compiling Global DRP Status ---")
all_drp_rows = [[
    "Partner Name",
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles"
]]

drp_profiles_by_partner = {}

for p in PARTNERS:
    pname = p["partner"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    drp_csv = os.path.join("drp_data", f"{safe_name}_drp.csv")
    p_drp_total = 0
    
    if os.path.exists(drp_csv):
        with open(drp_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                if row and not "No DRP" in row[0]:
                    all_drp_rows.append([pname] + row)
                    try:
                        p_drp_total += int(row[5])
                    except:
                        pass
    drp_profiles_by_partner[pname] = p_drp_total

global_drp_csv = "global_dashboard_data/all_drp_status.csv"
with open(global_drp_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_drp_rows)

# =========================================================================
# 3. COMPILE CONSOLIDATED ACCREDITATIONS
# =========================================================================
print("\n--- 3. Compiling Global Accreditations ---")
all_accred_rows = [[
    "Partner Name",
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Legal Entity"
]]

accred_counts_by_partner = {}

for p in PARTNERS:
    pname = p["partner"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    accred_csv = os.path.join("accred_data", f"{safe_name}_accred.csv")
    p_accred_total = 0
    
    if os.path.exists(accred_csv):
        with open(accred_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            for row in reader:
                if row and not "No active" in row[0]:
                    all_accred_rows.append([pname] + row)
                    p_accred_total += 1
    accred_counts_by_partner[pname] = p_accred_total

global_accred_csv = "global_dashboard_data/all_accreditations.csv"
with open(global_accred_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_accred_rows)

# =========================================================================
# 4. COMPILE EXECUTIVE SUMMARY SCORECARD
# =========================================================================
print("\n--- 4. Compiling Executive Summary Scorecard ---")
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
for p in PARTNERS:
    pname = p["partner"]
    pid = p["default_pid"]
    p_url = f"https://vector.lightning.force.com/lightning/r/Account/{pid}/view"
    p_link = make_hyperlink(p_url, pname)
    
    tracker_url = f"https://docs.google.com/spreadsheets/d/{p['sheet_id']}/edit#gid=0"
    tracker_link = make_hyperlink(tracker_url, "Open Partner Tracker ↗")
    
    wkl_cnt = workload_counts_by_partner.get(pname, 0)
    arr_val = total_arr_by_partner.get(pname, 0.0)
    drp_cnt = drp_profiles_by_partner.get(pname, 0)
    accred_cnt = accred_counts_by_partner.get(pname, 0)
    
    summary_rows.append([
        p_link,
        p["country"],
        p["tier_level"],
        str(wkl_cnt),
        f"{arr_val:,.2f}",
        str(drp_cnt),
        str(accred_cnt),
        tracker_link
    ])

# Add Total Row
total_wkl = sum(workload_counts_by_partner.values())
total_arr = sum(total_arr_by_partner.values())
total_drp = sum(drp_profiles_by_partner.values())
total_accred = sum(accred_counts_by_partner.values())

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

global_summary_csv = "global_dashboard_data/executive_summary.csv"
with open(global_summary_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(summary_rows)

print("\n--- 5. Importing into Global Master Spreadsheet ---")

# Tab 1: Executive_Summary
tab1 = "Executive_Summary"
sid1 = ensure_sheet_tab(GLOBAL_SSID, tab1)
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, f"'{tab1}'!A1:Z500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", f"'{tab1}'!2:500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_summary_csv, "--sheet", tab1], capture_output=True)
subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid1), "--rows", "1"], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid1),
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "8",
    "--bold",
    "--bg-color", "#1A73E8", # Royal blue header
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
# Total row bold & highlight
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid1),
    "--start-row", str(len(summary_rows)-1), "--end-row", str(len(summary_rows)),
    "--start-col", "0", "--end-col", "8",
    "--bold",
    "--bg-color", "#E8F0FE"
], capture_output=True)
# Center numbers
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid1),
    "--start-row", "1", "--end-row", str(len(summary_rows)),
    "--start-col", "3", "--end-col", "7",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid1), "--start-col", "0", "--end-col", "8"], capture_output=True)

# Tab 2: All_Workloads_Follow_up
tab2 = "All_Workloads_Follow_up"
sid2 = ensure_sheet_tab(GLOBAL_SSID, tab2)
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, f"'{tab2}'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", f"'{tab2}'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_wkl_csv, "--sheet", tab2], capture_output=True)
subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid2), "--rows", "1"], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid2),
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "15",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid2),
    "--start-row", "0", "--end-row", "1",
    "--start-col", "13", "--end-col", "15",
    "--bold",
    "--bg-color", "#E6F4EA",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid2),
    "--start-row", "1", "--end-row", str(len(all_workload_rows)),
    "--start-col", "2", "--end-col", "3",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid2), "--start-col", "0", "--end-col", "15"], capture_output=True)

# Tab 3: All_DRP_Status
tab3 = "All_DRP_Status"
sid3 = ensure_sheet_tab(GLOBAL_SSID, tab3)
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, f"'{tab3}'!A1:Z2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", f"'{tab3}'!2:2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_drp_csv, "--sheet", tab3], capture_output=True)
subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid3), "--rows", "1"], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid3),
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "7",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid3),
    "--start-row", "1", "--end-row", str(len(all_drp_rows)),
    "--start-col", "4", "--end-col", "7",
    "--align", "CENTER"
], capture_output=True)
# Perform merges for Partner Name (Col 0) and Pillar (Col 1)
partner_blocks = []
curr_p = None
s_r = 1
for r_idx in range(1, len(all_drp_rows)):
    p = all_drp_rows[r_idx][0]
    if curr_p is None:
        curr_p = p
        s_r = r_idx
    elif p != curr_p:
        if r_idx - s_r > 1:
            partner_blocks.append((curr_p, s_r, r_idx))
        curr_p = p
        s_r = r_idx
if curr_p and (len(all_drp_rows) - s_r > 1):
    partner_blocks.append((curr_p, s_r, len(all_drp_rows)))

for p, s_idx, e_idx in partner_blocks:
    subprocess.run([
        GSHEETS, "mutate", "merge", GLOBAL_SSID,
        "--sheet-id", str(sid3),
        "--start-row", str(s_idx),
        "--end-row", str(e_idx),
        "--start-col", "0",
        "--end-col", "1",
        "--merge-type", "MERGE_ALL"
    ], capture_output=True)

# Pillar blocks
pillar_blocks = []
curr_pil = None
curr_pil_p = None
s_r = 1
for r_idx in range(1, len(all_drp_rows)):
    p = all_drp_rows[r_idx][0]
    pil = all_drp_rows[r_idx][1]
    if curr_pil is None:
        curr_pil = pil
        curr_pil_p = p
        s_r = r_idx
    elif pil != curr_pil or p != curr_pil_p:
        if r_idx - s_r > 1:
            pillar_blocks.append((curr_pil, s_r, r_idx))
        curr_pil = pil
        curr_pil_p = p
        s_r = r_idx
if curr_pil and (len(all_drp_rows) - s_r > 1):
    pillar_blocks.append((curr_pil, s_r, len(all_drp_rows)))

for pil, s_idx, e_idx in pillar_blocks:
    subprocess.run([
        GSHEETS, "mutate", "merge", GLOBAL_SSID,
        "--sheet-id", str(sid3),
        "--start-row", str(s_idx),
        "--end-row", str(e_idx),
        "--start-col", "1",
        "--end-col", "2",
        "--merge-type", "MERGE_ALL"
    ], capture_output=True)

subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid3), "--start-col", "0", "--end-col", "7"], capture_output=True)

# Tab 4: All_Acreditaciones
tab4 = "All_Acreditaciones"
sid4 = ensure_sheet_tab(GLOBAL_SSID, tab4)
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, f"'{tab4}'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", f"'{tab4}'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_accred_csv, "--sheet", tab4], capture_output=True)
subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid4), "--rows", "1"], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid4),
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "9",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", GLOBAL_SSID,
    "--sheet-id", str(sid4),
    "--start-row", "1", "--end-row", str(len(all_accred_rows)),
    "--start-col", "6", "--end-col", "8",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid4), "--start-col", "0", "--end-col", "9"], capture_output=True)

# If default Sheet1 exists, delete it
res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", GLOBAL_SSID, "--json"], capture_output=True, text=True)
if res_meta.returncode == 0:
    sheets = json.loads(res_meta.stdout)
    for s in sheets:
        if s.get("title") in ["Sheet1", "Hoja 1"] and len(sheets) > 1:
            subprocess.run([GSHEETS, "mutate", "delete-sheet", GLOBAL_SSID, "--sheet-id", str(s["id"])], capture_output=True)

print("\n==========================================")
print("GLOBAL PARTNER MANAGEMENT DASHBOARD COMPLETED!")
print(f"Spreadsheet ID: {GLOBAL_SSID}")
print(f"URL: https://docs.google.com/spreadsheets/d/{GLOBAL_SSID}/edit")
print("==========================================")
