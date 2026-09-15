import sys
import os
import json
import re
import subprocess
from datetime import datetime

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

CACHE_FILE = "workload_drp_ai_cache.json"
DUCKIE_BIN = "/google/bin/releases/gemini-agents-duckie/duckie_cli"

# 1. Load DRP Catalog and map product to (pillar, solution)
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
_, rows_cat = run_query(sql_catalog)
drp_catalog = [(r["f"][0].get("v"), r["f"][1].get("v"), r["f"][2].get("v")) for r in rows_cat]
drp_products = sorted(list(set(c[2] for c in drp_catalog if c[2] != "All Products")))

# 2. Load existing cache
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r") as f:
            classification_cache = json.load(f)
    except:
        classification_cache = {}
else:
    classification_cache = {}

def classify_workload_ai(workload_data):
    w_id = workload_data["workload_id"]
    if w_id in classification_cache:
        return classification_cache[w_id]
        
    w_name = workload_data.get("workload_name", "")
    w_pillar = workload_data.get("primary_workload_pillar", "")
    w_play = workload_data.get("sales_play", "")
    w_sol = workload_data.get("workload_solutions", "")
    w_prods = workload_data.get("key_workload_products", [])
    w_opp = workload_data.get("opportunity_name", "")
    w_strat = workload_data.get("technical_win_strategy", "")
    w_next = workload_data.get("next_steps", "")
    
    prods_str = ", ".join(w_prods) if isinstance(w_prods, list) else str(w_prods or "")
    
    prompt = f"""Eres un arquitecto especialista en Google Cloud y en el Delivery Readiness Program (DRP).
Tu objetivo es clasificar el siguiente Workload comercial de un partner dentro de exactamente UNO de los 28 Productos calificados del catálogo DRP.
Evalúa minuciosamente toda la información contextual disponible en el workload.

Catálogo estricto de los 28 Productos DRP:
{chr(10).join(f"- {p}" for p in drp_products)}

Datos del Workload:
- Workload Name: {w_name}
- Primary Pillar: {w_pillar}
- Sales Play: {w_play}
- Workload Solution: {w_sol}
- Key Products: {prods_str}
- Opportunity: {w_opp}
- Technical Win Strategy: {w_strat}
- Next Steps: {w_next}

Instrucciones:
1. Elige como 'matched_product' exactamente uno de los 28 nombres de la lista de Productos DRP.
2. Asigna 'certainty_pct' (0 a 100) según qué tan explícita y unívoca es la información del workload.
3. Si el workload involucra múltiples productos, elige el principal como 'matched_product' y los demás en 'secondary_products'.
4. Justifica técnicamente tu decisión de manera concisa en 'reasoning' basándote únicamente en los datos proporcionados.

Responde ÚNICAMENTE un objeto JSON válido con la siguiente estructura (sin texto extra):
{{
  "matched_product": "<uno de los 28 productos>",
  "certainty_pct": <número entero entre 0 y 100>,
  "reasoning": "<justificación concisa>",
  "secondary_products": ["<opcional: otros productos calificados involucrados>"]
}}
"""
    res = subprocess.run([
        DUCKIE_BIN,
        f"--question={prompt}"
    ], capture_output=True, text=True)
    
    output = res.stdout.strip()
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if parsed.get("matched_product") in drp_products:
                classification_cache[w_id] = parsed
                with open(CACHE_FILE, "w") as f:
                    json.dump(classification_cache, f, indent=2)
                return parsed
        except Exception as e:
            print(f"JSON parse error for {w_name}: {e}")
            
    fallback = {
        "matched_product": "Google Compute Engine" if "infra" in (w_pillar or "").lower() else "Cloud Run",
        "certainty_pct": 30,
        "reasoning": "Fallback automático por fallo de inferencia.",
        "secondary_products": []
    }
    classification_cache[w_id] = fallback
    with open(CACHE_FILE, "w") as f:
        json.dump(classification_cache, f, indent=2)
    return fallback

def legacy_keyword_match(w_pillar, w_sales_play, w_solution, w_prods):
    p_text = f"{w_pillar} {w_sales_play} {w_solution} {' '.join(w_prods or [])}".lower()
    matches = []
    for c_pillar, c_sol, c_prod in drp_catalog:
        c_prod_lower = c_prod.lower()
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
        elif "gemini" in p_text and "gemini" in c_prod_lower:
            matches.append((c_pillar, c_sol, c_prod))
    if not matches:
        for c_pillar, c_sol, c_prod in drp_catalog:
            if c_pillar.lower() in p_text:
                matches.append((c_pillar, c_sol, c_prod))
    return list(set(matches))

