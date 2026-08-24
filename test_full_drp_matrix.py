import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
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
  WHERE p.consolidated_partner_id IN ("P20220602109", "0014M00001h39BLQAY")
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
print(f"Zenta Full DRP Matrix rows: {len(rows)}")
for r in rows:
    pil = r["f"][0].get("v")
    sol = r["f"][1].get("v")
    prd = r["f"][2].get("v")
    t1 = r["f"][3].get("v")
    t2 = r["f"][4].get("v")
    tot = r["f"][5].get("v")
    print(f"  {pil} | {sol} | {prd} -> T1: {t1}, T2: {t2}, Tot: {tot}")
