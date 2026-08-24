import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

tables_to_test = [
    "concord-prod.service_gcpn.delivery_readiness_portal_profiles",
    "concord-prod.service_partnercoe.drp_partner_master",
    "concord-prod.service_partnercoe.view_delivery_capacity_dri",
    "concord-prod.service_partnercoe.view_delivery_capacity_dri_profile",
    "concord-prod.service_cloudbi.partner_certifications",
    "concord-prod.service_gcpn.partner_certifications",
    "concord-prod.service_partner360.partner_certifications",
    "concord-prod.service_partnerlifecycle.competencies"
]

for tbl in tables_to_test:
    try:
        schema, rows = run_query(f"SELECT * FROM `{tbl}` LIMIT 1")
        cnt = len(schema["fields"])
        print(f"SUCCESS: {tbl} ({cnt} fields)")
    except Exception as e:
        print(f"FAILED: {tbl} -> {e}")
