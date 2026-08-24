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
        "partner_ids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
        "default_pid": "0014M00001h39BLQAY"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "partner_ids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
        "default_pid": "0014M00002JmizDQAR"
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "partner_ids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
        "default_pid": "0014M00001h38aiQAA"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "partner_ids": ["0014M00002M7lcJQAR"],
        "default_pid": "0014M00002M7lcJQAR"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "partner_ids": ["001Kf0000150rJ2IAI", "0014M00001kxZPMQA2", "0014M00001m9v8HQAQ"],
        "default_pid": "0014M00001kxZPMQA2"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "partner_ids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
        "default_pid": "0014M00001uFlbSQAS"
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "partner_ids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
        "default_pid": "0014M00002GGNRCQA5"
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "partner_ids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "001Kf000010cw8CIAQ", "0014M00002N5mLOQAZ"],
        "default_pid": "0014M00001h35nAQAQ"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "partner_ids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "default_pid": "001Kf000013fuVXIAY"
    },
]

HEADERS = [
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
    "Annual Gross Revenue (ARR USD)"
]

def make_hyperlink(url, label):
    if not url or not label:
        return label or ""
    clean_label = str(label).replace('"', '""')
    return f'=HYPERLINK("{url}", "{clean_label}")'

def parse_expert_requests(er_raw):
    if not er_raw or not isinstance(er_raw, dict):
        return ""
    f_list = er_raw.get("f", [])
    if not f_list:
        return ""
    items = f_list[0].get("v", [])
    if not items or not isinstance(items, list):
        return ""
    
    er_entries = []
    for item in items:
        val = item.get("v", {})
        if isinstance(val, dict) and "f" in val:
            fields = val["f"]
            er_name = fields[3].get("v") if len(fields) > 3 else ""
            er_id = fields[10].get("v") if len(fields) > 10 else ""
            if er_name:
                er_entries.append((er_name, er_id))
    
    if not er_entries:
        return ""
    
    if len(er_entries) == 1:
        name, er_id = er_entries[0]
        if er_id:
            return make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Expert_Request__c/{er_id}/view", name)
        return name
    else:
        return ", ".join([e[0] for e in er_entries])

def get_account_tier(segment_val):
    if not segment_val:
        return "3"
    s = str(segment_val).strip().lower()
    if "enterprise" in s or s == "1":
        return "1"
    elif "corporate" in s or s == "2":
        return "2"
    else:
        return "3"

os.makedirs("followup_data_v3", exist_ok=True)
summary_results = []

