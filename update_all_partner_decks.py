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
        "partner_ids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
        "cert_pids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
        "drp_keys": ["P20220602109", "0014M00001h39BLQAY", "0014M00001m9woLQAQ"],
        "default_pid": "0014M00001h39BLQAY",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "partner_ids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
        "cert_pids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
        "drp_keys": ["P20260318001", "0014M00002JmizDQAR"],
        "default_pid": "0014M00002JmizDQAR",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "partner_ids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
        "cert_pids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
        "drp_keys": ["P20220923084", "0014M00001h38aiQAA"],
        "default_pid": "0014M00001h38aiQAA",
        "country": "Chile",
        "tier_level": "Premier"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "partner_ids": ["0014M00002M7lcJQAR"],
        "cert_pids": ["0014M00002M7lcJQAR"],
        "drp_keys": ["0014M00002M7lcJQAR"],
        "default_pid": "0014M00002M7lcJQAR",
        "country": "Colombia",
        "tier_level": "Premier"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "partner_ids": ["001Kf0000150rJ2IAI", "0014M00001kxZPMQA2", "0014M00001m9v8HQAQ"],
        "cert_pids": ["0014M00001kxZPMQA2", "001Kf0000150rJ2IAI", "0014M00001m9v8HQAQ"],
        "drp_keys": ["P20220923297", "0014M00001kxZPMQA2", "001Kf0000150rJ2IAI"],
        "default_pid": "0014M00001kxZPMQA2",
        "country": "Colombia / Regional",
        "tier_level": "Premier"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "partner_ids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
        "cert_pids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
        "drp_keys": ["P20220602104", "0014M00001uFlbSQAS"],
        "default_pid": "0014M00001uFlbSQAS",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "partner_ids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
        "cert_pids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
        "drp_keys": ["P20231208017", "0014M00002GGNRCQA5"],
        "default_pid": "0014M00002GGNRCQA5",
        "country": "Brazil",
        "tier_level": "Premier"
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "partner_ids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "001Kf000010cw8CIAQ", "0014M00002N5mLOQAZ"],
        "cert_pids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "0014M00002N5mLOQAZ"],
        "drp_keys": ["P20220923048", "0014M00001h35nAQAQ"],
        "default_pid": "0014M00001h35nAQAQ",
        "country": "Regional / Spain & LATAM",
        "tier_level": "Premier"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "partner_ids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "cert_pids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "drp_keys": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"],
        "default_pid": "001Kf000013fuVXIAY",
        "country": "El Salvador / Central America",
        "tier_level": "Premier"
    }
]

