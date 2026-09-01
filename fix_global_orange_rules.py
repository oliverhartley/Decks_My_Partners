import json
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"
SID = 713943462  # All_Workloads_Follow_up

# 1. Fetch current info to count rules
res = subprocess.run([GSHEETS, "readonly", "info", GLOBAL_SSID, "--json"], capture_output=True, text=True)
data = json.loads(res.stdout)
num_rules = 0
row_count = 1000
for s in data.get("sheets", []):
    if s.get("properties", {}).get("sheetId") == SID:
        num_rules = len(s.get("conditionalFormats", []))
        row_count = s.get("properties", {}).get("gridProperties", {}).get("rowCount", 1000)

print(f"Deleting {num_rules} old conditional formatting rules...")

delete_requests = []
# Delete all rules from index 0 repeatedly or reverse index
for _ in range(num_rules):
    delete_requests.append({
        "deleteConditionalFormatRule": {
            "sheetId": SID,
            "index": 0
        }
    })

if delete_requests:
    tmp_del = "/tmp/delete_rules.json"
    with open(tmp_del, "w", encoding="utf-8") as f:
        json.dump({"requests": delete_requests}, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch-update", GLOBAL_SSID, tmp_del], capture_output=True)
    if os.path.exists(tmp_del):
        os.remove(tmp_del)

# 2. Update E3 cell text
subprocess.run([GSHEETS, "mutate", "write", GLOBAL_SSID, "'All_Workloads_Follow_up'!E3", "🟧 High (15-30d)"], capture_output=True, text=True)

# 3. Add vibrant distinct Orange and Yellow formatting + 3 clean conditional formatting rules
# True Orange: #FFB74D (RGB: 255, 183, 77 -> red: 1.0, green: 0.718, blue: 0.302)
# Crisp Yellow: #FFF59D (RGB: 255, 245, 157 -> red: 1.0, green: 0.961, blue: 0.616)
# Soft Red: #FCE8E6 (RGB: 252, 232, 230 -> red: 0.988, green: 0.910, blue: 0.902)

batch_req = {
    "requests": [
        # Cell D3: Critical (<=14d)
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
        # Cell E3: High (15-30d) - TRUE ORANGE (#FFB74D)
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.55, "green": 0.15, "blue": 0.0}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Cell F3:G3: Medium (31-45d) - CRISP YELLOW (#FFF59D)
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Cell H3:I3: Normal (>45d) - Grey
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
        },
        # Rule 0: Critical (<=14d) - Soft Red (#FCE8E6)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": 20}],
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
        },
        # Rule 1: High (15-30d) - TRUE ORANGE (#FFB74D)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": 20}],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": '=AND(OR(LEFT($G6,3)="0-2",LEFT($G6,2)="3:"), $Q6<>"", ($Q6-TODAY())>=15, ($Q6-TODAY())<=30)'}]
                        },
                        "format": {
                            "backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}
                        }
                    }
                },
                "index": 1
            }
        },
        # Rule 2: Medium (31-45d) - CRISP YELLOW (#FFF59D)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": 20}],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": '=AND(OR(LEFT($G6,3)="0-2",LEFT($G6,2)="3:"), $Q6<>"", ($Q6-TODAY())>=31, ($Q6-TODAY())<=45)'}]
                        },
                        "format": {
                            "backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}
                        }
                    }
                },
                "index": 2
            }
        }
    ]
}

tmp_add = "/tmp/add_orange_rules.json"
with open(tmp_add, "w", encoding="utf-8") as f:
    json.dump(batch_req, f)

res2 = subprocess.run([GSHEETS, "mutate", "raw-batch-update", GLOBAL_SSID, tmp_add], capture_output=True, text=True)
if os.path.exists(tmp_add):
    os.remove(tmp_add)

if res2.returncode == 0:
    print("✓ Successfully cleaned old rules and applied TRUE ORANGE #FFB74D to E3 and High alert rows!")
else:
    print(f"✗ Failed: {res2.stderr}")
