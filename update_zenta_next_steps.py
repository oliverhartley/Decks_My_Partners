import json
import csv
import subprocess
import os
import sys
import datetime

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners")
from query_bq import run_query

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

now = datetime.datetime.now()
DATE_FORMATTED = f"{now.day} - {now.strftime('%b')} {now.year}"

ZENTA_CFG = {
    "partner": "Comercializadora Zenta Group SPA",
    "pe": "Oliver Hartley",
    "sheet_id": "1fkfQ5BFGu9tPyPUlxgWAK_NeA2gGiAn1TChTYP1R0d0",
    "partner_ids": [
        "0014M00001h39BLQAY",
        "0014M00001m9woLQAQ",
        "001Kf000012gqs3IAA"
    ],
    "cert_pids": [
        "0014M00001h39BLQAY",
        "0014M00001m9woLQAQ",
        "001Kf000012gqs3IAA"
    ],
    "drp_keys": [
        "P20220602109",
        "0014M00001h39BLQAY",
        "0014M00001m9woLQAQ",
        "001Kf000012gqs3IAA"
    ],
    "default_pid": "0014M00001h39BLQAY",
    "country": "Chile",
    "tier_level": "Premier"
}

# 19 Columns for Partner Trackers (with Next Steps between Opportunity Name and Expert Requests)
PARTNER_FOLLOWUP_HEADERS = [
    "Customer Account Name",            # Col 0 (A)
    "Account Tier",                     # Col 1 (B)
    "Workload Name",                    # Col 2 (C)
    "Workload Owner",                   # Col 3 (D)
    "Workload Progress",                # Col 4 (E)
    "Capacity Status (DRP Readiness)",  # Col 5 (F)
    "Opportunity Name",                 # Col 6 (G)
    "Next Steps",                       # Col 7 (H)  <-- NEW COLUMN!
    "Expert Requests",                  # Col 8 (I)
    "Customer Sub Region",              # Col 9 (J)
    "Customer Micro Region",            # Col 10 (K)
    "Primary Workload Pillar",          # Col 11 (L)
    "Sales Play",                       # Col 12 (M)
    "Workload Solution",                # Col 13 (N)
    "Begin Migration Date",             # Col 14 (O)
    "Production Date",                  # Col 15 (P)
    "Annual Gross Revenue (ARR USD)",   # Col 16 (Q)
    "Last Touch",                       # Col 17 (R)
    "Link"                              # Col 18 (S)
]

PARTNER_COL_WIDTHS = {
    0: 280,  # Customer Account Name
    1: 90,   # Account Tier
    2: 240,  # Workload Name
    3: 180,  # Workload Owner
    4: 170,  # Workload Progress
    5: 200,  # Capacity Status
    6: 260,  # Opportunity Name
    7: 350,  # Next Steps
    8: 180,  # Expert Requests
    9: 120,  # Customer Sub Region
    10: 130, # Customer Micro Region
    11: 180, # Primary Workload Pillar
    12: 260, # Sales Play
    13: 240, # Workload Solution
    14: 130, # Begin Migration Date
    15: 130, # Production Date
    16: 150, # ARR USD
    17: 160, # Last Touch
    18: 160  # Link
}

def make_hyperlink(url, label):
    if not url or not label:
        return label or ""
    clean_label = str(label).replace('"', '""')
    return f'=HYPERLINK("{url}", "{clean_label}")'

def parse_expert_requests(er_raw):
    if not er_raw:
        return ""
    items = []
    if isinstance(er_raw, dict):
        items = er_raw.get("details", [])
    elif isinstance(er_raw, list):
        items = er_raw
    else:
        return str(er_raw)
        
    er_entries = []
    for item in items:
        if isinstance(item, dict):
            er_id = item.get("expert_request_id", "")
            er_name = item.get("name", "")
            disp = er_name if er_name else er_id
            if er_id:
                url = f"https://vector.lightning.force.com/lightning/r/Expert_Request__c/{er_id}/view"
                er_entries.append((disp, url))
            elif disp:
                er_entries.append((disp, ""))
                
    if not er_entries:
        return ""
    if len(er_entries) == 1:
        name, url = er_entries[0]
        return make_hyperlink(url, name) if url else name
    return ", ".join([e[0] for e in er_entries])

