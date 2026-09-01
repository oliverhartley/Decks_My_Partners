import json
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

with open("created_trackers.json", "r", encoding="utf-8") as f:
    PARTNERS = json.load(f)

print(f"Starting rollout across all {len(PARTNERS)} partner action trackers...")

def update_partner_alert_styling(partner_info):
    pname = partner_info.get("partner") or partner_info.get("partner_name", "Partner")
    ssid = partner_info["sheet_id"]
    
    # 1. Fetch info
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        print(f"✗ Failed to get info for {pname} ({ssid}): {res.stderr}")
        return False
    
    try:
        data = json.loads(res.stdout)
    except Exception as e:
        print(f"✗ JSON decode error for {pname}: {e}")
        return False
        
    target_sheet = None
    for s in data.get("sheets", []):
        t = s.get("properties", {}).get("title")
        if t in ["Follow_up", "Sheet1"]:
            target_sheet = s
            break
    if target_sheet is None and data.get("sheets"):
        target_sheet = data["sheets"][0]
        
    sid = target_sheet.get("properties", {}).get("sheetId", 0)
    title = target_sheet.get("properties", {}).get("title", "")
    row_count = target_sheet.get("properties", {}).get("gridProperties", {}).get("rowCount", 1000)
    num_existing_rules = len(target_sheet.get("conditionalFormats", []))
    
    # 2. Update E3 cell text
    subprocess.run([GSHEETS, "mutate", "write", ssid, f"'{title}'!E3", "🟧 High (15-30d)"], capture_output=True, text=True)
    
    # 3. Build Batch Request
    requests = []
    
    # A. Delete all existing conditional format rules in reverse index
    for i in reversed(range(num_existing_rules)):
        requests.append({
            "deleteConditionalFormatRule": {
                "sheetId": sid,
                "index": i
            }
        })
        
    # B. Reset A3:C3 to clean transparent/white background
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                    "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                    "horizontalAlignment": "RIGHT"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                    "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                    "horizontalAlignment": "LEFT"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    
    # C. Cell D3: Critical (<=14d) - DARKER CORAL RED (#F28B82)
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510},
                    "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    
    # D. Cell E3: High (15-30d) - TRUE ORANGE (#FFB74D)
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302},
                    "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    
    # E. Cell F3:G3: Medium (31-45d) - CRISP YELLOW (#FFF59D)
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616},
                    "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    
    # F. Cell H3:I3: Normal (>45d) - Grey (#F1F3F4)
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957},
                    "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    
    # G. Add 3 Fresh Conditional Formatting Rules (Progress is Col E [$E6], Production Date is Col O [$O6])
    # Rule 0: Critical (<=14d) - Coral Red (#F28B82)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": 18}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": '=AND(OR(LEFT($E6,3)="0-2",LEFT($E6,2)="3:"), $O6<>"", ($O6-TODAY())<=14)'}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}
                    }
                }
            },
            "index": 0
        }
    })
    
    # Rule 1: High (15-30d) - True Orange (#FFB74D)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": 18}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": '=AND(OR(LEFT($E6,3)="0-2",LEFT($E6,2)="3:"), $O6<>"", ($O6-TODAY())>=15, ($O6-TODAY())<=30)'}]
                    },
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}
                    }
                }
            },
            "index": 1
        }
    })
    
    # Rule 2: Medium (31-45d) - Crisp Yellow (#FFF59D)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": 18}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": '=AND(OR(LEFT($E6,3)="0-2",LEFT($E6,2)="3:"), $O6<>"", ($O6-TODAY())>=31, ($O6-TODAY())<=45)'}]
                    },
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}
                    }
                }
            },
            "index": 2
        }
    })
    
    # Execute batch request
    tmp_file = f"/tmp/rollout_{sid}.json"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump({"requests": requests}, f)
        
    res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_file], capture_output=True, text=True)
    if os.path.exists(tmp_file):
        os.remove(tmp_file)
        
    if res_batch.returncode == 0:
        print(f"✓ Successfully updated alert colors for {pname} (Cleared {num_existing_rules} old rules -> 3 fresh rules)")
        return True
    else:
        print(f"✗ Error updating {pname} ({ssid}): {res_batch.stderr}")
        return False

# Run rollout across all 31 partners
success_count = 0
for idx, p in enumerate(PARTNERS, 1):
    partner_title = p.get("partner") or p.get("partner_name", "Partner")
    print(f"[{idx}/{len(PARTNERS)}] Processing {partner_title}...")
    if update_partner_alert_styling(p):
        success_count += 1

print(f"\n========================================================")
print(f"SUCCESS: {success_count}/{len(PARTNERS)} PARTNER TRACKERS UPDATED WITH NEW ALERT PALETTE!")
print(f"========================================================")
