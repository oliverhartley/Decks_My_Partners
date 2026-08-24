import csv
import glob
import os

PILLAR_MAPPING = {
    "Application Modernization": ["Migrate Modernize and Build", "Application Modernization"],
    "Artificial Intelligence": ["Build with AI", "Infra AI", "Developer AI Assistance", "Customer Engagement", "Artificial Intelligence"],
    "Data & Analytics": ["Analytics", "Data & Analytics", "Data Cloud"],
    "Databases": ["Migrate and Modernize Databases", "Databases", "Database"],
    "Infrastructure Modernization": ["Migrate Modernize and Build", "Infrastructure Modernization", "Networking", "Storage", "Infrastructure"],
    "Security": ["Security"],
    "Workspace": ["Workspace", "Google Workspace"]
}

synced_files = glob.glob("followup_data_synced/*_synced.csv")
for f in synced_files:
    pname = os.path.basename(f).replace("_synced.csv", "").replace("_", " ")
    workloads_by_drp_pillar = {k: 0 for k in PILLAR_MAPPING}
    
    with open(f, "r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        next(reader, None)
        for row in reader:
            if len(row) > 8:
                w_pil = row[8].strip()
                for drp_pil, synonyms in PILLAR_MAPPING.items():
                    if any(s.lower() in w_pil.lower() for s in synonyms):
                        workloads_by_drp_pillar[drp_pil] += 1
                        
    print(f"\n{pname}:")
    for dp, w_cnt in workloads_by_drp_pillar.items():
        print(f"  - {dp}: {w_cnt} active workloads")
