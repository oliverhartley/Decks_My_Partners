import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

for tbl in [
    "concord-prod.service_cloudbi.partner_specialization",
    "concord-prod.service_cloudbi.partner_expertise",
    "concord-prod.service_cloudbi.partner_persons",
    "concord-prod.service_cloudbi.partner_scorecard"
]:
    sql = f"SELECT * FROM `{tbl}` LIMIT 1"
    try:
        schema, rows = run_query(sql)
        print(f"\nSchema for {tbl} ({len(schema['fields'])} fields):")
        for f in schema["fields"]:
            print(f"  {f['name']}: {f.get('type')}")
    except Exception as e:
        print(f"Error {tbl}: {e}")
