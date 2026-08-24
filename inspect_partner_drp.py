import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT 
  partner_id,
  standardized_partner_name,
  parent_pillar,
  solution_name,
  tier_category,
  COUNT(DISTINCT profile_id) as profile_count
FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri`
WHERE partner_id IN (
  "0014M00001h39BLQAY", "0014M00002JmizDQAR", "0014M00001h38aiQAA",
  "0014M00002M7lcJQAR", "0014M00001kxZPMQA2", "0014M00001uFlbSQAS",
  "0014M00002GGNRCQA5", "0014M00001h35nAQAQ", "0014M00002M7ryLQAR",
  "001Kf000010ctuwIAA", "0014M00002N5mLOQAZ", "001Kf000013fuVXIAY",
  "0014M00001m9woLQAQ", "0014M00001m9sVvQAI", "001Kf00001G4DmBIAV",
  "0014M00002C1I0PQAV", "001Kf000013hWaOIAU", "0014M00001w6MZzQAM"
)
GROUP BY 1, 2, 3, 4, 5
ORDER BY standardized_partner_name, parent_pillar, solution_name, tier_category
"""
schema, rows = run_query(sql)
print(f"DRP records found: {len(rows)}")
for r in rows[:30]:
    print([c.get("v") for c in r["f"]])
