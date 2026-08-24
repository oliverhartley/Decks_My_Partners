import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT 
  p.consolidated_partner_id,
  p.standardized_partner_name,
  COALESCE(pillar, 'All Pillars') as pillar,
  COALESCE(sol, 'All Solutions') as solution,
  COALESCE(p.scored_product, 'All Products') as product,
  COUNT(DISTINCT IF(p.tier_category = 'Tier 1', p.profile_id, NULL)) as tier1_count,
  COUNT(DISTINCT IF(p.tier_category = 'Tier 2', p.profile_id, NULL)) as tier2_count,
  COUNT(DISTINCT IF(p.tier_category IN ('Tier 1', 'Tier 2'), p.profile_id, NULL)) as total_tier1_tier2
FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
LEFT JOIN UNNEST(p.parent_pillar) pillar
LEFT JOIN UNNEST(p.sales_play) sol
WHERE p.consolidated_partner_id IN (
  "0014M00001h39BLQAY", "0014M00002JmizDQAR", "0014M00001h38aiQAA",
  "0014M00002M7lcJQAR", "0014M00001kxZPMQA2", "0014M00001uFlbSQAS",
  "0014M00002GGNRCQA5", "0014M00001h35nAQAQ", "0014M00002M7ryLQAR",
  "001Kf000010ctuwIAA", "0014M00002N5mLOQAZ", "001Kf000013fuVXIAY",
  "0014M00001m9woLQAQ", "0014M00001m9sVvQAI", "001Kf00001G4DmBIAV",
  "0014M00002C1I0PQAV", "001Kf000013hWaOIAU", "0014M00001w6MZzQAM"
)
GROUP BY 1, 2, 3, 4, 5
HAVING total_tier1_tier2 > 0
ORDER BY standardized_partner_name, pillar, solution, product
"""
schema, rows = run_query(sql)
print(f"Aggregated DRP rows found: {len(rows)}")
for r in rows[:30]:
    pname = r["f"][1].get("v")
    pillar = r["f"][2].get("v")
    sol = r["f"][3].get("v")
    prod = r["f"][4].get("v")
    t1 = r["f"][5].get("v")
    t2 = r["f"][6].get("v")
    tot = r["f"][7].get("v")
    print(f"[{pname}] {pillar} | Solution: {sol} | Product: {prod} | Tier 1: {t1} | Tier 2: {t2} | Total: {tot}")
