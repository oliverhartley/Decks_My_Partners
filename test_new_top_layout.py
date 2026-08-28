import csv
import subprocess
import json
import datetime

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q" # Zenta
pname = "Comercializadora Zenta Group SPA"

now = datetime.datetime.now()
date_str = f"{now.day} - {now.strftime('%b')}"

# 17 columns headers (no Partner Name)
PARTNER_FOLLOWUP_HEADERS = [
    "Customer Account Name",
    "Account Tier",
    "Workload Name",
    "Capacity Status (DRP Readiness)",
    "Opportunity Name",
    "Expert Requests",
    "Customer Sub Region",
    "Customer Micro Region",
    "Primary Workload Pillar",
    "Sales Play",
    "Workload Solution",
    "Workload Progress",
    "Begin Migration Date",
    "Production Date",
    "Annual Gross Revenue (ARR USD)",
    "Last Touch",
    "Link"
]

TOP_BLOCK = [
    ["Partner:", pname, "", "Last Update:", date_str] + [""] * 12,
    [""] * 17,
    [""] * 17,
    ["Production Date Alert Legend (Workloads in Stage 0-2 or 3)", "", "", "", ""] + [""] * 12,
    ["Days Remaining (Production Date)", "Risk Level", "Alert Criteria / Stage", "", ""] + [""] * 12,
    ["0 to 14 days (or overdue)", "🔴 Critical", "Production Date <= 14 days in Stage 0-2 or 3", "", ""] + [""] * 12,
    ["15 to 30 days", "🌸 High", "Production Date 15-30 days in Stage 0-2 or 3", "", ""] + [""] * 12,
    ["31 to 45 days", "🟡 Medium", "Production Date 31-45 days in Stage 0-2 or 3", "", ""] + [""] * 12,
    ["> 45 days (or Stage >= 4)", "⚪ Normal", "Standard Timeline / Delivery", "", ""] + [""] * 12,
    [""] * 17,
    PARTNER_FOLLOWUP_HEADERS
]

# Read existing data rows from followup_data_latest (which currently has 18 columns, col 0 was partner)
data_rows = []
with open("followup_data_latest/Comercializadora_Zenta_Group_SPA_followup.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        # Find rows that are data rows (start with =HYPERLINK or have customer account name)
        if len(row) >= 18 and "vector.lightning.force.com" in row[0] and "Account" in row[0]:
            # omit col 0 (partner)
            data_rows.append(row[1:])

all_rows = TOP_BLOCK + data_rows

with open("test_zenta_top.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_rows)

print(f"Total rows in test CSV: {len(all_rows)}")
