import json
import csv
import subprocess
import os
import sys
import re
import datetime

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GDRIVE = "/google/bin/releases/gemini-agents-gdrive/gdrive"
OLIVER_FOLDER_ID = "1WG2zMHJXRU8HnSCVR2cTN_5KeAUm5kQ3"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"
OLIVER_DASHBOARD_SSID = "1VkmmtXJopJ57K_XL3jwdqk8LrN6qw0_iGrBbl5deYpI"

now = datetime.datetime.now()
DATE_FORMATTED = f"{now.day} - {now.strftime('%b')} {now.year}"

PARTNER_COL_WIDTHS = {
    0: 280,  # Customer Account Name
    1: 90,   # Account Tier
    2: 240,  # Workload Name
    3: 180,  # Workload Owner
    4: 170,  # Workload Progress
    5: 200,  # Capacity Status
    6: 260,  # Opportunity Name
    7: 180,  # Expert Requests
    8: 120,  # Customer Sub Region
    9: 130,  # Customer Micro Region
    10: 180, # Primary Workload Pillar
    11: 220, # Sales Play
    12: 220, # Workload Solution
    13: 130, # Begin Migration Date
    14: 130, # Production Date
    15: 150, # Annual Gross Revenue
    16: 160, # Last Touch
    17: 160  # Link
}

OLIVER_PARTNERS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "followup_csv": "followup_data_latest/Comercializadora_Zenta_Group_SPA_followup.csv",
        "drp_csv": "drp_data_latest/Comercializadora_Zenta_Group_SPA_drp.csv",
        "accred_csv": "accred_data_latest/Comercializadora_Zenta_Group_SPA_accred.csv"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "followup_csv": "followup_data_latest/Consiti__Consultoría_y_Soluciones_Informáticas__followup.csv",
        "drp_csv": "drp_data_latest/Consiti__Consultoría_y_Soluciones_Informáticas__drp.csv",
        "accred_csv": "accred_data_latest/Consiti__Consultoría_y_Soluciones_Informáticas__accred.csv"
    },
    {
        "partner": "Devaid SPA",
        "followup_csv": "followup_data_latest/Devaid_SPA_followup.csv",
        "drp_csv": "drp_data_latest/Devaid_SPA_drp.csv",
        "accred_csv": "accred_data_latest/Devaid_SPA_accred.csv"
    },
    {
        "partner": "MadeinWeb S/A",
        "followup_csv": "followup_data_latest/MadeinWeb_S_A_followup.csv",
        "drp_csv": "drp_data_latest/MadeinWeb_S_A_drp.csv",
        "accred_csv": "accred_data_latest/MadeinWeb_S_A_accred.csv"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "followup_csv": "followup_data_latest/Tech_Pulse_SPA__Axmos__followup.csv",
        "drp_csv": "drp_data_latest/Tech_Pulse_SPA__Axmos__drp.csv",
        "accred_csv": "accred_data_latest/Tech_Pulse_SPA__Axmos__accred.csv"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "followup_csv": "followup_data_latest/TIVIT_COLOMBIA_S_A_S_followup.csv",
        "drp_csv": "drp_data_latest/TIVIT_COLOMBIA_S_A_S_drp.csv",
        "accred_csv": "accred_data_latest/TIVIT_COLOMBIA_S_A_S_accred.csv"
    }
]

