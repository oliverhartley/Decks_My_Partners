import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q" # Zenta

# 1. Clear and import CSV
subprocess.run([GSHEETS, "mutate", "clear", SSID, "'Follow_up'!A1:Z2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", SSID, "--range", "'Follow_up'!2:2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", SSID, "test_zenta_legend.csv", "--sheet", "Follow_up"], capture_output=True)

# 2. Freeze at row 8 (header row)
subprocess.run([GSHEETS, "mutate", "freeze", SSID, "--sheet-id", "0", "--rows", "8"], capture_output=True)

# 3. Format Legend
# Title row 0
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "0", "--end-row", "1",
    "--start-col", "0", "--end-col", "3",
    "--bold"
], capture_output=True)

# Legend Header row 1
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "1", "--end-row", "2",
    "--start-col", "0", "--end-col", "3",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--align", "CENTER"
], capture_output=True)

# Legend Red row 2
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "2", "--end-row", "3",
    "--start-col", "0", "--end-col", "3",
    "--bold",
    "--bg-color", "#EA4335"
], capture_output=True)

# Legend Light Red row 3
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "3", "--end-row", "4",
    "--start-col", "0", "--end-col", "3",
    "--bg-color", "#FCE8E6"
], capture_output=True)

# Legend Light Yellow row 4
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "4", "--end-row", "5",
    "--start-col", "0", "--end-col", "3",
    "--bg-color", "#FFF2CC"
], capture_output=True)

# 4. Format Main Headers (row 7 in 0-based)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "7", "--end-row", "8",
    "--start-col", "0", "--end-col", "18",
    "--bold",
    "--bg-color", "#E8F0FE",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)

# Format Col Q & R headers (Col 16 to 18)
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "7", "--end-row", "8",
    "--start-col", "16", "--end-col", "18",
    "--bold",
    "--bg-color", "#E6F4EA",
    "--align", "CENTER",
    "--wrap"
], capture_output=True)

# Center Account Tier (col 2) and Capacity (col 4) for data rows
subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "8", "--end-row", "2000",
    "--start-col", "2", "--end-col", "3",
    "--align", "CENTER"
], capture_output=True)

subprocess.run([
    GSHEETS, "mutate", "format", SSID,
    "--sheet-id", "0",
    "--start-row", "8", "--end-row", "2000",
    "--start-col", "4", "--end-col", "5",
    "--align", "CENTER"
], capture_output=True)

# 5. Apply Entire Row Conditional Formatting
req = {
  "requests": [
    # Delete old conditional rules
    {"deleteConditionalFormatRule": {"sheetId": 0, "index": 0}},
    {"deleteConditionalFormatRule": {"sheetId": 0, "index": 0}},
    {"deleteConditionalFormatRule": {"sheetId": 0, "index": 0}},
    # 1. Red (0 to 14 days or overdue)
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 8,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 18
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($M9,3)=\"0-2\",LEFT($M9,2)=\"3:\"), $O9<>\"\", ($O9-TODAY())<=14)"}]
            },
            "format": {
              "backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510} # #F28B82 (soft red so text is legible across entire row)
            }
          }
        },
        "index": 0
      }
    },
    # 2. Light Red (15 to 30 days)
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 8,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 18
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($M9,3)=\"0-2\",LEFT($M9,2)=\"3:\"), $O9<>\"\", ($O9-TODAY())>=15, ($O9-TODAY())<=30)"}]
            },
            "format": {
              "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902} # #FCE8E6
            }
          }
        },
        "index": 1
      }
    },
    # 3. Light Yellow (31 to 45 days)
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 8,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 18
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($M9,3)=\"0-2\",LEFT($M9,2)=\"3:\"), $O9<>\"\", ($O9-TODAY())>=31, ($O9-TODAY())<=45)"}]
            },
            "format": {
              "backgroundColor": {"red": 1.0, "green": 0.949, "blue": 0.800} # #FFF2CC
            }
          }
        },
        "index": 2
      }
    }
  ]
}

with open("test_zenta_batch.json", "w") as f:
    json.dump(req, f, indent=2)

res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", "test_zenta_batch.json"], capture_output=True, text=True)
print("Batch Returncode:", res_batch.returncode)
print("Batch Stdout:", res_batch.stdout)
print("Batch Stderr:", res_batch.stderr)

subprocess.run([GSHEETS, "mutate", "autosize", SSID, "--sheet-id", "0", "--start-col", "0", "--end-col", "18"], capture_output=True)
print("✓ Completed test on Zenta!")
