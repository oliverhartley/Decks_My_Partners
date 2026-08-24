import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = "SELECT * FROM `concord-prod.service_cloudbi.partner_gcpn_reporting_daily` LIMIT 1"
schema, rows = run_query(sql)
print("partner_gcpn_reporting_daily columns:")
for f in schema["fields"]:
    print(f"  {f['name']}: {f.get('type')}")
