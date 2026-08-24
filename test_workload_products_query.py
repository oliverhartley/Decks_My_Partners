import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
SELECT 
  w.workload_name,
  w.workload_details.primary_workload_pillar,
  w.workload_details.sales_play,
  w.workload_details.workload_solutions,
  w.workload_details.key_workload_products
FROM `concord-prod.service_cloudbi.workloads` w
WHERE w.workload_details.partner_id IN (
  "0014M00001h39BLQAY", "0014M00002JmizDQAR", "0014M00001h38aiQAA",
  "0014M00002M7lcJQAR", "0014M00001kxZPMQA2", "0014M00001uFlbSQAS",
  "0014M00002GGNRCQA5", "0014M00001h35nAQAQ", "001Kf000013fuVXIAY"
)
  AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
LIMIT 20
"""
schema, rows = run_query(sql)
print(f"Workload records with product fields: {len(rows)}")
for r in rows:
    wname = r["f"][0].get("v")
    pil = r["f"][1].get("v")
    play = r["f"][2].get("v")
    sol = r["f"][3].get("v")
    prods_raw = r["f"][4].get("v")
    prods = [x.get("v") for x in prods_raw] if isinstance(prods_raw, list) else prods_raw
    print(f"Workload: {wname[:25]} | Pillar: {pil} | Play: {play} | Sol: {sol} | Prods: {prods}")
