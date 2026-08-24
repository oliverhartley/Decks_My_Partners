import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT DISTINCT
  consolidated_partner_id,
  standardized_partner_name,
  all_profile_count
FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_partner_info`
WHERE (
  LOWER(standardized_partner_name) LIKE "%zenta%"
  OR LOWER(standardized_partner_name) LIKE "%tech pulse%"
  OR LOWER(standardized_partner_name) LIKE "%axmos%"
  OR LOWER(standardized_partner_name) LIKE "%devaid%"
  OR LOWER(standardized_partner_name) LIKE "%ucloud%"
  OR LOWER(standardized_partner_name) LIKE "%tivit%"
  OR LOWER(standardized_partner_name) LIKE "%venha%"
  OR LOWER(standardized_partner_name) LIKE "%vpn%"
  OR LOWER(standardized_partner_name) LIKE "%madeinweb%"
  OR LOWER(standardized_partner_name) LIKE "%cu2%"
  OR LOWER(standardized_partner_name) LIKE "%consiti%"
)
ORDER BY standardized_partner_name
"""
schema, rows = run_query(sql)
print(f"Matched DRP partners in partner_info: {len(rows)}")
for r in rows:
    pid = r["f"][0].get("v")
    pname = r["f"][1].get("v")
    cnt = r["f"][2].get("v")
    print(f"  {pid} | {pname} | profiles={cnt}")
