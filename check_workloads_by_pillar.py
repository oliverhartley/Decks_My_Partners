import csv
import os
import glob

synced_files = glob.glob("followup_data_synced/*_synced.csv")
for f in synced_files:
    pname = os.path.basename(f).replace("_synced.csv", "").replace("_", " ")
    pillar_counts = {}
    with open(f, "r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        next(reader, None)
        for row in reader:
            if len(row) > 8:
                pil = row[8].strip() or "Unassigned"
                pillar_counts[pil] = pillar_counts.get(pil, 0) + 1
    print(f"\n{pname} Workloads by Pillar:")
    for pil, cnt in sorted(pillar_counts.items(), key=lambda x: -x[1]):
        print(f"  - {pil}: {cnt}")
