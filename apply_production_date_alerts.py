import json
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

PARTNERS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q",
        "tab_name": "Follow_up"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "tab_name": "Follow_up"
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "tab_name": "Follow_up"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "tab_name": "Follow_up"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "tab_name": "Follow_up"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "tab_name": "Follow_up"
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "tab_name": "Follow_up"
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "sheet_id": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew",
        "tab_name": "Follow_up"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "tab_name": "Follow_up"
    },
    {
        "partner": "Global Partner Management Dashboard",
        "sheet_id": GLOBAL_SSID,
        "tab_name": "All_Workloads_Follow_up"
    }
]

def apply_alerts_to_sheet(ssid, tab_title):
    print(f"\nProcessing alerts for {ssid} ({tab_title})...")
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error fetching info for {ssid}: {res.stderr}")
        return
    
    data = json.loads(res.stdout)
    target_sheet = None
    for s in data.get("sheets", []):
        if s.get("properties", {}).get("title") == tab_title:
            target_sheet = s
            break
            
    if not target_sheet:
        print(f"Tab {tab_title} not found in {ssid}")
        return
        
    sid = target_sheet["properties"].get("sheetId", 0)
    num_rows = target_sheet["properties"]["gridProperties"].get("rowCount", 2000)
    existing_rules_count = len(target_sheet.get("conditionalFormats", []))
    print(f"Found sheetId: {sid}, total rows: {num_rows}, existing conditional rules: {existing_rules_count}")
    
    requests = []
    # Delete old rules if any
    for _ in range(existing_rules_count):
        requests.append({
            "deleteConditionalFormatRule": {
                "sheetId": sid,
                "index": 0
            }
        })
        
    # Column O is index 14 (0-based)
    # 1. RED (0 to 14 days / <= 14 days)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sid,
                    "startRowIndex": 1,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 14,
                    "endColumnIndex": 15
                }],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), $O2<>\"\", ($O2-TODAY())<=14)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.918, "green": 0.263, "blue": 0.208}, # #EA4335
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                        }
                    }
                }
            },
            "index": 0
        }
    })
    
    # 2. LIGHT RED (15 to 30 days)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sid,
                    "startRowIndex": 1,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 14,
                    "endColumnIndex": 15
                }],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), $O2<>\"\", ($O2-TODAY())>=15, ($O2-TODAY())<=30)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902} # #FCE8E6
                    }
                }
            },
            "index": 1
        }
    })
    
    # 3. LIGHT YELLOW (31 to 45 days)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sid,
                    "startRowIndex": 1,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 14,
                    "endColumnIndex": 15
                }],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), $O2<>\"\", ($O2-TODAY())>=31, ($O2-TODAY())<=45)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.949, "blue": 0.800} # #FFF2CC
                    }
                }
            },
            "index": 2
        }
    })
    
    req_body = {"requests": requests}
    tmp_file = f"temp_alert_req_{sid}.json"
    with open(tmp_file, "w") as f:
        json.dump(req_body, f)
        
    res_b = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_file], capture_output=True, text=True)
    if res_b.returncode == 0:
        print(f"✓ Successfully applied 3 alert rules to {tab_title} in {ssid}")
    else:
        print(f"✗ Failed raw-batch for {ssid}: {res_b.stderr}")
    
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

for p in PARTNERS:
    apply_alerts_to_sheet(p["sheet_id"], p["tab_name"])

print("\n==========================================")
print("ALL SHEETS CONFIGURED WITH PRODUCTION DATE CONDITIONAL FORMATTING ALERTS!")
print("==========================================")
