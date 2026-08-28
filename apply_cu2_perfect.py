import json
import csv
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew" # CU2

# 1. Read raw CSV
src_csv = "followup_data_latest/CU2_CLOUD_TEC_STORE_SL_followup.csv"
rows = []
with open(src_csv, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for r in reader:
        rows.append(r)

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
new_rows = [
    ["Partner:", "CU2 CLOUD TEC STORE SL", "", "", "Last Update:", "24 - Aug 2026", "", "", "", "", "", "", "", "", "", "", ""],
    ["Alert Legend (Stage 0-3):", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "⚪ Normal (>45d / Stage 4+)", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    header_row
]
new_rows.extend(data_rows)

out_csv = "cu2_redesign_perfect.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

# Clear and import
subprocess.run([GSHEETS, "mutate", "clear", SSID, "'Follow_up'!A1:Z2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", SSID, "--range", "'Follow_up'!2:2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", SSID, out_csv, "--sheet", "Follow_up"], capture_output=True)

# Build comprehensive batch update request to reset formats, merge, style, borders, conditional formatting
num_total_rows = len(new_rows)

batch_req = {
  "requests": [
    # 1. Reset all formatting on sheet 0 across rows 0 to 50, cols 0 to 20
    {
      "repeatCell": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 0,
          "endRowIndex": 50,
          "startColumnIndex": 0,
          "endColumnIndex": 20
        },
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
            "textFormat": {
              "foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, # #202124
              "fontSize": 10,
              "bold": False,
              "italic": False,
              "fontFamily": "Arial"
            },
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "OVERFLOW_CELL"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
      }
    },
    # 2. Clear old merges and add clean merge for Partner Name B1:D1
    {
      "unmergeCells": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 0,
          "endRowIndex": 10,
          "startColumnIndex": 0,
          "endColumnIndex": 10
        }
      }
    },
    {
      "mergeCells": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 0,
          "endRowIndex": 1,
          "startColumnIndex": 1,
          "endColumnIndex": 4
        },
        "mergeType": "MERGE_ALL"
      }
    },
    # 3. Format Row 1 (Metadata)
    # A1 (Partner label)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {
          "userEnteredFormat": {
            "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, # #5F6368
            "horizontalAlignment": "RIGHT"
          }
        },
        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
      }
    },
    # B1:D1 (Partner Name)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, # #E8F0FE
            "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, # #1A73E8
            "horizontalAlignment": "CENTER"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
      }
    },
    # E1 (Last Update label)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5},
        "cell": {
          "userEnteredFormat": {
            "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, # #5F6368
            "horizontalAlignment": "RIGHT"
          }
        },
        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
      }
    },
    # F1 (Last Update Date)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, # #E6F4EA
            "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, # #137333
            "horizontalAlignment": "CENTER"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
      }
    },
    # 4. Format Row 2 (Legend)
    # A2 (Label)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {
          "userEnteredFormat": {
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
            "horizontalAlignment": "RIGHT"
          }
        },
        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
      }
    },
    # C2 (Critical)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 2, "endColumnIndex": 3},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}, # #FCE8E6
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.77, "green": 0.13, "blue": 0.12}}, # #C5221F
            "horizontalAlignment": "CENTER"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
      }
    },
    # D2 (High)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 3, "endColumnIndex": 4},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}, # #FEF7E0
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.69, "green": 0.38, "blue": 0.0}}, # #B06000
            "horizontalAlignment": "CENTER"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
      }
    },
    # E2 (Medium)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 4, "endColumnIndex": 5},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}, # #FFF9DB
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.49, "green": 0.29, "blue": 0.01}}, # #7C4A03
            "horizontalAlignment": "CENTER"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
      }
    },
    # F2 (Normal)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 5, "endColumnIndex": 6},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, # #F1F3F4
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, # #5F6368
            "horizontalAlignment": "CENTER"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
      }
    },
    # 5. Format Main Table Header (Row 4, index 3)
    # Cols A to O (Automated CRM Data) -> Modern Corporate Deep Blue #1A73E8
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 15},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, # #1A73E8
            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
      }
    },
    # Cols P to Q (Manual Entry Columns) -> Distinct Forest Green #137333
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 15, "endColumnIndex": 17},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, # #137333
            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
      }
    },
    # 6. Format Data Rows (startRowIndex: 4 to num_total_rows)
    # Alternating zebra striping & alignments
    # Center align Tier (Col 1), Capacity (Col 3), ER (Col 5), Begin Date (Col 12), Prod Date (Col 13)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": num_total_rows, "startColumnIndex": 1, "endColumnIndex": 2},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": num_total_rows, "startColumnIndex": 3, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": num_total_rows, "startColumnIndex": 5, "endColumnIndex": 6},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": num_total_rows, "startColumnIndex": 12, "endColumnIndex": 14},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # Right align ARR USD (Col 14) and format with currency numberFormat
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": num_total_rows, "startColumnIndex": 14, "endColumnIndex": 15},
        "cell": {
          "userEnteredFormat": {
            "horizontalAlignment": "RIGHT",
            "numberFormat": {
              "type": "CURRENCY",
              "pattern": "$#,##0.00"
            }
          }
        },
        "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"
      }
    },
    # Subtle green tint for manual entry columns P & Q
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": num_total_rows, "startColumnIndex": 15, "endColumnIndex": 17},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957} # #F1F8F5
          }
        },
        "fields": "userEnteredFormat(backgroundColor)"
      }
    },
    # 7. Add clean borders across the table
    {
      "updateBorders": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 3,
          "endRowIndex": num_total_rows,
          "startColumnIndex": 0,
          "endColumnIndex": 17
        },
        "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
      }
    },
    # 8. Set Basic Filter
    {"clearBasicFilter": {"sheetId": 0}},
    {
      "setBasicFilter": {
        "filter": {
          "range": {
            "sheetId": 0,
            "startRowIndex": 3,
            "endRowIndex": num_total_rows,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }
        }
      }
    },
    # 9. Conditional Formatting Rules
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

# Add zebra striping for rows (only on automated cols 0 to 15, since 15-17 has green tint)
for r_idx in range(4, num_total_rows):
    if r_idx % 2 == 1: # odd rows get light tint
        batch_req["requests"].append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 15},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980} # #F8F9FA
                    }
                },
                "fields": "userEnteredFormat(backgroundColor)"
            }
        })

# Set row heights: Row 1 (Metadata) = 32px, Row 2 (Legend) = 26px, Row 4 (Header) = 36px, Data rows = 24px
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 32},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 1, "endIndex": 2},
        "properties": {"pixelSize": 26},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 3, "endIndex": 4},
        "properties": {"pixelSize": 36},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 4, "endIndex": num_total_rows},
        "properties": {"pixelSize": 26},
        "fields": "pixelSize"
    }
})

# Set column widths in one batch!
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
    batch_req["requests"].append({
        "updateDimensionProperties": {
            "range": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
            "properties": {"pixelSize": width},
            "fields": "pixelSize"
        }
    })

tmp_batch = "cu2_perfect_batch.json"
with open(tmp_batch, "w") as f:
    json.dump(batch_req, f, indent=2)

res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", tmp_batch], capture_output=True, text=True)
print("Single Batch Returncode:", res_batch.returncode)
if res_batch.returncode != 0:
    print("Batch Error:", res_batch.stderr)
else:
    print("Batch Success!")

# Freeze rows 1 to 4
subprocess.run([GSHEETS, "mutate", "freeze", SSID, "--sheet-id", "0", "--rows", "4"], capture_output=True)

print("All perfect formatting applied in single atomic batch!")
