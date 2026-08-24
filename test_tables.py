import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

candidates = [
    "concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile",
    "concord-prod.service_partnercoe_ops.view_drp_pdm_map",
    "concord-prod.service_cloudbi_partner_uat.partner_certifications",
    "concord-prod.service_vector_partner.partnercertifications",
    "concord-prod.service_cloudbi.partner_certifications",
    "concord-prod.service_cloudbi.learning_enablement_gc_certifications",
    "concord-prod.service_cloudbi.cepf_certs"
]

for tbl in candidates:
    try:
        schema, rows = run_query(f"SELECT * FROM `{tbl}` LIMIT 1")
        cnt = len(schema["fields"])
        print(f"SUCCESS: {tbl} ({cnt} fields)")
    except Exception as e:
        print(f"FAILED: {tbl} -> {e}")
