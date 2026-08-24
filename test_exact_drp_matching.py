import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

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

def match_exact_drp(w_pillar, w_sales_play, w_solution, w_prods):
    """
    Strict, precise hierarchical matching between workload and DRP catalog.
    """
    w_pil_clean = (w_pillar or "").strip().lower()
    w_play_clean = (w_sales_play or "").strip().lower()
    w_sol_clean = (w_solution or "").strip().lower()
    w_prods_clean = [str(x).strip().lower() for x in (w_prods or [])]
    full_text = f"{w_pil_clean} {w_play_clean} {w_sol_clean} {' '.join(w_prods_clean)}"
    
    # 1. Direct Product Specific Matches
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

    # Default fallback to primary pillar
    for c_pillar, c_sol, c_prod in drp_catalog:
        if c_pillar.lower() == w_pil_clean:
            return [(c_pillar, c_sol, c_prod)]
            
    return []

# Test for Devaid Workloads
sql_devaid_wkl = """
SELECT 
  w.workload_name,
  w.workload_details.primary_workload_pillar,
  w.workload_details.sales_play,
  w.workload_details.workload_solutions,
  w.workload_details.key_workload_products
FROM `concord-prod.service_cloudbi.workloads` w
WHERE w.workload_details.partner_id IN ("0014M00001h38aiQAA", "0014M00001m9sVvQAI")
  AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
LIMIT 10
"""
_, dev_wkls = run_query(sql_devaid_wkl)
for r in dev_wkls:
    wn = r["f"][0].get("v")
    wp = r["f"][1].get("v") or ""
    ws = r["f"][2].get("v") or ""
    wsol = r["f"][3].get("v") or ""
    wprods = [x.get("v") for x in r["f"][4].get("v")] if isinstance(r["f"][4].get("v"), list) else []
    matches = match_exact_drp(wp, ws, wsol, wprods)
    print(f"\nWorkload: {wn}")
    print(f"  Inputs: Pillar='{wp}', SalesPlay='{ws}', Sol='{wsol}'")
    print(f"  Strict Matched DRP: {matches}")