def get_account_tier(segment_val):
    if not segment_val:
        return "3"
    s = str(segment_val).strip().lower()
    if any(k in s for k in ["select", "tier 2", "tier2", "t2"]):
        return "2"
    else:
        return "3"

def fetch_existing_manual_entries(ssid, tab_title="Follow_up"):
    manual_entries = {}
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, f"'{tab_title}'!A1:Z500", "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            if data and len(data) > 1:
                header_row_idx = -1
                lt_idx = -1
                link_idx = -1
                wkl_idx = -1
                for r_idx, row in enumerate(data):
                    for idx, h in enumerate(row):
                        h_clean = str(h).strip().lower()
                        if "workload name" in h_clean:
                            wkl_idx = idx
                            header_row_idx = r_idx
                        elif "last touch" in h_clean:
                            lt_idx = idx
                        elif "link" in h_clean:
                            link_idx = idx
                    if wkl_idx >= 0:
                        break
                if wkl_idx >= 0 and header_row_idx >= 0:
                    for row in data[header_row_idx + 1:]:
                        if len(row) > wkl_idx and row[wkl_idx]:
                            w_name = str(row[wkl_idx]).strip()
                            lt_val = str(row[lt_idx]).strip() if lt_idx >= 0 and len(row) > lt_idx else ""
                            link_val = str(row[link_idx]).strip() if link_idx >= 0 and len(row) > link_idx else ""
                            if lt_val.lower() == "last touch":
                                lt_val = ""
                            if link_val.lower() == "link":
                                link_val = ""
                            if lt_val or link_val:
                                manual_entries[w_name] = {"last_touch": lt_val, "link": link_val}
        except Exception as e:
            print(f"Error fetching manual entries for {ssid}: {e}")
    return manual_entries