def ensure_sheet_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
            if len(sheets) == 1 and sheets[0].get("title") in ["Sheet1", "Hoja 1"]:
                subprocess.run([GSHEETS, "mutate", "rename-sheet", ssid, "--sheet-id", str(sheets[0]["id"]), "--title", tab_title], capture_output=True)
                return sheets[0]["id"]
        except Exception as e:
            print(f"Error checking sheets for {ssid}: {e}")
            
    subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    res2 = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            sheets = json.loads(res2.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    return None

def get_grid_info(ssid):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    try:
        data = json.loads(res.stdout)
        grid_info = {}
        for s in data.get("sheets", []):
            props = s.get("properties", {})
            grid_info[props.get("title")] = {
                "sheetId": props.get("sheetId", 0),
                "rowCount": props.get("gridProperties", {}).get("rowCount", 1000),
                "columnCount": props.get("gridProperties", {}).get("columnCount", 26)
            }
        return grid_info
    except:
        return {}

def cleanup_default_sheets(ssid):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            if len(sheets) > 1:
                for s in sheets:
                    if s.get("title") in ["Sheet1", "Hoja 1"]:
                        subprocess.run([GSHEETS, "mutate", "delete-sheet", ssid, "--sheet-id", str(s["id"])], capture_output=True)
        except:
            pass

new_trackers_map = {}

for pcfg in OLIVER_PARTNERS:
    pname = pcfg["partner"]
    followup_csv = pcfg["followup_csv"]
    drp_csv = pcfg["drp_csv"]
    accred_csv = pcfg["accred_csv"]
    
    print(f"\n========================================================")
    print(f"Creating Action Tracker for: {pname}")
    print(f"========================================================")
    
    # 1. Create spreadsheet
    res = subprocess.check_output([GSHEETS, "mutate", "create", "--title", pname]).decode("utf-8")
    match = re.search(r"ID:\s*([a-zA-Z0-9_\-]+)", res)
    if not match:
        raise RuntimeError(f"Could not parse sheet ID from {res}")
    ssid = match.group(1)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{ssid}/edit"
    print(f"Created: {ssid} ({sheet_url})")
    
    # 2. Move to Oliver's folder
    print(f"Moving to Oliver Hartley folder ({OLIVER_FOLDER_ID})...")
    subprocess.check_call([GDRIVE, "mutate", "mv", ssid, OLIVER_FOLDER_ID])
    print("Moved successfully.")
    
    new_trackers_map[pname] = ssid
    
    # 3. Tab 1: Follow_up
    print("Populating Follow_up...")
    sid_followup = ensure_sheet_tab(ssid, "Follow_up")
    with open(followup_csv) as f:
        followup_rows = list(csv.reader(f))
    f_total_rows = len(followup_rows)
    has_data = f_total_rows > 5
    
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Follow_up'!2:2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, followup_csv, "--sheet", "Follow_up"], capture_output=True)
    
    grid_info = get_grid_info(ssid)
    f_info = grid_info.get("Follow_up", {"sheetId": sid_followup, "rowCount": f_total_rows, "columnCount": 18})
    sid_followup = f_info["sheetId"]
    f_rows = max(f_total_rows, f_info["rowCount"])
    
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_followup), "--rows", "5"], capture_output=True)
    
    batch_req = {
      "requests": [
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"unmergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": min(10, f_rows), "startColumnIndex": 0, "endColumnIndex": 18}}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        
        # Row 1
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 3 (Alert Criteria)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 5 (Main Header: Cols 0-15 Blue, Cols 16-17 Green)
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 16, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        
        # Borders
        {"updateBorders": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
        {"clearBasicFilter": {"sheetId": sid_followup}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}}}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}}
      ]
    }
    
    if has_data:
        batch_req["requests"].extend([
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 13}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 1, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 13, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 15, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 16, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}}}}, "index": 0}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())>=15, ($O6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}}}}, "index": 1}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($E6,3)=\"0-2\",LEFT($E6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())>=31, ($O6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}}}}, "index": 2}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 5, "endIndex": f_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
        ])
        for r_idx in range(5, f_rows):
            if r_idx % 2 == 1:
                batch_req["requests"].append({"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})
        for r_idx in range(5, f_rows):
            if r_idx < len(followup_rows):
                val = followup_rows[r_idx][7]
                if "ER-" in val and ("HYPERLINK" in val or "http" in val):
                    batch_req["requests"].append({"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}})

    for col_idx, width in PARTNER_COL_WIDTHS.items():
        batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})

    tmp_batch = f"temp_batch_{ssid}.json"
    with open(tmp_batch, "w") as f:
        json.dump(batch_req, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_batch], capture_output=True)
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)
    print("✓ Follow_up tab formatted.")
    
    # 4. Tab 2: DRP_Status
    print("Populating DRP_Status...")
    sid_drp = ensure_sheet_tab(ssid, "DRP_Status")
    with open(drp_csv) as f:
        drp_rows = list(csv.reader(f))
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'DRP_Status'!A1:Z1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'DRP_Status'!2:1000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, drp_csv, "--sheet", "DRP_Status"], capture_output=True)
    if sid_drp is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_drp), "--rows", "1"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "format", ssid, "--sheet-id", str(sid_drp), "--start-row", "0", "--end-row", "1", "--start-col", "0", "--end-col", "7", "--bold", "--bg-color", "#E8F0FE", "--align", "CENTER", "--wrap"], capture_output=True)
        if len(drp_rows) > 1:
            subprocess.run([GSHEETS, "mutate", "format", ssid, "--sheet-id", str(sid_drp), "--start-row", "1", "--end-row", str(len(drp_rows)), "--start-col", "3", "--end-col", "7", "--align", "CENTER"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_drp), "--start-col", "0", "--end-col", "7"], capture_output=True)
    print("✓ DRP_Status tab populated.")
    
    # 5. Tab 3: Acreditaciones
    print("Populating Acreditaciones...")
    sid_accred = ensure_sheet_tab(ssid, "Acreditaciones")
    with open(accred_csv) as f:
        accred_rows = list(csv.reader(f))
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Acreditaciones'!A1:Z3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Acreditaciones'!2:3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, accred_csv, "--sheet", "Acreditaciones"], capture_output=True)
    if sid_accred is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_accred), "--rows", "1"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "format", ssid, "--sheet-id", str(sid_accred), "--start-row", "0", "--end-row", "1", "--start-col", "0", "--end-col", "8", "--bold", "--bg-color", "#E8F0FE", "--align", "CENTER", "--wrap"], capture_output=True)
        if len(accred_rows) > 1:
            subprocess.run([GSHEETS, "mutate", "format", ssid, "--sheet-id", str(sid_accred), "--start-row", "1", "--end-row", str(len(accred_rows)), "--start-col", "5", "--end-col", "7", "--align", "CENTER"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_accred), "--start-col", "0", "--end-col", "8"], capture_output=True)
    print("✓ Acreditaciones tab populated.")
    
    cleanup_default_sheets(ssid)
    print(f"✓ Completed recreation of tracker for {pname}.")

# Save new IDs to file
with open("oliver_new_trackers.json", "w") as f:
    json.dump(new_trackers_map, f, indent=2)

print("\nAll 6 trackers created successfully:")
for p, s in new_trackers_map.items():
    print(f"  - {p}: {s}")
