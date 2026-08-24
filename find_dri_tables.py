import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT table_schema, table_name
FROM `concord-prod.region-us.INFORMATION_SCHEMA.TABLES`
WHERE (LOWER(table_name) LIKE "%dri_tier%"
   OR LOWER(table_name) LIKE "%delivery_readiness%"
   OR LOWER(table_name) LIKE "%delivery_capacity%")
  AND table_schema NOT LIKE "raw_%"
"""
schema, rows = run_query(sql)
print(f"Found {len(rows)} tables:")
for r in rows:
    ts = r["f"][0].get("v")
    tn = r["f"][1].get("v")
    print(f"  {ts}.{tn}")
