import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = "SELECT * FROM `concord-prod.service_cloudbi.partner_certifications` LIMIT 1"
schema, rows = run_query(sql)
for f in schema["fields"]:
    print(f["name"])
    if "fields" in f:
        for sub in f["fields"]:
            print(f"   - {sub['name']}: {sub.get('type')}")
