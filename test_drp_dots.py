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

def get_workload_counts_by_pillar(safe_name):
    csv_file = f"followup_data_synced/{safe_name}_synced.csv"
    counts = {k: 0 for k in PILLAR_MAPPING}
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) > 8:
                    w_pil = row[8].strip()
                    for drp_pil, synonyms in PILLAR_MAPPING.items():
                        if any(s.lower() in w_pil.lower() for s in synonyms):
                            counts[drp_pil] += 1
    return counts

def compute_dot(drp_profiles, pillar_workloads):
    p = 0
    try:
        p = int(drp_profiles)
    except:
        p = 0
    w = pillar_workloads
    
    if w > 0 and p == 0:
        return f"🔴 Gap (0 / {w} wkls)"
    elif w > 0 and p < w:
        return f"🟡 Constrained ({p} / {w} wkls)"
    elif p >= w and (p > 0 or w > 0):
        return f"🟢 Ready ({p} / {w} wkls)" if w > 0 else f"🟢 Capacity ({p} profiles)"
    else:
        return "⚪ No Demand"

# Test for Zenta
w_counts = get_workload_counts_by_pillar("Comercializadora_Zenta_Group_SPA")
print("Zenta workload counts by pillar:", w_counts)
with open("drp_data_full/Comercializadora_Zenta_Group_SPA_drp_full.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    headers = next(reader)
    for row in reader:
        pil = row[0]
        sol = row[1]
        prod = row[2]
        tot = row[5]
        w = w_counts.get(pil, 0)
        dot = compute_dot(tot, w)
        if tot or w > 0:
            print(f"  {pil[:15]} | {prod[:25]} | DRP: {tot or '0'} | Wkls: {w} -> {dot}")
