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
        "drp_keys": ["P20220602109", "0014M00001h39BLQAY", "0014M00001m9woLQAQ"]
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "drp_keys": ["P20260318001", "0014M00002JmizDQAR"]
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "drp_keys": ["P20220923084", "0014M00001h38aiQAA"]
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "drp_keys": ["0014M00002M7lcJQAR"]
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "drp_keys": ["P20220923297", "0014M00001kxZPMQA2", "001Kf0000150rJ2IAI"]
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "drp_keys": ["P20220602104", "0014M00001uFlbSQAS"]
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "drp_keys": ["P20231208017", "0014M00002GGNRCQA5"]
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "drp_keys": ["P20220923048", "0014M00001h35nAQAQ"]
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "drp_keys": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"]
    }
]

PILLAR_MAPPING = {
    "Application Modernization": ["Migrate Modernize and Build", "Application Modernization"],
    "Artificial Intelligence": ["Build with AI", "Infra AI", "Developer AI Assistance", "Customer Engagement", "Artificial Intelligence"],
    "Data & Analytics": ["Analytics", "Data & Analytics", "Data Cloud"],
    "Databases": ["Migrate and Modernize Databases", "Databases", "Database"],
    "Infrastructure Modernization": ["Migrate Modernize and Build", "Infrastructure Modernization", "Networking", "Storage", "Infrastructure"],
    "Security": ["Security"],
    "Workspace": ["Workspace", "Google Workspace"]
}

def get_workload_counts_by_pillar(safe_name):
    csv_file = f"followup_data_synced/{safe_name}_synced.csv"
    counts = {k: 0 for k in PILLAR_MAPPING}
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) > 8:
                    w_pil = row[8].strip()
                    for drp_pil, synonyms in PILLAR_MAPPING.items():
                        if any(s.lower() in w_pil.lower() for s in synonyms):
                            counts[drp_pil] += 1
    return counts

def compute_dot(drp_profiles_str, pillar_workloads):
    p = 0
    try:
        if drp_profiles_str and str(drp_profiles_str).strip() not in ["", "0", "None"]:
            p = int(drp_profiles_str)
    except:
        p = 0
    w = pillar_workloads
    
    if w > 0 and p == 0:
        return f"🔴 Gap (0 / {w} wkls)"
    elif w > 0 and p < w:
        return f"🟡 Constrained ({p} / {w} wkls)"
    elif p >= w and (p > 0 or w > 0):
        return f"🟢 Ready ({p} / {w} wkls)" if w > 0 else f"🟢 Ready ({p} profiles)"
    else:
        return "⚪ No Active Demand"

def format_count(val):
    if val is None or str(val).strip() in ["0", "", "None"]:
        return ""
    return str(val).strip()

DRP_HEADERS = [
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
]

os.makedirs("drp_data_with_dots", exist_ok=True)
all_global_drp_rows = [[
    "Partner Name",
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
]]

