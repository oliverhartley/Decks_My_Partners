import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = "SELECT * FROM `concord-prod.service_cloudbi.partner_workloads` LIMIT 1"
schema, rows = run_query(sql)
print(f"partner_workloads total fields: {len(schema['fields'])}")
for idx, f in enumerate(schema['fields']):
    fname = f['name']
    ftype = f.get('type')
    print(f"  {idx+1}. {fname} ({ftype})")
