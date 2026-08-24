import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

PARTNER_DRP_KEYS = {
    "Comercializadora Zenta Group SPA": ["P20220602109", "0014M00001h39BLQAY"],
    "Tech Pulse SPA (Axmos)": ["P20260318001", "0014M00002JmizDQAR"],
    "Devaid SPA": ["P20220923084", "0014M00001h38aiQAA"],
    "UCLOUD STORE COLOMBIA S A S": ["0014M00002M7lcJQAR"],
    "TIVIT COLOMBIA S A S": ["P20220923297", "0014M00001kxZPMQA2", "001Kf0000150rJ2IAI"],
    "VPN Soluçoes em TI LTDA (Venha para Nuvem)": ["P20220602104", "0014M00001uFlbSQAS"],
    "MadeinWeb S/A": ["P20231208017", "0014M00002GGNRCQA5"],
    "CU2 CLOUD TEC STORE SL": ["P20220923048", "0014M00001h35nAQAQ"],
    "Consiti (Consultoría y Soluciones Informáticas)": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"]
}

for pname, keys in PARTNER_DRP_KEYS.items():
    keys_str = ", ".join([f"\"{k}\"" for k in keys])
    sql = f"""
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
    schema, rows = run_query(sql)
    print(f"\n{pname}: {len(rows)} DRP Solution/Product rows")
    for r in rows[:5]:
        print("  ", [c.get("v") for c in r["f"]])
