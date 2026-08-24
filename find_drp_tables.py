import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT table_name
FROM `concord-prod.service_cloudbi.INFORMATION_SCHEMA.TABLES`
WHERE LOWER(table_name) LIKE "%partner%"
ORDER BY table_name
"""
schema, rows = run_query(sql)
print("Partner tables in service_cloudbi:")
for r in rows:
    print(f"  {r['f'][0].get('v')}")
