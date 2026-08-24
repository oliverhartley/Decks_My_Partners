import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

for tbl in [
    "concord-prod.service_cloudbi.partner_certifications",
    "concord-prod.service_cloudbi.learning_enablement_gc_certifications",
    "concord-prod.service_cloudbi.cepf_certs"
]:
    sql = f"SELECT * FROM `{tbl}` LIMIT 1"
    schema, rows = run_query(sql)
    print(f"\nSchema for {tbl}:")
    for f in schema["fields"]:
        fn = f["name"]
        ft = f.get("type")
        print(f"  {fn}: {ft}")
