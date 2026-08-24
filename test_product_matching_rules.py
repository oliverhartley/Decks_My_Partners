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
catalog = [(r["f"][0].get("v"), r["f"][1].get("v"), r["f"][2].get("v")) for r in rows_cat]
print(f"Catalog size: {len(catalog)}")

def match_drp_product(w_pillar, w_sales_play, w_solution, w_prods):
    """
    Given workload attributes, returns the best matching DRP product(s) or solution.
    """
    matches = []
    p_text = f"{w_pillar} {w_sales_play} {w_solution} {' '.join(w_prods or [])}".lower()
    
    for c_pillar, c_sol, c_prod in catalog:
        c_prod_lower = c_prod.lower()
        c_sol_lower = c_sol.lower()
        c_pil_lower = c_pillar.lower()
        
        # Exact product name match
        if c_prod_lower in p_text:
            matches.append((c_pillar, c_sol, c_prod))
        # Specific solution patterns
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
        elif "gemini enterprise" in p_text and "gemini enterprise" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "apigee" in p_text and "apigee" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
        elif "security" in p_text and c_pil_lower == "security":
            matches.append((c_pillar, c_sol, c_prod))
            
    if not matches:
        # Fallback to pillar level matches
        for c_pillar, c_sol, c_prod in catalog:
            if c_pillar.lower() in p_text or ("ai" in p_text and c_pillar == "Artificial Intelligence"):
                matches.append((c_pillar, c_sol, c_prod))
                
    return list(set(matches))

# Test on 10 workloads from Zenta & Tech Pulse
sql_wkl = """
SELECT 
  w.workload_name,
  w.workload_details.primary_workload_pillar,
  w.workload_details.sales_play,
  w.workload_details.workload_solutions,
  w.workload_details.key_workload_products
FROM `concord-prod.service_cloudbi.workloads` w
WHERE w.workload_details.partner_id IN ("0014M00001h39BLQAY", "0014M00002JmizDQAR")
  AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
LIMIT 10
"""
schema_w, rows_w = run_query(sql_wkl)
for r in rows_w:
    wn = r["f"][0].get("v")
    wp = r["f"][1].get("v") or ""
    ws = r["f"][2].get("v") or ""
    wsol = r["f"][3].get("v") or ""
    wprods = [x.get("v") for x in r["f"][4].get("v")] if isinstance(r["f"][4].get("v"), list) else []
    m = match_drp_product(wp, ws, wsol, wprods)
    print(f"\nWorkload: {wn}")
    print(f"  Inputs: Pillar='{wp}', SalesPlay='{ws}', Solution='{wsol}', Prods={wprods}")
    print(f"  Matched DRP Items ({len(m)}): {[x[2] for x in m[:4]]}")
