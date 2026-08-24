import csv
import subprocess
import json

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q" # Zenta

# Read existing data rows from followup_data_latest
with open("followup_data_latest/Comercializadora_Zenta_Group_SPA_followup.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    main_headers = next(reader)
    data_rows = list(reader)

# Construct new CSV with Legend on top
legend_rows = [
    ["Production Date Alert Legend (Workloads in Stage 0-2 or 3)", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["Days Remaining (Production Date)", "Risk Level", "Alert Criteria / Stage", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["0 to 14 days (or overdue)", "🔴 Critical", "Production Date <= 14 days in Stage 0-2 or 3", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["15 to 30 days", "🌸 High", "Production Date 15-30 days in Stage 0-2 or 3", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["31 to 45 days", "🟡 Medium", "Production Date 31-45 days in Stage 0-2 or 3", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["> 45 days (or Stage >= 4)", "⚪ Normal", "Standard Timeline / Delivery", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""], # Row 7 empty
    main_headers
]

all_rows = legend_rows + data_rows

with open("test_zenta_legend.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_rows)

print(f"Total rows in test CSV: {len(all_rows)}")
