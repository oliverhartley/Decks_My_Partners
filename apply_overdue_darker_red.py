import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

ALL_SPREADSHEETS = [
    # 9 Partners
    {"name": "Comercializadora Zenta Group SPA", "ssid": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q", "tab": "Follow_up", "is_global": False},
    {"name": "Tech Pulse SPA (Axmos)", "ssid": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI", "tab": "Follow_up", "is_global": False},
    {"name": "Devaid SPA", "ssid": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8", "tab": "Follow_up", "is_global": False},
    {"name": "UCLOUD STORE COLOMBIA S A S", "ssid": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI", "tab": "Follow_up", "is_global": False},
    {"name": "TIVIT COLOMBIA S A S", "ssid": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o", "tab": "Follow_up", "is_global": False},
    {"name": "VPN Soluçoes em TI LTDA (Venha para Nuvem)", "ssid": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo", "tab": "Follow_up", "is_global": False},
    {"name": "MadeinWeb S/A", "ssid": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI", "tab": "Follow_up", "is_global": False},
    {"name": "CU2 CLOUD TEC STORE SL", "ssid": "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew", "tab": "Follow_up", "is_global": False},
    {"name": "Consiti (Consultoría y Soluciones Informáticas)", "ssid": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo", "tab": "Follow_up", "is_global": False},
    # Global Master Dashboard
    {"name": "Global Partner Management Dashboard", "ssid": GLOBAL_SSID, "tab": "All_Workloads_Follow_up", "is_global": True}
]

def get_sheet_info(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return 0, 1000, 18
    data = json.loads(res.stdout)
    for s in data.get("sheets", []):
        props = s.get("properties", {})
        if props.get("title") == tab_title:
            return (
                props.get("sheetId", 0),
                props.get("gridProperties", {}).get("rowCount", 1000),
                props.get("gridProperties", {}).get("columnCount", 18)
            )
    return 0, 1000, 18

for item in ALL_SPREADSHEETS:
    sname = item["name"]
    ssid = item["ssid"]
    tab = item["tab"]
    is_global = item["is_global"]
    
    sheet_id, row_count, col_count = get_sheet_info(ssid, tab)
    print(f"Applying darker red for overdue workloads in: {sname} ({tab})...")
    
    stage_col = "$M6" if is_global else "$L6"
    date_col = "$O6" if is_global else "$N6"
    num_cols = 18 if is_global else 17

    # We first clear existing conditional formatting rules, then add the 4 ordered rules:
    # 1. Overdue (< 0 days): Darker red #F4C7C3
    # 2. Critical (0 to 14 days): Soft rose #FCE8E6
    # 3. High (15 to 30 days): Light orange #FFE0B2
    # 4. Medium (31 to 45 days): Soft yellow #FFF9DB
    
    # In Google Sheets API, to replace rules cleanly, we delete existing rules or overwrite them.
    # A standard way is delete conditionalFormatRule at indices or use booleanRules.
    # Let's inspect how many conditional format rules exist.
    # Alternatively, we can send a batch request that deletes rule 0 three times, then adds the 4 rules.
    # Or get the sheet's conditionalFormats count from info.
    res_info = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    c_count = 3
    if res_info.returncode == 0:
        d_info = json.loads(res_info.stdout)
        for s in d_info.get("sheets", []):
            if s.get("properties", {}).get("title") == tab:
                c_count = len(s.get("conditionalFormats", []))
                break

    batch_req = {"requests": []}
    for _ in range(c_count):
        batch_req["requests"].append({"deleteConditionalFormatRule": {"sheetId": sheet_id, "index": 0}})

    # Add Rule 0: Overdue (< 0 days) -> Darker Red #F4C7C3 (red: 0.957, green: 0.780, blue: 0.765)
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": num_cols}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": f"=AND(OR(LEFT({stage_col},3)=\"0-2\",LEFT({stage_col},2)=\"3:\"), {date_col}<>\"\", ({date_col}-TODAY())<0)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.957, "green": 0.780, "blue": 0.765} # Darker Red #F4C7C3
                    }
                }
            },
            "index": 0
        }
    })

    # Add Rule 1: Critical (0 to 14 days) -> Soft Rose #FCE8E6
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": num_cols}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": f"=AND(OR(LEFT({stage_col},3)=\"0-2\",LEFT({stage_col},2)=\"3:\"), {date_col}<>\"\", ({date_col}-TODAY())>=0, ({date_col}-TODAY())<=14)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902} # Soft Rose #FCE8E6
                    }
                }
            },
            "index": 1
        }
    })

    # Add Rule 2: High (15 to 30 days) -> Light Orange #FFE0B2
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": num_cols}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": f"=AND(OR(LEFT({stage_col},3)=\"0-2\",LEFT({stage_col},2)=\"3:\"), {date_col}<>\"\", ({date_col}-TODAY())>=15, ({date_col}-TODAY())<=30)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.698} # Light Orange #FFE0B2
                    }
                }
            },
            "index": 2
        }
    })

    # Add Rule 3: Medium (31 to 45 days) -> Soft Yellow #FFF9DB
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sheet_id, "startRowIndex": 5, "endRowIndex": row_count, "startColumnIndex": 0, "endColumnIndex": num_cols}],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": f"=AND(OR(LEFT({stage_col},3)=\"0-2\",LEFT({stage_col},2)=\"3:\"), {date_col}<>\"\", ({date_col}-TODAY())>=31, ({date_col}-TODAY())<=45)"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859} # Soft Yellow #FFF9DB
                    }
                }
            },
            "index": 3
        }
    })

    tmp_file = f"temp_darkred_{sheet_id}.json"
    with open(tmp_file, "w") as f:
        json.dump(batch_req, f, indent=2)

    res = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_file], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Succeeded for {sname}")
    else:
        print(f"✗ Failed for {sname}: {res.stderr}")
    
    import os
    if os.path.exists(tmp_file):
        os.remove(tmp_file)

print("\n==========================================")
print("ALL SPREADSHEETS UPDATED WITH DARKER RED FOR OVERDUE WORKLOADS!")
print("==========================================")
