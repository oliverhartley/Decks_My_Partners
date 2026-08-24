import json
import csv
import subprocess
import os
import sys

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

PARTNER_CONFIGS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q",
        "partner_ids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
        "drp_keys": ["P20220602109", "0014M00001h39BLQAY", "0014M00001m9woLQAQ"],
        "default_pid": "0014M00001h39BLQAY"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "partner_ids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
        "drp_keys": ["P20260318001", "0014M00002JmizDQAR"],
        "default_pid": "0014M00002JmizDQAR"
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "partner_ids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
        "drp_keys": ["P20220923084", "0014M00001h38aiQAA"],
        "default_pid": "0014M00001h38aiQAA"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "partner_ids": ["0014M00002M7lcJQAR"],
        "drp_keys": ["0014M00002M7lcJQAR"],
        "default_pid": "0014M00002M7lcJQAR"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "partner_ids": ["001Kf0000150rJ2IAI", "0014M00001kxZPMQA2", "0014M00001m9v8HQAQ"],
        "drp_keys": ["P20220923297", "0014M00001kxZPMQA2", "001Kf0000150rJ2IAI"],
        "default_pid": "0014M00001kxZPMQA2"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "partner_ids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
        "drp_keys": ["P20220602104", "0014M00001uFlbSQAS"],
        "default_pid": "0014M00001uFlbSQAS"
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "partner_ids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
        "drp_keys": ["P20231208017", "0014M00002GGNRCQA5"],
        "default_pid": "0014M00002GGNRCQA5"
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "partner_ids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "001Kf000010cw8CIAQ", "0014M00002N5mLOQAZ"],
        "drp_keys": ["P20220923048", "0014M00001h35nAQAQ"],
        "default_pid": "0014M00001h35nAQAQ"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "partner_ids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "drp_keys": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "default_pid": "001Kf000013fuVXIAY"
    }
]

FOLLOWUP_HEADERS = [
    "Partner Name",
    "Customer Account Name",
    "Account Tier",
    "Workload Name",
    "Opportunity Name",
    "Expert Requests",
    "Customer Sub Region",
    "Customer Micro Region",
    "Primary Workload Pillar",
    "Sales Play",
    "Workload Solution",
    "Workload Progress",
    "Begin Migration Date",
    "Production Date",
    "Annual Gross Revenue (ARR USD)",
    "Capacity Status (DRP Readiness)",
    "Last Touch",
    "Link"
]

