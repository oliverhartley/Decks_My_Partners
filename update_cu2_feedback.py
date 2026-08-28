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

# Build clean rows:
# Row 1: Partner Info & Last Update
# Row 2: Thin empty row
# Row 3: Alert Explanation & Legend Pills
# Row 4: Thin empty row
# Row 5: Main Header
# Rows 6+: Data rows
new_rows = [
    ["Partner:", "CU2 CLOUD TEC STORE SL", "", "", "Last Update:", "24 - Aug 2026", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    header_row
]
new_rows.extend(data_rows)

out_csv = "cu2_feedback_temp.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

# Clear and import
subprocess.run([GSHEETS, "mutate", "clear", SSID, "'Follow_up'!A1:Z2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", SSID, "--range", "'Follow_up'!2:2000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", SSID, out_csv, "--sheet", "Follow_up"], capture_output=True)

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
    # 2. Clear old merges
    {
      "unmergeCells": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 0,
          "endRowIndex": 10,
          "startColumnIndex": 0,
          "endColumnIndex": 17
        }
      }
    },
    # 3. Add clean merges:
    # Row 1: Partner Name B1:D1
    {
      "mergeCells": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
        "mergeType": "MERGE_ALL"
      }
    },
    # Row 3: Explanation B3:C3
    {
      "mergeCells": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
        "mergeType": "MERGE_ALL"
      }
    },
    # Row 3: Medium F3:G3
    {
      "mergeCells": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7},
        "mergeType": "MERGE_ALL"
      }
    },
    # Row 3: Normal H3:I3
    {
      "mergeCells": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9},
        "mergeType": "MERGE_ALL"
      }
    },

    # 4. Format Row 1 (Metadata)
    # A1 (Partner label)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {
          "userEnteredFormat": {
            "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
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
            "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
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

    # 5. Format Row 3 (Explanation & Legend)
    # A3 (Label)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {
          "userEnteredFormat": {
            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
            "horizontalAlignment": "RIGHT"
          }
        },
        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
      }
    },
    # B3:C3 (Explanation)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
        "cell": {
          "userEnteredFormat": {
            "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
            "horizontalAlignment": "LEFT"
          }
        },
        "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
      }
    },
    # D3 (Critical)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4},
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
    # E3 (High)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5},
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
    # F3:G3 (Medium)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7},
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
    # H3:I3 (Normal)
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9},
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

    # 6. Format Main Table Header (Row 5, index 4)
    # Cols A to O (Automated CRM Data) -> Modern Corporate Deep Blue #1A73E8
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 15},
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
        "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 15, "endColumnIndex": 17},
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

    # 7. Format Data Rows (startRowIndex: 5 to num_total_rows)
    # Alignments requested by user:
    # Customer Account Name (Col 0) -> LEFT
    # Workload Name (Col 2) -> LEFT
    # Opportunity Name (Col 4) -> LEFT
    # Expert Requests (Col 5) -> LEFT
    # Customer Sub Region (Col 6) -> LEFT
    # Customer Micro Region (Col 7) -> LEFT
    # Primary Workload Pillar (Col 8) -> LEFT
    # Sales Play (Col 9) -> LEFT
    # Workload Solution (Col 10) -> LEFT
    # Workload Progress (Col 11) -> LEFT
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 2, "endColumnIndex": 3},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 4, "endColumnIndex": 12},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # Account Tier (Col 1) -> CENTER
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 1, "endColumnIndex": 2},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # Capacity Status (Col 3) -> CENTER
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 3, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # Begin Date & Prod Date (Cols 12-14) -> CENTER
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 12, "endColumnIndex": 14},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # Right align ARR USD (Col 14) and format with currency numberFormat
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 14, "endColumnIndex": 15},
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
    # Subtle green tint for manual entry columns P & Q (Cols 15-17) -> LEFT
    {
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 5, "endRowIndex": num_total_rows, "startColumnIndex": 15, "endColumnIndex": 17},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, # #F1F8F5
            "horizontalAlignment": "LEFT"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"
      }
    },

    # 8. Add clean borders across the table
    {
      "updateBorders": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 4,
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
    # 9. Set Basic Filter across headers and data
    {"clearBasicFilter": {"sheetId": 0}},
    {
      "setBasicFilter": {
        "filter": {
          "range": {
            "sheetId": 0,
            "startRowIndex": 4,
            "endRowIndex": num_total_rows,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }
        }
      }
    },
    # 10. Conditional Formatting Rules (Data starts on row 6 -> $L6 and $N6)
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [{
            "sheetId": 0,
            "startRowIndex": 5,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($L6,3)=\"0-2\",LEFT($L6,2)=\"3:\"), $N6<>\"\", ($N6-TODAY())<=14)"}]
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
            "startRowIndex": 5,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($L6,3)=\"0-2\",LEFT($L6,2)=\"3:\"), $N6<>\"\", ($N6-TODAY())>=15, ($N6-TODAY())<=30)"}]
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
            "startRowIndex": 5,
            "endRowIndex": 2000,
            "startColumnIndex": 0,
            "endColumnIndex": 17
          }],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [{"userEnteredValue": "=AND(OR(LEFT($L6,3)=\"0-2\",LEFT($L6,2)=\"3:\"), $N6<>\"\", ($N6-TODAY())>=31, ($N6-TODAY())<=45)"}]
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

