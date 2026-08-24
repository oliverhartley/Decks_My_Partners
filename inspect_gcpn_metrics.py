import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT DISTINCT metric_name, requirement_name, competency_type, competency_name
FROM `concord-prod.service_cloudbi.partner_gcpn_reporting_daily`
WHERE LOWER(metric_name) LIKE "%drp%" 
   OR LOWER(metric_name) LIKE "%delivery%"
   OR LOWER(metric_name) LIKE "%readiness%"
   OR LOWER(metric_name) LIKE "%profile%"
LIMIT 30
"""
schema, rows = run_query(sql)
print("DRP metrics in partner_gcpn_reporting_daily:")
for r in rows:
    print([c.get("v") for c in r["f"]])
