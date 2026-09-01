import json
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"
SID = 713943462  # All_Workloads_Follow_up
ROW_COUNT = 797

# Fetch current info to delete existing 3 rules and re-add with darker red
res = subprocess.run([GSHEETS, "readonly", "info", GLOBAL_SSID, "--json"], capture_output=True, text=True)
data = json.loads(res.stdout)
num_rules = 0
for s in data.get("sheets", []):
    if s.get("properties", {}).get("sheetId") == SID:
        num_rules = len(s.get("conditionalFormats", []))

print(f"Deleting {num_rules} conditional formatting rules...")
delete_requests = [{"deleteConditionalFormatRule": {"sheetId": SID, "index": i}} for i in reversed(range(num_rules))]
if delete_requests:
    tmp_del = "/tmp/del_rules_red.json"
    with open(tmp_del, "w", encoding="utf-8") as f:
        json.dump({"requests": delete_requests}, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", GLOBAL_SSID, "-f", tmp_del], capture_output=True)
    if os.path.exists(tmp_del):
        os.remove(tmp_del)

# Darker Coral Red: #F28B82 (RGB: 242, 139, 130 -> red: 0.949, green: 0.545, blue: 0.510)
# True Orange: #FFB74D (RGB: 255, 183, 77 -> red: 1.0, green: 0.718, blue: 0.302)
# Crisp Yellow: #FFF59D (RGB: 255, 245, 157 -> red: 1.0, green: 0.961, blue: 0.616)

batch_req = {
    "requests": [
        # Cell D3: Critical (<=14d) - DARKER RED (#F28B82)
        {
            "repeatCell": {
                "range": {"sheetId": SID, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510},
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}},
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
                        "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}},
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
        # Rule 0: Critical (<=14d) - DARKER RED (#F28B82)
        {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": ROW_COUNT, "startColumnIndex": 0, "endColumnIndex": 20}],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": '=AND(OR(LEFT($G6,3)="0-2",LEFT($G6,2)="3:"), $Q6<>"", ($Q6-TODAY())<=14)'}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}
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
                    "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": ROW_COUNT, "startColumnIndex": 0, "endColumnIndex": 20}],
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
                    "ranges": [{"sheetId": SID, "startRowIndex": 5, "endRowIndex": ROW_COUNT, "startColumnIndex": 0, "endColumnIndex": 20}],
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

tmp_file = "/tmp/apply_darker_red.json"
with open(tmp_file, "w", encoding="utf-8") as f:
    json.dump(batch_req, f)

res = subprocess.run([GSHEETS, "mutate", "raw-batch", GLOBAL_SSID, "-f", tmp_file], capture_output=True, text=True)
if os.path.exists(tmp_file):
    os.remove(tmp_file)

if res.returncode == 0:
    print("✓ Successfully updated Global Master Dashboard with Darker Red #F28B82!")
else:
    print(f"✗ Failed: {res.stderr}")