DRP_HEADERS = [
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
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

def fetch_existing_manual_entries(ssid):
    manual_entries = {}
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Follow_up'!A1:R500", "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            if data and len(data) > 1:
                header_row = data[0]
                lt_idx = -1
                link_idx = -1
                wkl_idx = -1
                for idx, h in enumerate(header_row):
                    h_clean = str(h).strip().lower()
                    if "last touch" in h_clean:
                        lt_idx = idx
                    elif "link" in h_clean:
                        link_idx = idx
                    elif "workload name" in h_clean:
                        wkl_idx = idx
                if wkl_idx >= 0:
                    for row in data[1:]:
                        if len(row) > wkl_idx and row[wkl_idx]:
                            w_name = str(row[wkl_idx]).strip()
                            lt_val = str(row[lt_idx]).strip() if lt_idx >= 0 and len(row) > lt_idx else ""
                            link_val = str(row[link_idx]).strip() if link_idx >= 0 and len(row) > link_idx else ""
                            if lt_val or link_val:
                                manual_entries[w_name] = {"last_touch": lt_val, "link": link_val}
        except:
            pass
    return manual_entries

# 1. Fetch DRP Catalog
sql_catalog = """
SELECT DISTINCT
  pillar,
  sol as solution,
  COALESCE(p.scored_product, 'All Products') as product
FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
CROSS JOIN UNNEST(p.parent_pillar) pillar
CROSS JOIN UNNEST(p.sales_play) sol
WHERE pillar IS NOT NULL AND sol IS NOT NULL
ORDER BY pillar, solution, product
"""
schema_cat, rows_cat = run_query(sql_catalog)
drp_catalog = [(r["f"][0].get("v"), r["f"][1].get("v"), r["f"][2].get("v")) for r in rows_cat]

def match_workload_to_drp(w_pillar, w_sales_play, w_solution, w_prods):
    matches = []
    p_text = f"{w_pillar} {w_sales_play} {w_solution} {' '.join(w_prods or [])}".lower()
    
    for c_pillar, c_sol, c_prod in drp_catalog:
        c_prod_lower = c_prod.lower()
        c_sol_lower = c_sol.lower()
        c_pil_lower = c_pillar.lower()
        
        if c_prod_lower in p_text and c_prod_lower != "all products":
            matches.append((c_pillar, c_sol, c_prod))
        elif "gke" in p_text and "kubernetes" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "cloudrun" in p_text and "cloud run" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "vmware" in p_text and "vmware" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "oracle" in p_text and "oracle" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "sap" in p_text and "sap" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "bigquery" in p_text and "bigquery" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "looker" in p_text and "looker" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "alloydb" in p_text and "alloydb" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "cloud sql" in p_text and "cloud sql" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "spanner" in p_text and "spanner" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "gemini" in p_text and ("gemini" in c_prod_lower or "ai" in c_sol_lower):
            matches.append((c_pillar, c_sol, c_prod))
        elif "security" in p_text and c_pil_lower == "security":
            matches.append((c_pillar, c_sol, c_prod))
            
    if not matches:
        # Fallback to pillar matches
        for c_pillar, c_sol, c_prod in drp_catalog:
            if c_pillar.lower() in p_text or ("ai" in p_text and c_pillar == "Artificial Intelligence"):
                matches.append((c_pillar, c_sol, c_prod))
    return list(set(matches))

# Directories
os.makedirs("followup_data_v5", exist_ok=True)
os.makedirs("drp_data_v5", exist_ok=True)

all_global_followup_rows = [FOLLOWUP_HEADERS]
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

for cfg in PARTNER_CONFIGS:
    pname = cfg["partner"]
    ssid = cfg["sheet_id"]
    pids = ", ".join([f"\"{x}\"" for x in cfg["partner_ids"]])
    drp_keys_str = ", ".join([f"\"{x}\"" for x in cfg["drp_keys"]])
    default_pid = cfg["default_pid"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    
    print(f"\n==========================================")
    print(f"Processing Full Correlation for: {pname}")
    print(f"==========================================")
    
    # 1. Fetch DRP Profile Counts for this partner
    sql_drp = f"""
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
      WHERE p.consolidated_partner_id IN ({drp_keys_str})
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
    _, drp_bq_rows = run_query(sql_drp)
    partner_drp_map = {} # (pillar, sol, prod) -> {"t1": X, "t2": Y, "tot": Z}
    for r in drp_bq_rows:
        pil = r["f"][0].get("v")
        sol = r["f"][1].get("v")
        prd = r["f"][2].get("v")
        t1 = int(r["f"][3].get("v") or 0)
        t2 = int(r["f"][4].get("v") or 0)
        tot = int(r["f"][5].get("v") or 0)
        partner_drp_map[(pil, sol, prd)] = {"t1": t1, "t2": t2, "tot": tot}
        
    # 2. Fetch Workloads for this partner
    manual_entries = fetch_existing_manual_entries(ssid)
    sql_wkl = f"""
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
      w.workload_details.sales_play,
      w.workload_details.workload_solutions,
      w.workload_details.workload_progress,
      CAST(w.workload_details.begin_migration_date AS STRING) AS begin_migration_date,
      CAST(w.workload_details.production_date AS STRING) AS production_date,
      w.metrics.annual_gross_revenue,
      w.expert_request,
      w.workload_details.partner_id,
      w.workload_details.partner_name,
      CAST(w.workload_details.sfdc_created_date AS STRING) AS sfdc_created_date,
      w.workload_details.key_workload_products
    FROM `concord-prod.service_cloudbi.workloads` w
    LEFT JOIN `concord-prod.service_cloudbi.opportunities` o
      ON w.opportunity_id = o.opportunity_id
    WHERE w.workload_details.partner_id IN ({pids})
      AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
      AND (w.workload_details.workload_progress IS NULL OR (
             LOWER(w.workload_details.workload_progress) NOT LIKE "%closed%"
             AND w.workload_details.workload_progress NOT LIKE "5.%"
          ))
      AND COALESCE(w.customer.segment, o.segment) != "Enterprise"
      AND IFNULL(o.is_commit, FALSE) = FALSE 
      AND IFNULL(o.forecast_category_name, "") != "Commit"
    ORDER BY w.workload_details.sfdc_created_date DESC, w.metrics.annual_gross_revenue DESC
    """
    _, wkl_bq_rows = run_query(sql_wkl)
    print(f"Found {len(wkl_bq_rows)} workloads for {pname}")
    
    # Count workload demand per DRP item
    drp_workload_demand = {(pil, sol, prd): 0 for (pil, sol, prd) in drp_catalog}
    
    followup_rows = [FOLLOWUP_HEADERS]
    for r in wkl_bq_rows:
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
        sales_play = cells[10].get("v") or ""
        workload_solution = cells[11].get("v") or ""
        progress = cells[12].get("v") or ""
        begin_migration_date = cells[13].get("v") or ""
        production_date = cells[14].get("v") or ""
        arr_val = cells[15].get("v") or "0"
        er_raw = cells[16].get("v")
        row_partner_id = cells[17].get("v") or default_pid
        row_partner_name = cells[18].get("v") or pname
        key_prods_raw = cells[20].get("v") if len(cells) > 20 else []
        key_prods = [x.get("v") for x in key_prods_raw] if isinstance(key_prods_raw, list) else []
        
        # Hyperlinks
        p_url = f"https://vector.lightning.force.com/lightning/r/Account/{row_partner_id}/view" if row_partner_id else ""
        p_linked = make_hyperlink(p_url, row_partner_name) if p_url else row_partner_name
        
        acc_url = f"https://vector.lightning.force.com/lightning/r/Account/{account_id}/view" if account_id else ""
        acc_linked = make_hyperlink(acc_url, account_name) if acc_url else account_name
        
        wkl_url = f"https://vector.lightning.force.com/lightning/r/Workload__c/{workload_id}/view" if workload_id else ""
        wkl_linked = make_hyperlink(wkl_url, workload_name) if wkl_url else workload_name
        
        opp_url = f"https://vector.lightning.force.com/lightning/r/Opportunity/{opportunity_id}/view" if opportunity_id else ""
        opp_linked = make_hyperlink(opp_url, opportunity_name) if opp_url else opportunity_name
        
        er_linked = parse_expert_requests(er_raw)
        tier = get_account_tier(segment)
        try:
            arr_formatted = f"{float(arr_val):,.2f}"
        except:
            arr_formatted = "0.00"
            
        # Match to DRP to compute capacity semaforo for this workload
        matched_drp = match_workload_to_drp(pillar, sales_play, workload_solution, key_prods)
        for m_item in matched_drp:
            drp_workload_demand[m_item] = drp_workload_demand.get(m_item, 0) + 1
            
        # Total DRP capacity available for this workload's technology
        total_drp_for_wkl = 0
        if matched_drp:
            total_drp_for_wkl = sum(partner_drp_map.get(m, {}).get("tot", 0) for m in matched_drp)
            
        if total_drp_for_wkl == 0:
            wkl_capacity_status = "🔴 Capacity Gap (0 DRP Profiles)"
        elif total_drp_for_wkl == 1:
            wkl_capacity_status = "🟡 Constrained (1 DRP Profile)"
        else:
            wkl_capacity_status = f"🟢 Ready ({total_drp_for_wkl} DRP Profiles)"
            
        # Manual edits preservation
        lt_preserved = ""
        link_preserved = ""
        if workload_name in manual_entries:
            lt_preserved = manual_entries[workload_name].get("last_touch", "")
            link_preserved = manual_entries[workload_name].get("link", "")
            
        row_followup = [
            p_linked,
            acc_linked,
            tier,
            wkl_linked,
            opp_linked,
            er_linked,
            sub_region,
            micro_region,
            pillar,
            sales_play,
            workload_solution,
            progress,
            begin_migration_date,
            production_date,
            arr_formatted,
            wkl_capacity_status,
            lt_preserved,
            link_preserved
        ]
        followup_rows.append(row_followup)
        all_global_followup_rows.append(row_followup)
        
    # Write Partner Follow_up CSV
    followup_csv = os.path.join("followup_data_v5", f"{safe_name}_followup_v5.csv")
    with open(followup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(followup_rows)
        
    # Import into Partner Sheet Follow_up
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Follow_up'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, followup_csv, "--sheet", "Follow_up"], capture_output=True)
    
    # Format Follow_up
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", "0", "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "18",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    # Highlight manual columns Col 16 (Q) & Col 17 (R)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "0", "--end-row", "1",
        "--start-col", "16", "--end-col", "18",
        "--bold",
        "--bg-color", "#E6F4EA",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    # Center Tier & Capacity
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "1", "--end-row", "1000",
        "--start-col", "2", "--end-col", "3",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "1", "--end-row", "1000",
        "--start-col", "15", "--end-col", "16",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", "0", "--start-col", "0", "--end-col", "18"], capture_output=True)
    
    # 3. Build Partner DRP Tab with Exact Product-Level Demand Matching
    drp_rows = [DRP_HEADERS]
    for (pil, sol, prd) in drp_catalog:
        d_info = partner_drp_map.get((pil, sol, prd), {"t1": 0, "t2": 0, "tot": 0})
        t1_str = str(d_info["t1"]) if d_info["t1"] > 0 else ""
        t2_str = str(d_info["t2"]) if d_info["t2"] > 0 else ""
        tot_val = d_info["tot"]
        tot_str = str(tot_val) if tot_val > 0 else ""
        
        w_demand = drp_workload_demand.get((pil, sol, prd), 0)
        
        if w_demand > 0 and tot_val == 0:
            status_dot = f"🔴 Gap (0 DRP / {w_demand} wkls)"
        elif w_demand > 0 and tot_val < w_demand:
            status_dot = f"🟡 Constrained ({tot_val} DRP / {w_demand} wkls)"
        elif tot_val >= w_demand and (tot_val > 0 or w_demand > 0):
            status_dot = f"🟢 Ready ({tot_val} DRP / {w_demand} wkls)" if w_demand > 0 else f"🟢 Ready ({tot_val} profiles)"
        else:
            status_dot = "⚪ No Active Demand"
            
        drp_rows.append([pil, sol, prd, t1_str, t2_str, tot_str, status_dot])
        all_global_drp_rows.append([pname, pil, sol, prd, t1_str, t2_str, tot_str, status_dot])
        
    drp_csv = os.path.join("drp_data_v5", f"{safe_name}_drp_v5.csv")
    with open(drp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(drp_rows)
        
    # Find DRP sheet ID
    tab_drp = "DRP_Status"
    res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    sheets = json.loads(res_meta.stdout) if res_meta.returncode == 0 else []
    sid_drp = None
    for s in sheets:
        if s.get("title") == tab_drp:
            sid_drp = s.get("id")
            break
            
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_drp}'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_drp}'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, drp_csv, "--sheet", tab_drp], capture_output=True)
    
    if sid_drp is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_drp), "--rows", "1"], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sid_drp),
            "--start-row", "0", "--end-row", "1",
            "--start-col", "0", "--end-col", "7",
            "--bold",
            "--bg-color", "#E8F0FE",
            "--align", "CENTER",
            "--wrap"
        ], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sid_drp),
            "--start-row", "1", "--end-row", "1000",
            "--start-col", "3", "--end-col", "6",
            "--align", "CENTER"
        ], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_drp), "--start-col", "0", "--end-col", "7"], capture_output=True)
    print(f"Updated {pname} Follow_up & DRP_Status with full product-level capacity indicators!")

# =========================================================================
# UPDATE GLOBAL MASTER DASHBOARD
# =========================================================================
print("\n==========================================")
print("Updating Global Master Dashboard Tabs")
print("==========================================")

# 1. Global All_Workloads_Follow_up
global_followup_csv = "global_dashboard_data/all_workloads_followup_v5.csv"
with open(global_followup_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_followup_rows)

res_meta_g = subprocess.run([GSHEETS, "readonly", "list-sheets", GLOBAL_SSID, "--json"], capture_output=True, text=True)
sheets_g = json.loads(res_meta_g.stdout) if res_meta_g.returncode == 0 else []
sid_gwkl = None
sid_gdrp = None
for s in sheets_g:
    if s.get("title") == "All_Workloads_Follow_up":
        sid_gwkl = s.get("id")
    elif s.get("title") == "All_DRP_Status":
        sid_gdrp = s.get("id")

subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Workloads_Follow_up'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Workloads_Follow_up'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_followup_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True)

if sid_gwkl is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_gwkl), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "18",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "16", "--end-col", "18",
        "--bold",
        "--bg-color", "#E6F4EA",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "1", "--end-row", "5000",
        "--start-col", "2", "--end-col", "3",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "1", "--end-row", "5000",
        "--start-col", "15", "--end-col", "16",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid_gwkl), "--start-col", "0", "--end-col", "18"], capture_output=True)

# 2. Global All_DRP_Status
global_drp_csv = "global_dashboard_data/all_drp_status_v5.csv"
with open(global_drp_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_drp_rows)

subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_DRP_Status'!A1:Z3000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_DRP_Status'!2:3000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_drp_csv, "--sheet", "All_DRP_Status"], capture_output=True)

if sid_gdrp is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_gdrp), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gdrp),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gdrp),
        "--start-row", "1", "--end-row", "3000",
        "--start-col", "4", "--end-col", "7",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid_gdrp), "--start-col", "0", "--end-col", "8"], capture_output=True)

print("\n==========================================")
print("ALL SHEETS UPDATED WITH SALES PLAY, WORKLOAD SOLUTION, AND CAPACITY RAG SEMAPHORES!")
print("==========================================")