for p in PARTNERS:
    pname = p["partner"]
    ssid = p["sheet_id"]
    drp_keys = p["drp_keys"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    keys_str = ", ".join([f"\"{k}\"" for k in drp_keys])
    
    w_counts = get_workload_counts_by_pillar(safe_name)
    
    print(f"\n==========================================")
    print(f"Adding Capacity Dots to DRP for: {pname}")
    print(f"==========================================")
    
    sql = f"""
    WITH Catalog AS (
      SELECT DISTINCT
        pillar,
        sol as solution,
        COALESCE(p.scored_product, 'All Products') as product
      FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
      CROSS JOIN UNNEST(p.parent_pillar) pillar
      CROSS JOIN UNNEST(p.sales_play) sol
      WHERE pillar IS NOT NULL AND sol IS NOT NULL
    ),
    PartnerProfiles AS (
      SELECT 
        p.consolidated_partner_id,
        pillar,
        sol as solution,
        COALESCE(p.scored_product, 'All Products') as product,
        COUNT(DISTINCT IF(p.tier_category = 'Tier 1', p.profile_id, NULL)) as tier1_count,
        COUNT(DISTINCT IF(p.tier_category = 'Tier 2', p.profile_id, NULL)) as tier2_count,
        COUNT(DISTINCT IF(p.tier_category IN ('Tier 1', 'Tier 2'), p.profile_id, NULL)) as total_tier1_tier2
      FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
      CROSS JOIN UNNEST(p.parent_pillar) pillar
      CROSS JOIN UNNEST(p.sales_play) sol
      WHERE p.consolidated_partner_id IN ({keys_str})
      GROUP BY 1, 2, 3, 4
    )
    SELECT 
      c.pillar,
      c.solution,
      c.product,
      COALESCE(pp.tier1_count, 0) as tier1_count,
      COALESCE(pp.tier2_count, 0) as tier2_count,
      COALESCE(pp.total_tier1_tier2, 0) as total_tier1_tier2
    FROM Catalog c
    LEFT JOIN PartnerProfiles pp
      ON c.pillar = pp.pillar
      AND c.solution = pp.solution
      AND c.product = pp.product
    ORDER BY c.pillar, c.solution, c.product
    """
    
    schema, rows = run_query(sql)
    
    drp_rows = [DRP_HEADERS]
    for r in rows:
        pil = r["f"][0].get("v") or ""
        sol = r["f"][1].get("v") or ""
        prd = r["f"][2].get("v") or ""
        t1_raw = r["f"][3].get("v")
        t2_raw = r["f"][4].get("v")
        tot_raw = r["f"][5].get("v")
        
        t1 = format_count(t1_raw)
        t2 = format_count(t2_raw)
        tot = format_count(tot_raw)
        
        w_pillar_cnt = w_counts.get(pil, 0)
        dot_status = compute_dot(tot_raw, w_pillar_cnt)
        
        drp_rows.append([pil, sol, prd, t1, t2, tot, dot_status])
        all_global_drp_rows.append([pname, pil, sol, prd, t1, t2, tot, dot_status])
        
    csv_file = os.path.join("drp_data_with_dots", f"{safe_name}_drp_dots.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(drp_rows)
        
    # Find sheet ID
    tab_title = "DRP_Status"
    res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    sheets = json.loads(res_meta.stdout) if res_meta.returncode == 0 else []
    sheet_id = None
    for s in sheets:
        if s.get("title") == tab_title:
            sheet_id = s.get("id")
            break
            
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_title}'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_title}'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, csv_file, "--sheet", tab_title], capture_output=True)
    
    if sheet_id is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sheet_id), "--rows", "1"], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sheet_id),
            "--start-row", "0", "--end-row", "1",
            "--start-col", "0", "--end-col", "7",
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
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sheet_id), "--start-col", "0", "--end-col", "7"], capture_output=True)
    print(f"Updated {pname} DRP_Status with Column G Capacity Dots.")

# Update Global Master Dashboard All_DRP_Status tab
print("\n==========================================")
print("Updating Global Master Dashboard All_DRP_Status with Column H Capacity Dots")
print("==========================================")

global_drp_dots_csv = "global_dashboard_data/all_drp_status_dots.csv"
with open(global_drp_dots_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_drp_rows)

res_meta_g = subprocess.run([GSHEETS, "readonly", "list-sheets", GLOBAL_SSID, "--json"], capture_output=True, text=True)
sheets_g = json.loads(res_meta_g.stdout) if res_meta_g.returncode == 0 else []
sheet_id_g = None
for s in sheets_g:
    if s.get("title") == "All_DRP_Status":
        sheet_id_g = s.get("id")
        break

subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_DRP_Status'!A1:Z3000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_DRP_Status'!2:3000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_drp_dots_csv, "--sheet", "All_DRP_Status"], capture_output=True)

if sheet_id_g is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sheet_id_g), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sheet_id_g),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sheet_id_g),
        "--start-row", "1", "--end-row", "3000",
        "--start-col", "4", "--end-col", "7",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sheet_id_g), "--start-col", "0", "--end-col", "8"], capture_output=True)

print("\n==========================================")
print("ALL DRP TABS UPDATED WITH CAPACITY DOT INDICATORS (COL G / H)!")
print("==========================================")
