import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

sql = """
WITH WorkloadsExpanded AS (
  SELECT 
    w.workload_details.partner_name,
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
)
SELECT 
  primary_workload_pillar,
  sales_play,
  workload_solutions,
  COUNT(*) as cnt
FROM WorkloadsExpanded
GROUP BY 1, 2, 3
ORDER BY cnt DESC
"""
schema, rows = run_query(sql)
print("Distinct Workload (Pillar / Sales Play / Solution) combinations:")
for r in rows:
    pil = r["f"][0].get("v") or "(empty)"
    play = r["f"][1].get("v") or "(empty)"
    sol = r["f"][2].get("v") or "(empty)"
    c = r["f"][3].get("v")
    print(f"  [{c} wkls] Pillar: {pil} | Sales Play: {play} | Solution: {sol}")
