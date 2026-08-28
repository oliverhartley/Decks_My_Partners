import json
import csv
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew" # CU2

# 1. Unmerge any existing merges on sheet 0
res_info = subprocess.run([GSHEETS, "readonly", "info", SSID, "--json"], capture_output=True, text=True)
if res_info.returncode == 0:
    info_data = json.loads(res_info.stdout)
    sheet0 = info_data["sheets"][0]
    merges = sheet0.get("merges", [])
    if merges:
        unmerge_reqs = []
        for m in merges:
            unmerge_reqs.append({
                "unmergeCells": {
                    "range": m
                }
            })
        tmp_unmerge = "temp_unmerge.json"
        with open(tmp_unmerge, "w") as f:
            json.dump({"requests": unmerge_reqs}, f)
        subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", tmp_unmerge], capture_output=True)

# 2. Read raw CSV
src_csv = "followup_data_latest/CU2_CLOUD_TEC_STORE_SL_followup.csv"
rows = []
with open(src_csv, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for r in reader:
        rows.append(r)

# Row 10 in CSV is the header row
header_row = [
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
data_rows = rows[11:]

# Build clean rows
# Row 1: Partner Info & Last Update
# Row 2: Alert Legend
# Row 3: Blank separator
# Row 4: Main Header
# Row 5+: Data rows
new_rows = [
    ["Partner:", "", "CU2 CLOUD TEC STORE SL", "Last Update:", "24 - Aug 2026", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["Alert Legend (Stage 0-3):", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "⚪ Normal (>45d / Stage 4+)", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    header_row
]
new_rows.extend(data_rows)

out_csv = "cu2_redesign_clean.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

# Clear and re-import
subprocess.run([GSHEETS, "mutate", "clear", SSID, "'Follow_up'!A1:Z2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", SSID, "--range", "'Follow_up'!2:2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", SSID, out_csv, "--sheet", "Follow_up"], capture_output=True)

# Freeze rows 1 to 4
subprocess.run([GSHEETS, "mutate", "freeze", SSID, "--sheet-id", "0", "--rows", "4"], capture_output=True)

# Format Top Metadata (Row 1)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "1",
    "--bold",
    "--fg-color", "#5F6368",
    "--align", "RIGHT"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "2", "--end-col", "3",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--fg-color", "#1A73E8",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "3", "--end-col", "4",
    "--bold",
    "--fg-color", "#5F6368",
    "--align", "RIGHT"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "4", "--end-col", "5",
    "--bold",
    "--bg-color", "#E6F4EA",
    "--fg-color", "#137333",
    "--align", "CENTER"
], capture_output=True)

# Format Row 2 (Legend)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "0", "--end-col", "1",
    "--bold",
    "--align", "RIGHT",
    "--fg-color", "#5F6368"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "2", "--end-col", "3",
    "--bold",
    "--bg-color", "#FCE8E6",
    "--fg-color", "#C5221F",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "3", "--end-col", "4",
    "--bold",
    "--bg-color", "#FEF7E0",
    "--fg-color", "#B06000",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "4", "--end-col", "5",
    "--bold",
    "--bg-color", "#FFF9DB",
    "--fg-color", "#7C4A03",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "5", "--end-col", "6",
    "--bold",
    "--bg-color", "#F1F3F4",
    "--fg-color", "#5F6368",
    "--align", "CENTER"
], capture_output=True)

# Format Main Table Header (Row 4, index 3)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "3", "--end-row", "4",
    "--start-col", "0", "--end-col", "15",
    "--bold",
    "--bg-color", "#1A73E8",
    "--fg-color", "#FFFFFF",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "3", "--end-row", "4",
    "--start-col", "15", "--end-col", "17",
    "--bold",
    "--bg-color", "#137333",
    "--fg-color", "#FFFFFF",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)

# Format Data Rows (start-row 4)
# Alternating rows (zebra striping)
for r_idx in range(4, len(new_rows)):
    bg = "#FFFFFF" if r_idx % 2 == 0 else "#F8F9FA"
    subprocess.run([
        GSHEETS, "mutate", "format", SSID,
        "--sheet-id", "0",
        "--start-row", str(r_idx), "--end-row", str(r_idx + 1),
        "--start-col", "0", "--end-col", "15",
        "--bg-color", bg
    ], capture_output=True)

# Alignments
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "2000",
    "--start-col", "1", "--end-col", "2",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "2000",
    "--start-col", "3", "--end-col", "4",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "2000",
    "--start-col", "5", "--end-col", "6",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "2000",
    "--start-col", "12", "--end-col", "14",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "2000",
    "--start-col", "14", "--end-col", "15",
    "--align", "RIGHT"
], capture_output=True)

# Light green tint for manual entry data columns (Cols 15-17)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "2000",
    "--start-col", "15", "--end-col", "17",
    "--bg-color", "#F1F8F5"
], capture_output=True)

# Batch: Filter & Conditional Formatting & Borders
req = {
  "requests": [
    {"clearBasicFilter": {"sheetId": 0}},
    {
      "setBasicFilter": {
        "filter": {
          "range": {
            "sheetId": 0,
            "startRowIndex": 3,
            "endRowIndex": len(new_rows),
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }
        }
      }
    },
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 4,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($L5,3)=\"0-2\",LEFT($L5,2)=\"3:\"), $N5<>\"\", ($N5-TODAY())<=14)"}]
            },
            "format": {
              "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}
            }
          }
        },
        "index": 0
      }
    },
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 4,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($L5,3)=\"0-2\",LEFT($L5,2)=\"3:\"), $N5<>\"\", ($N5-TODAY())>=15, ($N5-TODAY())<=30)"}]
            },
            "format": {
              "backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}
            }
          }
        },
        "index": 1
      }
    },
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 4,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($L5,3)=\"0-2\",LEFT($L5,2)=\"3:\"), $N5<>\"\", ($N5-TODAY())>=31, ($N5-TODAY())<=45)"}]
            },
            "format": {
              "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}
            }
          }
        },
        "index": 2
      }
    }
  ]
}

with open("cu2_redesign_clean_batch.json", "w") as f:
    json.dump(req, f, indent=2)

res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", "cu2_redesign_clean_batch.json"], capture_output=True, text=True)
print("Batch Returncode:", res_batch.returncode)

# Column Widths
col_widths = {
    0: 280,  # Customer Account Name
    1: 90,   # Account Tier
    2: 240,  # Workload Name
    3: 200,  # Capacity Status
    4: 260,  # Opportunity Name
    5: 110,  # Expert Requests
    6: 120,  # Customer Sub Region
    7: 130,  # Customer Micro Region
    8: 180,  # Primary Workload Pillar
    9: 220,  # Sales Play
    10: 220, # Workload Solution
    11: 170, # Workload Progress
    12: 130, # Begin Migration Date
    13: 130, # Production Date
    14: 150, # ARR USD
    15: 160, # Last Touch
    16: 160  # Link
}

for col_idx, width in col_widths.items():
    subprocess.run([
        GSHEETS, "mutate", "set-col-width", SSID,
        "--sheet-id", "0",
        "--start-col", str(col_idx),
        "--end-col", str(col_idx + 1),
        "--pixels", str(width)
    ], capture_output=True)

print("Clean redesign finished successfully!")