LEGEND_BLOCK = [
    ["Production Date Alert Legend (Workloads in Stage 0-2 or 3)", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["Days Remaining (Production Date)", "Risk Level", "Alert Criteria / Stage", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["0 to 14 days (or overdue)", "🔴 Critical", "Production Date <= 14 days in Stage 0-2 or 3", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["15 to 30 days", "🌸 High", "Production Date 15-30 days in Stage 0-2 or 3", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["31 to 45 days", "🟡 Medium", "Production Date 31-45 days in Stage 0-2 or 3", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["> 45 days (or Stage >= 4)", "⚪ Normal", "Standard Timeline / Delivery", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
]

FOLLOWUP_HEADERS = [
    "Partner Name",
    "Customer Account Name",
    "Account Tier",
    "Workload Name",
    "Capacity Status (DRP Readiness)",
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

GLOBAL_DRP_HEADERS = [
    "Partner Name",
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
]

ACCRED_HEADERS = [
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Legal Entity"
]

GLOBAL_ACCRED_HEADERS = [
    "Partner Name",
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Legal Entity"
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
                            if lt_val or link_val:
                                manual_entries[w_name] = {"last_touch": lt_val, "link": link_val}
        except Exception as e:
            print(f"Error fetching manual entries for {ssid}: {e}")
    return manual_entries

def ensure_sheet_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    res2 = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            sheets = json.loads(res2.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    return None

def apply_alerts_to_sheet(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return
    data = json.loads(res.stdout)
    target_sheet = None
    for s in data.get("sheets", []):
        if s.get("properties", {}).get("title") == tab_title:
            target_sheet = s
            break
    if not target_sheet:
        return
    sid = target_sheet["properties"].get("sheetId", 0)
    num_rows = target_sheet["properties"]["gridProperties"].get("rowCount", 2000)
    existing_rules_count = len(target_sheet.get("conditionalFormats", []))
    requests = []
    for _ in range(existing_rules_count):
        requests.append({"deleteConditionalFormatRule": {"sheetId": sid, "index": 0}})
        
    # Entire row conditional formatting starts on row 9 (index 8 in 0-based), columns 0 to 18 (A to R)
    # 1. RED (0 to 14 days / <= 14 days)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": 8, "endRowIndex": num_rows, "startColumnIndex": 0, "endColumnIndex": 18}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": "=AND(OR(LEFT($M9,3)=\"0-2\",LEFT($M9,2)=\"3:\"), $O9<>\"\", ($O9-TODAY())<=14)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510} # #F28B82 (soft red so text remains readable across row)
                    }
                }
            },
            "index": 0
        }
    })
    # 2. LIGHT RED (15 to 30 days)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": 8, "endRowIndex": num_rows, "startColumnIndex": 0, "endColumnIndex": 18}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": "=AND(OR(LEFT($M9,3)=\"0-2\",LEFT($M9,2)=\"3:\"), $O9<>\"\", ($O9-TODAY())>=15, ($O9-TODAY())<=30)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902} # #FCE8E6
                    }
                }
            },
            "index": 1
        }
    })
    # 3. LIGHT YELLOW (31 to 45 days)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": 8, "endRowIndex": num_rows, "startColumnIndex": 0, "endColumnIndex": 18}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": "=AND(OR(LEFT($M9,3)=\"0-2\",LEFT($M9,2)=\"3:\"), $O9<>\"\", ($O9-TODAY())>=31, ($O9-TODAY())<=45)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.949, "blue": 0.800} # #FFF2CC
                    }
                }
            },
            "index": 2
        }
    })
    tmp_file = f"temp_alert_req_{sid}.json"
    with open(tmp_file, "w") as f:
        json.dump({"requests": requests}, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_file], capture_output=True)
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

# 1. Fetch DRP Catalog
print("\n>>> Fetching full DRP Catalog from BigQuery...")
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
print(f"Loaded {len(drp_catalog)} catalog products/solutions.")

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
    if "oracle" in full_text:
        return [("Infrastructure Modernization", "Enterprise Platform of Choice: Oracle", "Oracle")]
    if "sap" in full_text:
        return [("Infrastructure Modernization", "Enterprise Platform of Choice: SAP", "SAP on Google Cloud")]
    if "networking" in full_text or "wan" in full_text:
        return [("Infrastructure Modernization", "Migrate, Modernize and Build", "Google Cloud Networking")]
    if "compute" in full_text or "vms" in full_text or "infra" in full_text or "infrastructure" in w_pil_clean:
        return [("Infrastructure Modernization", "Migrate, Modernize and Build", "Google Compute Engine")]

    if "security" in full_text or "secops" in full_text or "scc" in full_text:
        if "operations" in full_text or "secops" in full_text:
            return [("Security", "Agentic Defense with Google Security", "Security Operations")]
        elif "threat" in full_text:
            return [("Security", "Agentic Defense with Google Security", "Google Threat Intelligence")]
        elif "command center" in full_text or "scc" in full_text:
            return [("Security", "Agentic Defense with Google Security", "Security Command Center")]
        else:
            return [("Security", "Secure Innovation with Google Cloud", "Cloud Security")]

    for c_pillar, c_sol, c_prod in drp_catalog:
        if c_pillar.lower() == w_pil_clean:
            return [(c_pillar, c_sol, c_prod)]
            
    return []

# Storage directories
os.makedirs("followup_data_latest", exist_ok=True)
os.makedirs("drp_data_latest", exist_ok=True)
os.makedirs("accred_data_latest", exist_ok=True)
os.makedirs("global_dashboard_data", exist_ok=True)

all_global_workload_rows = []
all_global_drp_rows = [GLOBAL_DRP_HEADERS]
all_global_accred_rows = [GLOBAL_ACCRED_HEADERS]

summary_stats = []

