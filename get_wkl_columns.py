import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT column_name, data_type
FROM `concord-prod.service_cloudbi.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = "partner_workloads"
ORDER BY ordinal_position
"""
schema, rows = run_query(sql)
print(f"partner_workloads columns: {len(rows)}")
for r in rows:
    col = r['f'][0].get('v')
    dtype = r['f'][1].get('v')
    print(f"  {col}: {dtype}")
