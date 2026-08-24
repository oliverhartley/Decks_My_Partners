import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT DISTINCT metric_name, requirement_name, metric_short_name
FROM `concord-prod.service_cloudbi.partner_gcpn_reporting_daily`
ORDER BY metric_name
"""
schema, rows = run_query(sql)
print(f"Total metrics ({len(rows)}):")
for r in rows:
    print(f"  {r['f'][0].get('v')} | req: {r['f'][1].get('v')} | short: {r['f'][2].get('v')}")
