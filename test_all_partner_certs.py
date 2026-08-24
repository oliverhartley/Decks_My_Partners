import sys
sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Partner_Dashboard_v2")
from query_bq import run_query

PARTNER_CERT_PIDS = {
    "Comercializadora Zenta Group SPA": ["0014M00001h39BLQAY", "0014M00001m9woLQAQ", "001Kf000012gqs3IAA"],
    "Tech Pulse SPA (Axmos)": ["0014M00002JmizDQAR", "001Kf00001G4DmBIAV", "001Kf0000149iw9IAA"],
    "Devaid SPA": ["0014M00001h38aiQAA", "0014M00001m9sVvQAI"],
    "UCLOUD STORE COLOMBIA S A S": ["0014M00002M7lcJQAR"],
    "TIVIT COLOMBIA S A S": ["0014M00001kxZPMQA2", "001Kf0000150rJ2IAI", "0014M00001m9v8HQAQ"],
    "VPN Soluçoes em TI LTDA (Venha para Nuvem)": ["0014M00001uFlbSQAS", "0014M00002C1I0PQAV"],
    "MadeinWeb S/A": ["0014M00002GGNRCQA5", "001Kf000013hWaOIAU"],
    "CU2 CLOUD TEC STORE SL": ["0014M00001h35nAQAQ", "0014M00001w6MZzQAM", "0014M00002M7ryLQAR", "001Kf000010ctuwIAA", "0014M00002N5mLOQAZ"],
    "Consiti (Consultoría y Soluciones Informáticas)": ["001Kf000013fuVXIAY", "001Kf00001FoCy9IAF"]
}

for pname, pids in PARTNER_CERT_PIDS.items():
    pids_str = ", ".join([f"\"{x}\"" for x in pids])
    sql = f"""
    SELECT 
      p.certification_details.certification_name,
      p.certification_details.certification_type,
      p.certification_details.certification_sub_type,
      p.partner_contact_profile_details.profile_name,
      p.partner_contact_profile_details.lms_user_email,
      CAST(p.certification_details.certification_issued_date AS STRING) as issued_date,
      CAST(p.certification_details.certification_expiration_date AS STRING) as expiration_date,
      p.partner_details.partner_name
    FROM `concord-prod.service_cloudbi.partner_certifications` p
    WHERE p.partner_details.sfdc_partner_id IN ({pids_str})
      AND p.reporting_month = (SELECT MAX(reporting_month) FROM `concord-prod.service_cloudbi.partner_certifications`)
    ORDER BY p.certification_details.certification_type, p.certification_details.certification_name, p.partner_contact_profile_details.profile_name
    """
    schema, rows = run_query(sql)
    print(f"\n{pname}: {len(rows)} active certifications/accreditations")
    for r in rows[:3]:
        print("  ", [c.get("v") for c in r["f"]])
