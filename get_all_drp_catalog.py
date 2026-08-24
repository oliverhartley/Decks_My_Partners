import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
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
schema, rows = run_query(sql)
print(f"Total distinct DRP catalog items: {len(rows)}")
for r in rows:
    print(f"  {r['f'][0].get('v')} | {r['f'][1].get('v')} | {r['f'][2].get('v')}")
