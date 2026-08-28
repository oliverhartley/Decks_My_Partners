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
    print(f"Updating High (Orange) & Normal (Transparent) styling for: {sname} ({tab})...")
    
    # Formula variables
    # Partner: $L6 is Progress, $N6 is Prod Date. Global: $M6 is Progress, $O6 is Prod Date.
    stage_col = "$M6" if is_global else "$L6"
    date_col = "$O6" if is_global else "$N6"
    num_cols = 18 if is_global else 17

    batch_req = {
      "requests": [
        # 1. Update Row 3 High Pill (Col 4, E3) -> Light Orange #FFE0B2, text #C05621
        {
          "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {
              "userEnteredFormat": {
                "backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.698}, # #FFE0B2
                "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.753, "green": 0.337, "blue": 0.129}}, # #C05621
                "horizontalAlignment": "CENTER"
              }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        # 2. Update Row 3 Normal Pill (Cols 7-9, H3:I3) -> Transparent/White #FFFFFF, text #5F6368
        {
          "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9},
            "cell": {
              "userEnteredFormat": {
                "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, # Transparent/White
                "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, # #5F6368
                "horizontalAlignment": "CENTER"
              }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        # 3. Update Conditional Format Rule 1 (High: 15-30 days) to Light Orange #FFE0B2
        {
          "updateConditionalFormatRule": {
            "rule": {
              "ranges": [{
                "sheetId": sheet_id,
                "startRowIndex": 5,
                "endRowIndex": row_count,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
              }],
              "booleanRule": {
                "condition": {
                  "type": "CUSTOM_FORMULA",
                  "values": [{"userEnteredValue": f"=AND(OR(LEFT({stage_col},3)=\"0-2\",LEFT({stage_col},2)=\"3:\"), {date_col}<>\"\", ({date_col}-TODAY())>=15, ({date_col}-TODAY())<=30)"}]
                },
                "format": {
                  "backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.698} # #FFE0B2 Light Orange
                }
              }
            },
            "index": 1
          }
        }
      ]
    }

    tmp_file = f"temp_orange_{sheet_id}.json"
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
print("ALL SPREADSHEETS UPDATED WITH LIGHT ORANGE HIGH ALERT & TRANSPARENT NORMAL STATUS!")
print("==========================================")
