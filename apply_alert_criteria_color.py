import json
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
with open("created_trackers.json", "r", encoding="utf-8") as f:
    PARTNERS = json.load(f)

GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

def update_row3_color(ssid):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        print(f"Error fetching sheets for {ssid}")
        return
    sheets = json.loads(res.stdout)
    target_sid = None
    target_title = None
    for s in sheets:
        t = s.get("title")
        if t in ["Follow_up", "All_Workloads_Follow_up", "Sheet1"]:
            target_sid = s.get("id")
            target_title = t
            break
    if target_sid is None and sheets:
        target_sid = sheets[0].get("id")
        target_title = sheets[0].get("title")
        
    batch_req = {
        "requests": [
            {
                "repeatCell": {
                    "range": {"sheetId": target_sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992},
                            "textFormat": {
                                "bold": True,
                                "fontSize": 9,
                                "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}
                            },
                            "horizontalAlignment": "RIGHT"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": target_sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992},
                            "textFormat": {
                                "italic": True,
                                "fontSize": 9,
                                "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}
                            },
                            "horizontalAlignment": "LEFT"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            }
        ]
    }
    
    tmp_json = f"/tmp/row3_update_{target_sid}.json"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(batch_req, f)
        
    res_up = subprocess.run([GSHEETS, "mutate", "raw-batch-update", ssid, tmp_json], capture_output=True, text=True)
    if os.path.exists(tmp_json):
        os.remove(tmp_json)
    if res_up.returncode == 0:
        print(f"✓ Updated Alert Criteria color to light purple for {ssid} ({target_title})")
    else:
        print(f"✗ Failed for {ssid}: {res_up.stderr}")

print("Updating 31 Partner Action Trackers...")
for p in PARTNERS:
    update_row3_color(p["sheet_id"])

print("Updating Global Master Dashboard...")
update_row3_color(GLOBAL_SSID)
print("All complete!")
