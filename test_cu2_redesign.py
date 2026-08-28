import json
import csv
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew" # CU2

# Read latest raw data from followup_data_latest/CU2_CLOUD_TEC_STORE_SL_followup.csv
src_csv = "followup_data_latest/CU2_CLOUD_TEC_STORE_SL_followup.csv"
rows = []
with open(src_csv, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for r in reader:
        rows.append(r)

header_row = rows[10]
data_rows = rows[11:]

# Build new structured rows:
# Row 1: Partner & Last Update
# Row 2: Sleek horizontal Legend
# Row 3: Blank separator
# Row 4: Main table header
# Row 5+: Data rows

new_rows = [
    ["Partner:", "CU2 CLOUD TEC STORE SL", "", "Last Update:", "24 - Aug", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["Alert Legend (Stage 0-3):", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "⚪ Normal (>45d / Stage 4+)", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    header_row
]
new_rows.extend(data_rows)

out_csv = "cu2_redesign_temp.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

# 1. Clear and import new CSV
subprocess.run([GSHEETS, "mutate", "clear", SSID, "'Follow_up'!A1:Z2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", SSID, "--range", "'Follow_up'!2:2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", SSID, out_csv, "--sheet", "Follow_up"], capture_output=True)

# 2. Freeze rows 1 to 4 (header is at row 4, index 3)
subprocess.run([GSHEETS, "mutate", "freeze", SSID, "--sheet-id", "0", "--rows", "4"], capture_output=True)

# 3. Format Top Row 1 (Metadata)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "1",
    "--bold",
    "--bg-color", "#F1F3F4",
    "--align", "RIGHT"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "1", "--end-col", "3",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--fg-color", "#1A73E8",
    "--align", "LEFT"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "3", "--end-col", "4",
    "--bold",
    "--bg-color", "#F1F3F4",
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

# 4. Format Row 2 (Horizontal Legend)
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
    "--start-col", "1", "--end-col", "2",
    "--bold",
    "--bg-color", "#FCE8E6",
    "--fg-color", "#C5221F",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "2", "--end-col", "3",
    "--bold",
    "--bg-color", "#FEF7E0",
    "--fg-color", "#B06000",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "3", "--end-col", "4",
    "--bold",
    "--bg-color", "#FFF9DB",
    "--fg-color", "#7C4A03",
    "--align", "CENTER"
], capture_output=True)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "4", "--end-col", "5",
    "--bold",
    "--bg-color", "#F1F3F4",
    "--fg-color", "#5F6368",
    "--align", "CENTER"
], capture_output=True)

# 5. Format Main Table Header (Row 4, index 3)
# Automated Columns A to O (indices 0 to 15) -> Modern Deep Navy/Google Blue #1A73E8
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

# Manual Columns P and Q (indices 15 to 17) -> Elegant Forest Green #137333
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

# 6. Format Data Rows (start-row 4)
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
    "--bg-color", "#F6FCF8"
], capture_output=True)

# 7. Apply Raw-Batch for Conditional Formatting & Filter
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
              "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902} # Soft rose #FCE8E6
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
              "backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878} # Soft amber #FEF7E0
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
              "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859} # Soft yellow #FFF9DB
            }
          }
        },
        "index": 2
      }
    }
  ]
}

with open("cu2_redesign_batch.json", "w") as f:
    json.dump(req, f, indent=2)

res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", "cu2_redesign_batch.json"], capture_output=True, text=True)
print("Batch Returncode:", res_batch.returncode)

# Set custom generous column widths
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

print("Redesign applied successfully!")
