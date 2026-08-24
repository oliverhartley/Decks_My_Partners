import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

for tbl in [
    "concord-prod.service_cloudbi.partner_gcpn_reporting_daily",
    "concord-prod.service_cloudbi.partner_gcpn_reporting"
]:
    sql = f"SELECT * FROM `{tbl}` LIMIT 1"
    try:
        schema, rows = run_query(sql)
        cnt = len(schema["fields"])
        print(f"SUCCESS: {tbl} ({cnt} fields)")
    except Exception as e:
        print(f"FAILED: {tbl} -> {e}")
