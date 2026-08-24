import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

for v in [
    "concord-prod.service_partnercoe_general.view_delivery_capacity_dri",
    "concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile",
    "concord-prod.service_partnercoe_general.view_delivery_capacity_partner_info"
]:
    sql = f"SELECT * FROM `{v}` LIMIT 1"
    try:
        schema, rows = run_query(sql)
        print(f"SUCCESS: {v} ({len(schema['fields'])} fields)")
        for f in schema['fields']:
            print(f"   {f['name']}: {f.get('type')}")
    except Exception as e:
        print(f"FAILED: {v} -> {e}")