# Add zebra striping for rows (only on automated cols 0 to 15)
for r_idx in range(5, num_total_rows):
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

# Set row heights:
# Row 1 (Metadata): 30px
# Row 2 (Thin Row): 8px
# Row 3 (Legend & Explanation): 28px
# Row 4 (Thin Row): 8px
# Row 5 (Table Header): 36px
# Data rows: 26px
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 30},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 1, "endIndex": 2},
        "properties": {"pixelSize": 8},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 2, "endIndex": 3},
        "properties": {"pixelSize": 28},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 3, "endIndex": 4},
        "properties": {"pixelSize": 8},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 4, "endIndex": 5},
        "properties": {"pixelSize": 36},
        "fields": "pixelSize"
    }
})
batch_req["requests"].append({
    "updateDimensionProperties": {
        "range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 5, "endIndex": num_total_rows},
        "properties": {"pixelSize": 26},
        "fields": "pixelSize"
    }
})

# Set column widths
col_widths = {
    0: 280,  # Customer Account Name
    1: 90,   # Account Tier
    2: 240,  # Workload Name
    3: 200,  # Capacity Status
    4: 260,  # Opportunity Name
    5: 180,  # Expert Requests (expanded for dual links)
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

# Add multi-link rich text for Cortex Sap in Expert Requests (Row 12 -> index 12 in new_rows, which is data row 8)
# Let's find exactly which row has Cortex Sap in new_rows
cortex_row_idx = None
for idx, r in enumerate(new_rows):
    if len(r) > 2 and "Cortex Sap" in r[2]:
        cortex_row_idx = idx
        break

if cortex_row_idx is not None:
    batch_req["requests"].append({
        "updateCells": {
            "range": {
                "sheetId": 0,
                "startRowIndex": cortex_row_idx,
                "endRowIndex": cortex_row_idx + 1,
                "startColumnIndex": 5,
                "endColumnIndex": 6
            },
            "rows": [{
                "values": [{
                    "userEnteredValue": {
                        "stringValue": "ER-394016, ER-441904"
                    },
                    "textFormatRuns": [
                        {
                            "startIndex": 0,
                            "format": {
                                "link": {"uri": "https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf000000tPMMKA2/view"},
                                "underline": True,
                                "foregroundColor": {"red": 0.066, "green": 0.333, "blue": 0.8}
                            }
                        },
                        {
                            "startIndex": 9,
                            "format": {
                                "underline": False,
                                "foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}
                            }
                        },
                        {
                            "startIndex": 11,
                            "format": {
                                "link": {"uri": "https://vector.lightning.force.com/lightning/r/Expert_Request__c/aAuKf000000LfOJKA0/view"},
                                "underline": True,
                                "foregroundColor": {"red": 0.066, "green": 0.333, "blue": 0.8}
                            }
                        }
                    ]
                }]
            }],
            "fields": "userEnteredValue,textFormatRuns"
        }
    })

tmp_batch = "cu2_feedback_batch.json"
with open(tmp_batch, "w") as f:
    json.dump(batch_req, f, indent=2)

res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", tmp_batch], capture_output=True, text=True)
print("Batch Returncode:", res_batch.returncode)
if res_batch.returncode != 0:
    print("Batch Error:", res_batch.stderr)
else:
    print("Batch Success!")

# Freeze rows 1 to 5
subprocess.run([GSHEETS, "mutate", "freeze", SSID, "--sheet-id", "0", "--rows", "5"], capture_output=True)

print("Feedback updates applied successfully!")
