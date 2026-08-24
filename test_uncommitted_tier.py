import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

PARTNER_CONFIGS = [
    {"partner": "Comercializadora Zenta Group SPA", "pids": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"]},
    {"partner": "Tech Pulse SPA (Axmos)", "pids": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"]},
    {"partner": "Devaid SPA", "pids": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"]},
    {"partner": "UCLOUD STORE COLOMBIA S A S", "pids": ["0014M00002M7lcJQAR"]},
    {"partner": "TIVIT COLOMBIA S A S", "pids": ["001Kf0000150rJ2IAI", "0014M00001kxZPMQA2", "0014M00001m9v8HQAQ"]},
    {"partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)", "pids": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"]},
    {"partner": "MadeinWeb S/A", "pids": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"]},
    {"partner": "CU2 CLOUD TEC STORE SL", "pids": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "001Kf000010cw8CIAQ", "0014M00002N5mLOQAZ"]},
    {"partner": "Consiti (Consultoría y Soluciones Informáticas)", "pids": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"]}
]

for cfg in PARTNER_CONFIGS:
    pname = cfg["partner"]
    pids_str = ", ".join([f"\"{x}\"" for x in cfg["pids"]])
    sql = f"""
    SELECT 
      COUNT(*) as total,
      COUNTIF(COALESCE(w.customer.segment, o.segment) != "Enterprise") as tier_2_3_all,
      COUNTIF(
        COALESCE(w.customer.segment, o.segment) != "Enterprise" 
        AND IFNULL(o.is_commit, FALSE) = FALSE 
        AND IFNULL(o.forecast_category_name, "") != "Commit"
      ) as uncommitted_tier_2_3
    FROM `concord-prod.service_cloudbi.workloads` w
    LEFT JOIN `concord-prod.service_cloudbi.opportunities` o
      ON w.opportunity_id = o.opportunity_id
    WHERE w.workload_details.partner_id IN ({pids_str})
      AND EXTRACT(YEAR FROM w.workload_details.sfdc_created_date) >= 2025
      AND (w.workload_details.workload_progress IS NULL OR (
             LOWER(w.workload_details.workload_progress) NOT LIKE "%closed%"
             AND w.workload_details.workload_progress NOT LIKE "5.%"
          ))
    """
    schema, rows = run_query(sql)
    r = rows[0]["f"]
    tot = r[0].get("v")
    t23 = r[1].get("v")
    uncomm = r[2].get("v")
    print(f"{pname}: total open 2025+ = {tot} | Tier 2 & 3 = {t23} | Uncommitted Tier 2 & 3 = {uncomm}")