for cfg in PARTNERS:
    pname = cfg["partner"]
    ssid = cfg["sheet_id"]
    pids = ", ".join([f"\"{x}\"" for x in cfg["partner_ids"]])
    drp_keys_str = ", ".join([f"\"{x}\"" for x in cfg["drp_keys"]])
    cert_pids_str = ", ".join([f"\"{x}\"" for x in cfg["cert_pids"]])
    default_pid = cfg["default_pid"]
    safe_name = "".join(c if c.isalnum() else "_" for c in pname)
    
    print(f"\n========================================================")
    print(f"UPDATING TRACKER FOR: {pname}")
    print(f"Spreadsheet ID: {ssid}")
    print(f"========================================================")
    
    # ---------------------------------------------------------------------
    # A. DRP PROFILES QUERY
    # ---------------------------------------------------------------------
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
    partner_total_drp_capacity = 0
    for r in drp_bq_rows:
        pil = r["f"][0].get("v")
        sol = r["f"][1].get("v")
        prd = r["f"][2].get("v")
        t1 = int(r["f"][3].get("v") or 0)
        t2 = int(r["f"][4].get("v") or 0)
        tot = int(r["f"][5].get("v") or 0)
        partner_drp_map[(pil, sol, prd)] = {"t1": t1, "t2": t2, "tot": tot}
        partner_total_drp_capacity += tot
        
    # ---------------------------------------------------------------------
    # B. WORKLOADS QUERY
    # ---------------------------------------------------------------------
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
    print(f"-> Uncommitted Workloads found: {len(wkl_bq_rows)}")
    
    drp_workload_demand = {(pil, sol, prd): 0 for (pil, sol, prd) in drp_catalog}
    partner_total_arr = 0.0
    
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
        
        try:
            arr_float = float(arr_val)
            partner_total_arr += arr_float
            arr_formatted = f"{arr_float:,.2f}"
        except:
            arr_formatted = "0.00"
            
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
        
        matched_drp = match_exact_drp(pillar, sales_play, workload_solution, key_prods)
        for m_item in matched_drp:
            drp_workload_demand[m_item] = drp_workload_demand.get(m_item, 0) + 1
            
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
            
        row_followup = [
            p_linked,
            acc_linked,
            tier,
            wkl_linked,
            wkl_capacity_status,
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
            lt_preserved,
            link_preserved
        ]
        partner_workload_rows.append(row_followup)
        all_global_workload_rows.append(row_followup)
        
    # Build complete Follow_up CSV (Legend + Headers + Data)
    followup_rows = LEGEND_BLOCK + [FOLLOWUP_HEADERS] + partner_workload_rows
    followup_csv = os.path.join("followup_data_latest", f"{safe_name}_followup.csv")
    with open(followup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(followup_rows)
        
    # Overwrite Tab 1: Follow_up
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Follow_up'!2:2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, followup_csv, "--sheet", "Follow_up"], capture_output=True)
    
    # Freeze row 8
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", "0", "--rows", "8"], capture_output=True)
    
    # Format Legend
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "3",
        "--bold"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "1", "--end-row", "2",
        "--start-col", "0", "--end-col", "3",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "2", "--end-row", "3",
        "--start-col", "0", "--end-col", "3",
        "--bold",
        "--bg-color", "#EA4335"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "3", "--end-row", "4",
        "--start-col", "0", "--end-col", "3",
        "--bg-color", "#FCE8E6"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "4", "--end-row", "5",
        "--start-col", "0", "--end-col", "3",
        "--bg-color", "#FFF2CC"
    ], capture_output=True)
    
    # Format Main Header (row 7 in 0-based)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "7", "--end-row", "8",
        "--start-col", "0", "--end-col", "18",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "7", "--end-row", "8",
        "--start-col", "16", "--end-col", "18",
        "--bold",
        "--bg-color", "#E6F4EA",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    
    # Center Account Tier (Col 2) & Capacity (Col 4) on data rows
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "8", "--end-row", "2000",
        "--start-col", "2", "--end-col", "3",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", "0",
        "--start-row", "8", "--end-row", "2000",
        "--start-col", "4", "--end-col", "5",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", "0", "--start-col", "0", "--end-col", "18"], capture_output=True)
    apply_alerts_to_sheet(ssid, "Follow_up")
    
    # ---------------------------------------------------------------------
    # C. DRP STATUS TAB (33 items, blank zeros, capacity dots)
    # ---------------------------------------------------------------------
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
        
    drp_csv = os.path.join("drp_data_latest", f"{safe_name}_drp.csv")
    with open(drp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(drp_rows)
        
    tab_drp = "DRP_Status"
    sid_drp = ensure_sheet_tab(ssid, tab_drp)
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
        
    # ---------------------------------------------------------------------
    # D. ACCREDITATIONS TAB
    # ---------------------------------------------------------------------
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
    WHERE p.partner_details.sfdc_partner_id IN ({cert_pids_str})
      AND p.reporting_month = (SELECT MAX(reporting_month) FROM `concord-prod.service_cloudbi.partner_certifications`)
    ORDER BY p.certification_details.certification_type, p.certification_details.certification_name, p.partner_contact_profile_details.profile_name
    """
    _, rows_certs = run_query(sql_certs)
    partner_total_certs = len(rows_certs)
    print(f"-> Active Accreditations/Certs found: {partner_total_certs}")
    
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
            all_global_accred_rows.append([pname, cname, ctype, csubtype, pname_cand, pemail_cand, issued, exp, entity])
    else:
        accred_rows.append(["No active accreditations found", "-", "-", "-", "-", "-", "-", "-"])
        all_global_accred_rows.append([pname, "No active accreditations found", "-", "-", "-", "-", "-", "-", "-"])
        
    accred_csv = os.path.join("accred_data_latest", f"{safe_name}_accred.csv")
    with open(accred_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(accred_rows)
        
    tab_accred = "Acreditaciones"
    sid_accred = ensure_sheet_tab(ssid, tab_accred)
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{tab_accred}'!A1:Z3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{tab_accred}'!2:3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, accred_csv, "--sheet", tab_accred], capture_output=True)
    if sid_accred is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_accred), "--rows", "1"], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sid_accred),
            "--start-row", "0", "--end-row", "1",
            "--start-col", "0", "--end-col", "8",
            "--bold",
            "--bg-color", "#E8F0FE",
            "--align", "CENTER",
            "--wrap"
        ], capture_output=True)
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sid_accred),
            "--start-row", "1", "--end-row", "3000",
            "--start-col", "5", "--end-col", "7",
            "--align", "CENTER"
        ], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_accred), "--start-col", "0", "--end-col", "8"], capture_output=True)
        
    summary_stats.append({
        "partner": pname,
        "country": cfg["country"],
        "track": cfg["tier_level"],
        "default_pid": default_pid,
        "sheet_id": ssid,
        "workloads_count": len(wkl_bq_rows),
        "total_arr": partner_total_arr,
        "drp_capacities": partner_total_drp_capacity,
        "certs_count": partner_total_certs
    })
    print(f"✓ Completed full update for {pname}")

# =========================================================================
# E. UPDATE GLOBAL PARTNER MANAGEMENT DASHBOARD
# =========================================================================
print("\n========================================================")
print("UPDATING GLOBAL PARTNER MANAGEMENT DASHBOARD")
print(f"Spreadsheet ID: {GLOBAL_SSID}")
print("========================================================")

# 1. Executive_Summary
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
tot_all_wkls = sum(s["workloads_count"] for s in summary_stats)
tot_all_arr = sum(s["total_arr"] for s in summary_stats)
tot_all_drp = sum(s["drp_capacities"] for s in summary_stats)
tot_all_certs = sum(s["certs_count"] for s in summary_stats)

for s in summary_stats:
    p_url = f"https://vector.lightning.force.com/lightning/r/Account/{s['default_pid']}/view"
    p_link = make_hyperlink(p_url, s["partner"])
    tracker_url = f"https://docs.google.com/spreadsheets/d/{s['sheet_id']}/edit#gid=0"
    tracker_link = make_hyperlink(tracker_url, "Open Partner Tracker ↗")
    summary_rows.append([
        p_link,
        s["country"],
        s["track"],
        str(s["workloads_count"]),
        f"{s['total_arr']:,.2f}",
        str(s["drp_capacities"]),
        str(s["certs_count"]),
        tracker_link
    ])

summary_rows.append([
    "TOTAL (All 9 Partners)",
    "-",
    "-",
    str(tot_all_wkls),
    f"{tot_all_arr:,.2f}",
    str(tot_all_drp),
    str(tot_all_certs),
    "-"
])

exec_csv = "global_dashboard_data/executive_summary_latest.csv"
with open(exec_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(summary_rows)

sid_exec = ensure_sheet_tab(GLOBAL_SSID, "Executive_Summary")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'Executive_Summary'!A1:Z500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'Executive_Summary'!2:500"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, exec_csv, "--sheet", "Executive_Summary"], capture_output=True)
if sid_exec is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_exec), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_exec),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#1A73E8",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_exec),
        "--start-row", str(len(summary_rows)-1), "--end-row", str(len(summary_rows)),
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#E8F0FE"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_exec),
        "--start-row", "1", "--end-row", str(len(summary_rows)),
        "--start-col", "3", "--end-col", "7",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid_exec), "--start-col", "0", "--end-col", "8"], capture_output=True)
print("✓ Updated Global Executive_Summary")

# 2. All_Workloads_Follow_up
all_global_followup_rows = LEGEND_BLOCK + [FOLLOWUP_HEADERS] + all_global_workload_rows
global_followup_csv = "global_dashboard_data/all_workloads_followup_latest.csv"
with open(global_followup_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_followup_rows)

sid_gwkl = ensure_sheet_tab(GLOBAL_SSID, "All_Workloads_Follow_up")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Workloads_Follow_up'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Workloads_Follow_up'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_followup_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True)
if sid_gwkl is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_gwkl), "--rows", "8"], capture_output=True)
    
    # Format Legend
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "3",
        "--bold"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "1", "--end-row", "2",
        "--start-col", "0", "--end-col", "3",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "2", "--end-row", "3",
        "--start-col", "0", "--end-col", "3",
        "--bold",
        "--bg-color", "#EA4335"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "3", "--end-row", "4",
        "--start-col", "0", "--end-col", "3",
        "--bg-color", "#FCE8E6"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "4", "--end-row", "5",
        "--start-col", "0", "--end-col", "3",
        "--bg-color", "#FFF2CC"
    ], capture_output=True)
    
    # Format Main Header (row 7 in 0-based)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "7", "--end-row", "8",
        "--start-col", "0", "--end-col", "18",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "7", "--end-row", "8",
        "--start-col", "16", "--end-col", "18",
        "--bold",
        "--bg-color", "#E6F4EA",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    
    # Center Account Tier (Col 2) & Capacity (Col 4) on data rows
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "8", "--end-row", "5000",
        "--start-col", "2", "--end-col", "3",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gwkl),
        "--start-row", "8", "--end-row", "5000",
        "--start-col", "4", "--end-col", "5",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid_gwkl), "--start-col", "0", "--end-col", "18"], capture_output=True)
    apply_alerts_to_sheet(GLOBAL_SSID, "All_Workloads_Follow_up")
print("✓ Updated Global All_Workloads_Follow_up")

# 3. All_DRP_Status
global_drp_csv = "global_dashboard_data/all_drp_status_latest.csv"
with open(global_drp_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_drp_rows)

sid_gdrp = ensure_sheet_tab(GLOBAL_SSID, "All_DRP_Status")
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
print("✓ Updated Global All_DRP_Status")

# 4. All_Acreditaciones
global_accred_csv = "global_dashboard_data/all_accreditations_latest.csv"
with open(global_accred_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_accred_rows)

sid_gaccred = ensure_sheet_tab(GLOBAL_SSID, "All_Acreditaciones")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Acreditaciones'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Acreditaciones'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_accred_csv, "--sheet", "All_Acreditaciones"], capture_output=True)
if sid_gaccred is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(sid_gaccred), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gaccred),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "9",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", GLOBAL_SSID,
        "--sheet-id", str(sid_gaccred),
        "--start-row", "1", "--end-row", "5000",
        "--start-col", "6", "--end-col", "8",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", GLOBAL_SSID, "--sheet-id", str(sid_gaccred), "--start-col", "0", "--end-col", "9"], capture_output=True)
print("✓ Updated Global All_Acreditaciones")

print("\n========================================================")
print("ALL 10 SPREADSHEETS FULLY UPDATED WITH TOP LEGEND & FULL-ROW ALERTS!")
print("========================================================")