def get_grid_info(ssid):
    info = {}
    res = subprocess.run([GSHEETS, "readonly", "get", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            data = json.loads(res.stdout)
            for s in data.get("sheets", []):
                p = s.get("properties", {})
                title = p.get("title")
                gp = p.get("gridProperties", {})
                info[title] = {
                    "sheetId": p.get("sheetId"),
                    "rowCount": gp.get("rowCount", 1000),
                    "columnCount": gp.get("columnCount", 26)
                }
        except Exception as e:
            print(f"Error getting grid info for {ssid}: {e}")
    return info

def match_exact_drp(w_pillar, w_sales_play, w_solution, w_prods):
    w_pil_clean = (w_pillar or "").strip().lower()
    w_play_clean = (w_sales_play or "").strip().lower()
    w_sol_clean = (w_solution or "").strip().lower()
    w_prods_clean = [str(x).strip().lower() for x in (w_prods or [])]
    full_text = f"{w_pil_clean} {w_play_clean} {w_sol_clean} {' '.join(w_prods_clean)}"
    
    if "gemini enterprise" in full_text and ("workplace" in full_text or "licencias" in full_text or "seat" in full_text or "not a solution" in w_sol_clean or w_sol_clean == "gemini enterprise"):
        return [("Artificial Intelligence", "Agentic Workplace Transformation", "Gemini Enterprise")]
    
    if "gemini" in full_text and ("customer experience" in full_text or "ccaas" in full_text or "contact center" in full_text):
        return [("Artificial Intelligence", "Gemini Enterprise for Customer Experience", "Gemini Enterprise Agent Platform")]
        
    if "generative media" in full_text:
        return [("Artificial Intelligence", "Leverage Generative Media in your Business", "Gemini Enterprise Agent Platform")]
        
    if "your models" in full_text or "your business" in full_text:
        return [("Artificial Intelligence", "Your Business. Your Models.", "Gemini Enterprise Agent Platform")]
        
    if "ai apps" in full_text or "vertex" in full_text or "agent platform" in full_text or ("ai" in w_pil_clean and "agent" in full_text):
        return [("Artificial Intelligence", "Scale AI Apps and Agents", "Gemini Enterprise Agent Platform")]

    if "bigquery" in full_text or "warehouse" in full_text or "data analytics" in full_text or "analytics" in w_pil_clean:
        if "looker" in full_text:
            return [("Data & Analytics", "The AI Ready Data Cloud", "Looker")]
        elif "dataflow" in full_text:
            return [("Data & Analytics", "The AI Ready Data Cloud", "Dataflow")]
        elif "dataproc" in full_text or "spark" in full_text or "hadoop" in full_text:
            return [("Data & Analytics", "The AI Ready Data Cloud", "Dataproc")]
        else:
            return [("Data & Analytics", "The AI Ready Data Cloud", "BigQuery")]

    if "alloydb" in full_text:
        return [("Databases", "The AI Ready Data Cloud", "AlloyDB for PostgreSQL")]
    if "cloud sql" in full_text or "postgres" in full_text or "mysql" in full_text or "sql server" in full_text:
        return [("Databases", "The AI Ready Data Cloud", "Cloud SQL")]
    if "spanner" in full_text:
        return [("Databases", "The AI Ready Data Cloud", "Spanner")]

    if "gke" in full_text or "kubernetes" in full_text:
        return [("Application Modernization", "Migrate, Modernize and Build", "Google Kubernetes Engine")]
    if "cloud run" in full_text or "cloudrun" in full_text:
        return [("Application Modernization", "Migrate, Modernize and Build", "Cloud Run")]
    if "apigee" in full_text or "api" in full_text:
        return [("Application Modernization", "Migrate, Modernize and Build", "Apigee API Management")]

    if "vmware" in full_text or "gcve" in full_text:
        return [("Infrastructure Modernization", "Enterprise Platform of Choice: VMware", "Google Cloud VMware Engine")]
    if "mainframe" in full_text:
        return [("Infrastructure Modernization", "Mainframe Modernization", "Dual Run")]
    if "compute" in full_text or "gce" in full_text or "infra" in w_pil_clean or "infrastructure" in full_text:
        return [("Infrastructure Modernization", "Enterprise Infrastructure: Linux/Windows/Storage", "Compute Engine")]

    if "secops" in full_text or "chronicle" in full_text or "security" in full_text or "siem" in full_text or "soar" in full_text:
        return [("Security", "Modern SecOps", "Google Security Operations Enterprise (Chronicle SIEM)")]

    return [("Artificial Intelligence", "Scale AI Apps and Agents", "Gemini Enterprise Agent Platform")]

def run():
    pname = ZENTA_CFG["partner"]
    ssid = ZENTA_CFG["sheet_id"]
    pids = ", ".join([f"'{x}'" for x in ZENTA_CFG["partner_ids"]])
    drp_keys_str = ", ".join([f"'{x}'" for x in ZENTA_CFG["drp_keys"]])
    default_pid = ZENTA_CFG["default_pid"]
    
    print(f"=== Starting update for {pname} ===")
    print(f"Spreadsheet ID: {ssid}")
    
    # 1. Fetch DRP profiles
    print("Fetching DRP profiles...")
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
    partner_drp_map = {}
    for r in drp_bq_rows:
        pil = r["f"][0].get("v")
        sol = r["f"][1].get("v")
        prd = r["f"][2].get("v")
        t1 = int(r["f"][3].get("v") or 0)
        t2 = int(r["f"][4].get("v") or 0)
        tot = int(r["f"][5].get("v") or 0)
        partner_drp_map[(pil, sol, prd)] = {"t1": t1, "t2": t2, "tot": tot}
    print(f"DRP profiles loaded: {len(partner_drp_map)} items")

    # 2. Read manual entries
    print("Reading existing manual entries from Follow_up...")
    manual_entries = fetch_existing_manual_entries(ssid, "Follow_up")
    print(f"Preserved manual entries: {len(manual_entries)} entries")
    for k, v in manual_entries.items():
        print(f"  {k}: {v}")

    # 3. Query workloads with next_steps
    print("Querying workloads from BigQuery...")
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
      w.workload_details.key_workload_products,
      w.owner_details.owner_id,
      w.owner_details.owner_name,
      w.workload_details.next_steps
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
    print(f"Uncommitted workloads found: {len(wkl_bq_rows)}")

    partner_workload_rows = []
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
        owner_id = cells[21].get("v") if len(cells) > 21 else ""
        owner_name = cells[22].get("v") if len(cells) > 22 else ""
        next_steps = cells[23].get("v") if len(cells) > 23 else ""
        if next_steps:
            next_steps = str(next_steps).replace("\r\n", " ").replace("\n", " ").strip()
        else:
            next_steps = ""

        try:
            arr_float = float(arr_val)
            arr_formatted = f"${arr_float:,.2f}"
        except:
            arr_formatted = "$0.00"

        acc_url = f"https://vector.lightning.force.com/lightning/r/Account/{account_id}/view" if account_id else ""
        acc_linked = make_hyperlink(acc_url, account_name) if acc_url else account_name

        wkl_url = f"https://vector.lightning.force.com/lightning/r/Workload__c/{workload_id}/view" if workload_id else ""
        wkl_linked = make_hyperlink(wkl_url, workload_name) if wkl_url else workload_name

        opp_url = f"https://vector.lightning.force.com/lightning/r/Opportunity/{opportunity_id}/view" if opportunity_id else ""
        opp_linked = make_hyperlink(opp_url, opportunity_name) if opp_url else opportunity_name

        er_linked = parse_expert_requests(er_raw)
        tier = get_account_tier(segment)

        matched_drp = match_exact_drp(pillar, sales_play, workload_solution, key_prods)
        total_drp_for_wkl = 0
        if matched_drp:
            total_drp_for_wkl = max([partner_drp_map.get(m, {}).get("tot", 0) for m in matched_drp])

        if total_drp_for_wkl == 0:
            wkl_capacity_status = "🔴 Capacity Gap (0 DRP Profiles)"
        elif total_drp_for_wkl == 1:
            wkl_capacity_status = "🟡 Constrained (1 DRP Profile)"
        else:
            wkl_capacity_status = f"🟢 Ready ({total_drp_for_wkl} DRP Profiles)"

        lt_preserved = ""
        link_preserved = ""
        if workload_name in manual_entries:
            lt_preserved = manual_entries[workload_name].get("last_touch", "")
            link_preserved = manual_entries[workload_name].get("link", "")

        # 19 Columns
        row_followup = [
            acc_linked,             # 0: Customer Account Name
            tier,                   # 1: Account Tier
            wkl_linked,             # 2: Workload Name
            owner_name or "",       # 3: Workload Owner (plain text)
            progress,               # 4: Workload Progress
            wkl_capacity_status,    # 5: Capacity Status
            opp_linked,             # 6: Opportunity Name
            next_steps,             # 7: Next Steps  <-- BETWEEN G AND H
            er_linked,              # 8: Expert Requests
            sub_region,             # 9: Sub Region
            micro_region,           # 10: Micro Region
            pillar,                 # 11: Pillar
            sales_play,             # 12: Sales Play
            workload_solution,      # 13: Workload Solution
            begin_migration_date,   # 14: Begin Migration Date
            production_date,        # 15: Production Date
            arr_formatted,          # 16: ARR USD
            lt_preserved,           # 17: Last Touch
            link_preserved          # 18: Link
        ]
        partner_workload_rows.append(row_followup)

    # Top block (19 cols)
    partner_top_block = [
        ["Partner:", pname, "", "", "Last Update:", DATE_FORMATTED] + [""] * 13,
        [""] * 19,
        ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)"] + [""] * 11,
        [""] * 19,
        PARTNER_FOLLOWUP_HEADERS
    ]

    followup_rows = partner_top_block + partner_workload_rows
    followup_csv = "/tmp/zenta_followup_next_steps.csv"
    with open(followup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(followup_rows)

    print(f"CSV generated with {len(followup_rows)} rows and {len(PARTNER_FOLLOWUP_HEADERS)} columns.")

    # 4. Clear and import CSV to Follow_up tab
    print("Clearing and importing to Follow_up tab...")
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:Z2000"], capture_output=True, check=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Follow_up'!2:2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, followup_csv, "--sheet", "Follow_up"], capture_output=True, check=True)

    grid_info = get_grid_info(ssid)
    f_info = grid_info.get("Follow_up", {"sheetId": 0, "rowCount": len(followup_rows), "columnCount": 19})
    sid_followup = f_info["sheetId"]
    f_rows = f_info["rowCount"]

    # 5. Freeze row 5
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_followup), "--rows", "5"], capture_output=True)

    # 6. Delete old conditional formatting rules if any
    res_info = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res_info.returncode == 0 and res_info.stdout.strip():
        try:
            info_data = json.loads(res_info.stdout)
            cf_rules = info_data["sheets"][0].get("conditionalFormats", [])
            if cf_rules:
                del_reqs = [{"deleteConditionalFormatRule": {"sheetId": sid_followup, "index": i}} for i in reversed(range(len(cf_rules)))]
                del_batch = f"temp_del_rules_{ssid}.json"
                with open(del_batch, "w") as df:
                    json.dump({"requests": del_reqs}, df)
                subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", del_batch], capture_output=True)
                if os.path.exists(del_batch):
                    os.remove(del_batch)
        except Exception as e:
            print(f"Warning cleaning conditional formats: {e}")

    # 7. Batch formatting
    print("Applying styling, alignments, borders, widths, and conditional formatting...")
    batch_req = {
      "requests": [
        # Reset formatting
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 19},
            "cell": {
              "userEnteredFormat": {
                "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"},
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "OVERFLOW_CELL"
              }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
          }
        },
        # Unmerge top rows
        {
          "unmergeCells": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": min(10, f_rows), "startColumnIndex": 0, "endColumnIndex": 19}
          }
        },
        # Merges
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        
        # Row 1 Format
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },

        # Row 3 Format (Light Purple for Alert Criteria)
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "LEFT"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 5 Main Header (Cols 0-16 Google Blue, Cols 17-18 Forest Green)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 17}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 17, "endColumnIndex": 19}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

        # Data Rows Formatting
        # Left-aligned text:
        # Col 0 (Customer Account Name)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        # Cols 2, 3, 4 (Workload Name, Workload Owner, Workload Progress)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        # Cols 6 to 14 (Opportunity Name, Next Steps, Expert Requests, Sub Region, Micro Region, Pillar, Sales Play, Workload Solution)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 14}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},

        # Centered columns: Tier (Col 1), Capacity (Col 5), Dates (Cols 14-15)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 1, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 14, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},

        # ARR Currency (Col 16)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 16, "endColumnIndex": 17}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},

        # Manual Note Columns (Cols 17-18)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 17, "endColumnIndex": 19}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},

        # Hyperlinks styling
        # Col 0: Customer Account Name
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        # Col 2: Workload Name
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        # Col 6: Opportunity Name
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

        # Borders
        {
          "updateBorders": {
            "range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 19},
            "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
            "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
          }
        },
        # Basic Filter
        {"clearBasicFilter": {"sheetId": sid_followup}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 19}}}},

        # Conditional Formatting Rules (Progress is Col E [$E6], Production Date is Col P [$P6])
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 19}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $P6<>\"\", ($P6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}}}}, "index": 0}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 19}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $P6<>\"\", ($P6-TODAY())>=15, ($P6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}}}}, "index": 1}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 19}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $P6<>\"\", ($P6-TODAY())>=31, ($P6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}}}}, "index": 2}},

        # Row heights
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 5, "endIndex": f_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
      ]
    }

    # Zebra striping
    for r_idx in range(5, f_rows):
        if r_idx % 2 == 1:
            batch_req["requests"].append({
                "repeatCell": {
                    "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 17},
                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                    "fields": "userEnteredFormat(backgroundColor)"
                }
            })

    # Column widths
    for col_idx, width in PARTNER_COL_WIDTHS.items():
        batch_req["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    # Format ER column if has links (now Col 8)
    for r_idx in range(5, f_rows):
        if r_idx < len(followup_rows):
            val = followup_rows[r_idx][8]
            if "ER-" in val and ("HYPERLINK" in val or "http" in val):
                batch_req["requests"].append({
                    "repeatCell": {
                        "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 8, "endColumnIndex": 9},
                        "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}},
                        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
                    }
                })

    # Execute batch request
    tmp_batch = f"temp_batch_{ssid}.json"
    with open(tmp_batch, "w") as f:
        json.dump(batch_req, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_batch], capture_output=True, check=True)
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)

    print("✓ Follow_up tab successfully updated for Zenta with Next Steps column!")

if __name__ == "__main__":
    run()
