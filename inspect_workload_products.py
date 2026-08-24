import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT 
  w.partner_details.partner_name,
  w.workload_details.workload_name,
  w.workload_details.primary_workload_pillar,
  w.workload_details.workload_solution,
  w.workload_details.key_workload_products
FROM `concord-prod.service_cloudbi.partner_workloads` w
WHERE w.partner_details.sfdc_partner_id IN (
  "0014M00001h39BLQAY", "0014M00002JmizDQAR", "0014M00001h38aiQAA",
  "0014M00002M7lcJQAR", "0014M00001kxZPMQA2", "0014M00001uFlbSQAS",
  "0014M00002GGNRCQA5", "0014M00001h35nAQAQ", "001Kf000013fuVXIAY"
)
  AND w.reporting_date = (SELECT MAX(reporting_date) FROM `concord-prod.service_cloudbi.partner_workloads`)
  AND (w.workload_details.key_workload_products IS NOT NULL OR w.workload_details.workload_solution IS NOT NULL)
LIMIT 25
"""
schema, rows = run_query(sql)
print(f"Sample workload product/solution records: {len(rows)}")
for r in rows:
    pname = r["f"][0].get("v")
    wname = r["f"][1].get("v")
    pil = r["f"][2].get("v")
    sol = r["f"][3].get("v")
    prod = r["f"][4].get("v")
    print(f"[{pname[:20]}] Wkl: {wname[:25]} | Pillar: {pil} | Sol: {sol} | Prods: {prod}")
