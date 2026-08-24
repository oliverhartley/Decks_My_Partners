import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = "SELECT * FROM `concord-prod.service_cloudbi.partner_workloads` LIMIT 1"
schema, rows = run_query(sql)
print(f"partner_workloads total fields: {len(schema['fields'])}")
for f in schema["fields"]:
    name = f["name"]
    t = f.get("type")
    if any(k in name.lower() for k in ["product", "solution", "pillar", "tech", "service", "sku", "cloud", "play", "type", "use_case", "category"]):
        print(f"  {name}: {t}")
