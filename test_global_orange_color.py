import json
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"
SID = 713943462  # All_Workloads_Follow_up
ROW_COUNT = 797

# 1. Update Cell Text in E3: 🟧 High (15-30d)
subprocess.run([GSHEETS, "mutate", "write", GLOBAL_SSID, "'All_Workloads_Follow_up'!E3", "🟧 High (15-30d)"], capture_output=True, text=True)

# 2. Batch format request
batch_req = {
    "requests": [
        # Reset A3:C3 (Alert Criteria label & description) to clean neutral style
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                        "horizontalAlignment": "RIGHT"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Cell D3: Critical (<=14d) - Soft Rose / Red #FCE8E6
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.77, "green": 0.13, "blue": 0.12}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Cell E3: High (15-30d) - True Soft Orange #FFE0B2 (Material Orange 100)
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.698},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.745, "green": 0.212, "blue": 0.047}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Cell F3:G3: Medium (31-45d) - Crisp Soft Yellow #FFF9C4 (Material Yellow 100)
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.769},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.54, "green": 0.33, "blue": 0.0}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Cell H3:I3: Normal (>45d) - Subtle Grey #F1F3F4
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
    ]
}

# Add clean Conditional Formatting rules to sheet
# Delete existing conditional format rules and re-add them clearly
# Rule 0: Critical (<=14d) #FCE8E6
batch_req["requests"].append({
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": ROW_COUNT, "startColumnIndex": 0, "endColumnIndex": 20}],
            "booleanRule": {
                "condition": {
                    "type": "CUSTOM_FORMULA",
                    "values": [{"userEnteredValue": '=AND(OR(LEFT($G6,3)="0-2",LEFT($G6,2)="3:"), $Q6<>"", ($Q6-TODAY())<=14)'}]
                },
                "format": {
                    "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}
                }
            }
        },
        "index": 0
    }
})

# Rule 1: High (15-30d) #FFE0B2 (Distinct Orange)
batch_req["requests"].append({
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": ROW_COUNT, "startColumnIndex": 0, "endColumnIndex": 20}],
            "booleanRule": {
                "condition": {
                    "type": "CUSTOM_FORMULA",
                    "values": [{"userEnteredValue": '=AND(OR(LEFT($G6,3)="0-2",LEFT($G6,2)="3:"), $Q6<>"", ($Q6-TODAY())>=15, ($Q6-TODAY())<=30)'}]
                },
                "format": {
                    "backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.698}
                }
            }
        },
        "index": 1
    }
})

# Rule 2: Medium (31-45d) #FFF9C4 (Crisp Yellow)
batch_req["requests"].append({
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": ROW_COUNT, "startColumnIndex": 0, "endColumnIndex": 20}],
            "booleanRule": {
                "condition": {
                    "type": "CUSTOM_FORMULA",
                    "values": [{"userEnteredValue": '=AND(OR(LEFT($G6,3)="0-2",LEFT($G6,2)="3:"), $Q6<>"", ($Q6-TODAY())>=31, ($Q6-TODAY())<=45)'}]
                },
                "format": {
                    "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.769}
                }
            }
        },
        "index": 2
    }
})

tmp_json = "/tmp/test_global_orange.json"
with open(tmp_json, "w", encoding="utf-8") as f:
    json.dump(batch_req, f)

res = subprocess.run([GSHEETS, "mutate", "raw-batch-update", GLOBAL_SSID, tmp_json], capture_output=True, text=True)
if os.path.exists(tmp_json):
    os.remove(tmp_json)

if res.returncode == 0:
    print("✓ Successfully updated Global Master Dashboard with distinct Orange for High (15-30d) and Yellow for Medium (31-45d)!")
else:
    print(f"✗ Failed: {res.stderr}")
