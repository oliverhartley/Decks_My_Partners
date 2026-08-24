import json
import csv
import subprocess
import os
import sys

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

PARTNER_CONFIGS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q",
        "cert_pids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
        "drp_keys": ["P20220602109", "0014M00001h39BLQAY", "0014M00001m9woLQAQ"]
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "cert_pids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
        "drp_keys": ["P20260318001", "0014M00002JmizDQAR"]
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "cert_pids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
        "drp_keys": ["P20220923084", "0014M00001h38aiQAA"]
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "cert_pids": ["0014M00002M7lcJQAR"],
        "drp_keys": ["0014M00002M7lcJQAR"]
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "cert_pids": ["0014M00001kxZPMQA2", "001Kf0000150rJ2IAI", "0014M00001m9v8HQAQ"],
        "drp_keys": ["P20220923297", "0014M00001kxZPMQA2", "001Kf0000150rJ2IAI"]
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "cert_pids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
        "drp_keys": ["P20220602104", "0014M00001uFlbSQAS"]
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "cert_pids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
        "drp_keys": ["P20231208017", "0014M00002GGNRCQA5"]
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "cert_pids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "0014M00002N5mLOQAZ"],
        "drp_keys": ["P20220923048", "0014M00001h35nAQAQ"]
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "cert_pids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "drp_keys": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"]
    },
]

DRP_HEADERS = [
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles"
]

ACCRED_HEADERS = [
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Entity"
]

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

os.makedirs("drp_data", exist_ok=True)
os.makedirs("accred_data", exist_ok=True)
drp_summary = []
accred_summary = []

