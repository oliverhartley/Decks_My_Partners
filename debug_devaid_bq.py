import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT 
  pillar,
  sol as solution,
  p.scored_product,
  p.profile_id,
  p.tier_category
FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
CROSS JOIN UNNEST(p.parent_pillar) pillar
CROSS JOIN UNNEST(p.sales_play) sol
WHERE p.consolidated_partner_id IN ("P20220923084", "0014M00001h38aiQAA")
ORDER BY pillar, solution, scored_product
"""
schema, rows = run_query(sql)
print(f"Total DRP rows for Devaid: {len(rows)}")
for r in rows:
    pil = r["f"][0].get("v")
    sol = r["f"][1].get("v")
    prd = r["f"][2].get("v")
    pid = r["f"][3].get("v")
    tier = r["f"][4].get("v")
    print(f"  {pil} | {sol} | {prd} | Profile: {pid} | Tier: {tier}")
