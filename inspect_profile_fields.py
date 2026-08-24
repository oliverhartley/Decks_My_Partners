import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = "SELECT * FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` LIMIT 1"
schema, rows = run_query(sql)
for f in schema["fields"]:
    print(f"{f['name']}: {f.get('type')}")