for cfg in PARTNER_CONFIGS:
    pname = cfg["partner"]
    ssid = cfg["sheet_id"]
    drp_keys = cfg["drp_keys"]
    cert_pids = cfg["cert_pids"]
    
    print(f"\n==========================================")
    print(f"Building DRP & Accreditations for: {pname}")
    print(f"==========================================")
    
    # ==========================================
    # 1. DRP STATUS TAB
    # ==========================================
    drp_tab_title = "DRP_Status"
    drp_sheet_id = ensure_sheet_tab(ssid, drp_tab_title)
    print(f"Tab '{drp_tab_title}' sheet ID: {drp_sheet_id}")
    
    keys_str = ", ".join([f"\"{k}\"" for k in drp_keys])
    sql_drp = f"""
    SELECT 
      COALESCE(pillar, 'All Pillars') as pillar,
      COALESCE(sol, 'All Solutions') as solution,
      COALESCE(p.scored_product, 'All Products') as product,
      COUNT(DISTINCT IF(p.tier_category = 'Tier 1', p.profile_id, NULL)) as tier1_count,
      COUNT(DISTINCT IF(p.tier_category = 'Tier 2', p.profile_id, NULL)) as tier2_count,
      COUNT(DISTINCT IF(p.tier_category IN ('Tier 1', 'Tier 2'), p.profile_id, NULL)) as total_tier1_tier2
    FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
    LEFT JOIN UNNEST(p.parent_pillar) pillar
    LEFT JOIN UNNEST(p.sales_play) sol
    WHERE p.consolidated_partner_id IN ({keys_str})
    GROUP BY 1, 2, 3
    HAVING total_tier1_tier2 > 0
    ORDER BY pillar, solution, product
    """
    
    schema_drp, rows_drp = run_query(sql_drp)
    print(f"DRP Rows found: {len(rows_drp)}")
    
    drp_rows = [DRP_HEADERS]
    if rows_drp:
        for r in rows_drp:
            pillar = r["f"][0].get("v") or ""
            sol = r["f"][1].get("v") or ""
            prod = r["f"][2].get("v") or ""
            t1 = r["f"][3].get("v") or "0"
            t2 = r["f"][4].get("v") or "0"
            tot = r["f"][5].get("v") or "0"
            drp_rows.append([pillar, sol, prod, t1, t2, tot])
    else:
        drp_rows.append(["No DRP Tier 1 or Tier 2 profiles recorded", "-", "-", "0", "0", "0"])
        
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    drp_csv = os.path.join("drp_data", f"{safe_name}_drp.csv")
    with open(drp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(drp_rows)
        
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{drp_tab_title}'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{drp_tab_title}'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, drp_csv, "--sheet", drp_tab_title], capture_output=True)
    
    if drp_sheet_id is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(drp_sheet_id), "--rows", "1"], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(drp_sheet_id),
            "--start-row", "0", "--end-row", "1",
            "--start-col", "0", "--end-col", "6",
            "--bold",
            "--bg-color", "#E8F0FE",
            "--align", "CENTER",
            "--wrap"
        ], capture_output=True)
        # Center numerical columns (col 3, 4, 5)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(drp_sheet_id),
            "--start-row", "1", "--end-row", "1000",
            "--start-col", "3", "--end-col", "6",
            "--align", "CENTER"
        ], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(drp_sheet_id), "--start-col", "0", "--end-col", "6"], capture_output=True)
    
    # ==========================================
    # 2. ACCREDITATIONS TAB
    # ==========================================
    accred_tab_title = "Acreditaciones"
    accred_sheet_id = ensure_sheet_tab(ssid, accred_tab_title)
    print(f"Tab '{accred_tab_title}' sheet ID: {accred_sheet_id}")
    
    pids_str = ", ".join([f"\"{x}\"" for x in cert_pids])
    sql_certs = f"""
    SELECT 
      p.certification_details.certification_name,
      p.certification_details.certification_type,
      p.certification_details.certification_sub_type,
      p.partner_contact_profile_details.profile_name,
      p.partner_contact_profile_details.lms_user_email,
      CAST(p.certification_details.certification_issued_date AS STRING) as issued_date,
      CAST(p.certification_details.certification_expiration_date AS STRING) as expiration_date,
      p.partner_details.partner_name
    FROM `concord-prod.service_cloudbi.partner_certifications` p
    WHERE p.partner_details.sfdc_partner_id IN ({pids_str})
      AND p.reporting_month = (SELECT MAX(reporting_month) FROM `concord-prod.service_cloudbi.partner_certifications`)
    ORDER BY p.certification_details.certification_type, p.certification_details.certification_name, p.partner_contact_profile_details.profile_name
    """
    
    schema_certs, rows_certs = run_query(sql_certs)
    print(f"Active Certifications/Accreditations found: {len(rows_certs)}")
    
    accred_rows = [ACCRED_HEADERS]
    if rows_certs:
        for r in rows_certs:
            cname = r["f"][0].get("v") or ""
            ctype = r["f"][1].get("v") or ""
            csubtype = r["f"][2].get("v") or ""
            pname_cand = r["f"][3].get("v") or ""
            pemail_cand = r["f"][4].get("v") or ""
            issued = r["f"][5].get("v") or ""
            exp = r["f"][6].get("v") or ""
            entity = r["f"][7].get("v") or ""
            accred_rows.append([cname, ctype, csubtype, pname_cand, pemail_cand, issued, exp, entity])
    else:
        accred_rows.append(["No active accreditations found", "-", "-", "-", "-", "-", "-", "-"])
        
    accred_csv = os.path.join("accred_data", f"{safe_name}_accred.csv")
    with open(accred_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(accred_rows)
        
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{accred_tab_title}'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{accred_tab_title}'!2:2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, accred_csv, "--sheet", accred_tab_title], capture_output=True)
    
    if accred_sheet_id is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(accred_sheet_id), "--rows", "1"], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(accred_sheet_id),
            "--start-row", "0", "--end-row", "1",
            "--start-col", "0", "--end-col", "8",
            "--bold",
            "--bg-color", "#E8F0FE",
            "--align", "CENTER",
            "--wrap"
        ], capture_output=True)
        # Center Dates (col 5, 6)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(accred_sheet_id),
            "--start-row", "1", "--end-row", "2000",
            "--start-col", "5", "--end-col", "7",
            "--align", "CENTER"
        ], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(accred_sheet_id), "--start-col", "0", "--end-col", "8"], capture_output=True)
        
    drp_summary.append({"partner": pname, "drp_categories_count": len(rows_drp)})
    accred_summary.append({"partner": pname, "active_accreditations_count": len(rows_certs)})

print("\n==========================================")
print("ALL 9 PARTNER SPREADSHEETS FULLY POPULATED WITH DRP_Status AND Acreditaciones TABS!")
print("==========================================")
print("DRP Summary:", json.dumps(drp_summary, indent=2))
print("Accreditations Summary:", json.dumps(accred_summary, indent=2))
with open("drp_summary.json", "w") as f:
    json.dump(drp_summary, f, indent=2)
with open("accred_summary.json", "w") as f:
    json.dump(accred_summary, f, indent=2)