def run_prototype():
    print("====================================================================")
    print("Ejecutando PoC: AI Workload-to-DRP Product Matching & Capacity")
    print("====================================================================")
    
    partners_to_test = [
        {"name": "Comercializadora Zenta Group SPA", "pids": ["0014M00001h39BLQAY"], "drp_keys": ["P20220602109", "0014M00001h39BLQAY"]},
        {"name": "Tech Pulse SPA (Axmos)", "pids": ["0014M00002JmizDQAR"], "drp_keys": ["P20260318001", "0014M00002JmizDQAR"]},
        {"name": "Devaid SPA", "pids": ["0014M00001h38aiQAA"], "drp_keys": ["P20220923084", "0014M00001h38aiQAA"]}
    ]
    
    for p_cfg in partners_to_test:
        pname = p_cfg["name"]
        pid_str = ", ".join(f"\"{x}\"" for x in p_cfg["pids"])
        drp_str = ", ".join(f"\"{x}\"" for x in p_cfg["drp_keys"])
        
        print(f"\n=======================================================")
        print(f"Analizando Partner: {pname}")
        print(f"=======================================================")
        
        # 1. Fetch DRP Profile counts
        sql_drp = f"""
        SELECT 
          COALESCE(p.scored_product, 'All Products') as product,
          COUNT(DISTINCT IF(p.tier_category IN ('Tier 1', 'Tier 2'), p.profile_id, NULL)) as total_profiles
        FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
        WHERE p.consolidated_partner_id IN ({drp_str})
        GROUP BY 1
        """
        _, drp_rows = run_query(sql_drp)
        drp_profiles = {r["f"][0].get("v"): int(r["f"][1].get("v") or 0) for r in drp_rows}
        
        # 2. Fetch sample workloads (top 4 for each)
        sql_wkl = f"""
        SELECT 
          w.workload_id,
          w.workload_name,
          w.opportunity_id,
          o.opportunity_name,
          w.workload_details.primary_workload_pillar,
          w.workload_details.sales_play,
          w.workload_details.workload_solutions,
          w.workload_details.key_workload_products,
          w.workload_details.technical_win_strategy,
          w.workload_details.next_steps
        FROM `concord-prod.service_cloudbi.workloads` w
        LEFT JOIN `concord-prod.service_cloudbi.opportunities` o ON w.opportunity_id = o.opportunity_id
        WHERE w.workload_details.partner_id IN ({pid_str})
          AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
          AND (w.workload_details.workload_progress IS NULL OR (
                 LOWER(w.workload_details.workload_progress) NOT LIKE "%closed%"
                 AND w.workload_details.workload_progress NOT LIKE "5.%"
              ))
        ORDER BY w.metrics.annual_gross_revenue DESC
        LIMIT 4
        """
        _, wkl_rows = run_query(sql_wkl)
        print(f"Procesando {len(wkl_rows)} workloads de alta prioridad...")
        
        for idx, r in enumerate(wkl_rows):
            cells = [c.get("v") for c in r["f"]]
            w_id = cells[0]
            w_name = cells[1] or ""
            o_name = cells[3] or ""
            pillar = cells[4] or ""
            play = cells[5] or ""
            sol = cells[6] or ""
            raw_prods = cells[7] or []
            prods = [x.get("v") for x in raw_prods] if isinstance(raw_prods, list) else [raw_prods]
            strat = cells[8] or ""
            next_s = cells[9] or ""
            
            w_obj = {
                "workload_id": w_id,
                "workload_name": w_name,
                "opportunity_name": o_name,
                "primary_workload_pillar": pillar,
                "sales_play": play,
                "workload_solutions": sol,
                "key_workload_products": prods,
                "technical_win_strategy": strat,
                "next_steps": next_s
            }
            
            # Legacy matching
            legacy_m = legacy_keyword_match(pillar, play, sol, prods)
            legacy_prod_names = list(set(x[2] for x in legacy_m))
            legacy_profiles = sum(drp_profiles.get(p, 0) for p in legacy_prod_names)
            
            # AI matching
            ai_res = classify_workload_ai(w_obj)
            ai_prod = ai_res.get("matched_product")
            ai_cert = ai_res.get("certainty_pct", 0)
            ai_profiles = drp_profiles.get(ai_prod, 0)
            
            print(f"\n--- [WL #{idx+1}] {w_name} ---")
            print(f"  • Opp: {o_name}")
            print(f"  • Pillar: {pillar} | Sol: {sol} | Prods: {prods}")
            print(f"  [LEGACY] Productos sumados ({len(legacy_prod_names)}): {legacy_prod_names[:3]}")
            print(f"           Capacidad inflada: {legacy_profiles} perfiles")
            print(f"  [AI MATCH] Producto Preciso: {ai_prod} (Certeza: {ai_cert}%)")
            print(f"             Capacidad Real DRP: {ai_profiles} perfiles en {ai_prod}")
            print(f"             Justificación: {ai_res.get('reasoning')}")
            if ai_res.get("secondary_products"):
                print(f"             Secundarios: {ai_res.get('secondary_products')}")

if __name__ == "__main__":
    run_prototype()