for cfg in PARTNER_CONFIGS:
    pname = cfg["partner"]
    ssid = cfg["sheet_id"]
    default_pid = cfg["default_pid"]
    pids = ", ".join([f"\"{x}\"" for x in cfg["partner_ids"]])
    
    print(f"\n==========================================")
    print(f"Processing Strictly Dedicated Partner: {pname}")
    print(f"==========================================")
    
    sql = f"""
    SELECT 
      w.workload_id,
      w.workload_name,
      w.opportunity_id,
      o.opportunity_name,
      COALESCE(w.sfdc_account_id, o.sfdc_account_id) AS sfdc_account_id,
      COALESCE(w.customer.account_name, o.account_name) AS account_name,
      COALESCE(w.customer.segment, o.segment) AS segment,
      COALESCE(w.customer.sub_region, o.sub_region) AS sub_region,
      COALESCE(w.customer.micro_region, o.micro_region) AS micro_region,
      w.workload_details.primary_workload_pillar,
      w.workload_details.workload_progress,
      CAST(w.workload_details.begin_migration_date AS STRING) AS begin_migration_date,
      CAST(w.workload_details.production_date AS STRING) AS production_date,
      w.metrics.annual_gross_revenue,
      w.expert_request,
      w.workload_details.partner_id,
      w.workload_details.partner_name,
      CAST(w.workload_details.sfdc_created_date AS STRING) AS sfdc_created_date
    FROM `concord-prod.service_cloudbi.workloads` w
    LEFT JOIN `concord-prod.service_cloudbi.opportunities` o
      ON w.opportunity_id = o.opportunity_id
    WHERE w.workload_details.partner_id IN ({pids})
      AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
      AND (w.workload_details.workload_progress IS NULL OR (
             LOWER(w.workload_details.workload_progress) NOT LIKE "%closed%"
             AND w.workload_details.workload_progress NOT LIKE "5.%"
          ))
    ORDER BY w.workload_details.sfdc_created_date DESC, w.metrics.annual_gross_revenue DESC
    """
    
    schema, rows = run_query(sql)
    print(f"Found {len(rows)} strictly dedicated open 2025+ workloads.")
    
    csv_rows = [HEADERS]
    for r in rows:
        cells = r["f"]
        workload_id = cells[0].get("v") or ""
        workload_name = cells[1].get("v") or ""
        opportunity_id = cells[2].get("v") or ""
        opportunity_name = cells[3].get("v") or ""
        account_id = cells[4].get("v") or ""
        account_name = cells[5].get("v") or ""
        segment = cells[6].get("v") or ""
        sub_region = cells[7].get("v") or ""
        micro_region = cells[8].get("v") or ""
        pillar = cells[9].get("v") or ""
        progress = cells[10].get("v") or ""
        begin_migration_date = cells[11].get("v") or ""
        production_date = cells[12].get("v") or ""
        arr = cells[13].get("v") or "0"
        er_raw = cells[14].get("v")
        row_partner_id = cells[15].get("v") or default_pid
        row_partner_name = cells[16].get("v") or pname
        
        # 0. Partner Name Hyperlink (Column A)
        p_url = f"https://vector.lightning.force.com/lightning/r/Account/{row_partner_id}/view" if row_partner_id else ""
        p_linked = make_hyperlink(p_url, row_partner_name) if p_url else row_partner_name
        
        # 1. Account Name Hyperlink (Column B)
        acc_url = f"https://vector.lightning.force.com/lightning/r/Account/{account_id}/view" if account_id else ""
        acc_display = account_name if account_name else (account_id if account_id else "N/A")
        acc_linked = make_hyperlink(acc_url, acc_display) if acc_url else acc_display
        
        # 2. Account Tier (Column C: 1, 2, or 3)
        acc_tier = get_account_tier(segment)
        
        # 3. Workload Name Hyperlink (Column D)
        wkl_url = f"https://vector.lightning.force.com/lightning/r/Workload__c/{workload_id}/view" if workload_id else ""
        wkl_display = workload_name if workload_name else (workload_id if workload_id else "N/A")
        wkl_linked = make_hyperlink(wkl_url, wkl_display) if wkl_url else wkl_display
        
        # 4. Opportunity Name Hyperlink (Column E)
        opp_url = f"https://vector.lightning.force.com/lightning/r/Opportunity/{opportunity_id}/view" if opportunity_id else ""
        opp_display = opportunity_name if opportunity_name else (opportunity_id if opportunity_id else "")
        opp_linked = make_hyperlink(opp_url, opp_display) if opp_url and opp_display else opp_display
        
        # 5. Expert Requests (Column F)
        er_linked = parse_expert_requests(er_raw)
        
        # 12. ARR formatting (Column M)
        try:
            arr_float = float(arr)
            arr_formatted = f"{arr_float:,.2f}"
        except:
            arr_formatted = arr
            
        csv_rows.append([
            p_linked,
            acc_linked,
            acc_tier,
            wkl_linked,
            opp_linked,
            er_linked,
            sub_region,
            micro_region,
            pillar,
            progress,
            begin_migration_date,
            production_date,
            arr_formatted
        ])
        
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    csv_file = os.path.join("followup_data_v3", f"{safe_name}_v3.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    print(f"Written CSV: {csv_file}")
    
    # Update Spreadsheet tab
    tab_title = "Follow_up"
    print(f"Clearing old content in '{tab_title}'...")
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_title}'!A1:Z5000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_title}'!2:5000"], capture_output=True)
    
    print(f"Importing CSV to '{tab_title}'...")
    imp_res = subprocess.run([GSHEETS, "mutate", "import-csv", ssid, csv_file, "--sheet", tab_title], capture_output=True, text=True)
    if imp_res.returncode != 0:
        print(f"Error importing CSV: {imp_res.stderr} - {imp_res.stdout}")
    else:
        print("Import successful.")
        
    print("Applying formatting...")
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", "0", "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "13",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    
    # Align Account Tier column (col index 2) to CENTER
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "1", "--end-row", "5000",
        "--start-col", "2", "--end-col", "3",
        "--align", "CENTER"
    ], capture_output=True)
    
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", "0", "--start-col", "0", "--end-col", "13"], capture_output=True)
    
    summary_results.append({
        "partner": pname,
        "spreadsheet_id": ssid,
        "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{ssid}/edit#gid=0",
        "workloads_count": len(rows)
    })

print("\n\n==========================================")
print("ALL 9 PARTNER FOLLOWUP SHEETS UPDATED WITH ACCOUNT TIER (1, 2, 3)!")
print("==========================================")
print(json.dumps(summary_results, indent=2))
with open("followup_summary_v3.json", "w") as f:
    json.dump(summary_results, f, indent=2)
