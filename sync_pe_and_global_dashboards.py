import json
import csv
import subprocess
import os
import sys
import datetime
import re

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GDRIVE = "/google/bin/releases/gemini-agents-gdrive/gdrive"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

now = datetime.datetime.now()
DATE_FORMATTED = f"{now.day} - {now.strftime('%b')} {now.year}"

GLOBAL_FOLLOWUP_HEADERS = [
    "Partner Engineer (PE)",            # Col 0 (A)
    "Partner Name",                     # Col 1 (B)
    "Customer Account Name",            # Col 2 (C)
    "Account Tier",                     # Col 3 (D)
    "Workload Name",                    # Col 4 (E)
    "Workload Owner",                   # Col 5 (F)
    "Workload Progress",                # Col 6 (G)
    "Capacity Status (DRP Readiness)",  # Col 7 (H)
    "Opportunity Name",                 # Col 8 (I)
    "Expert Requests",                  # Col 9 (J)
    "Customer Sub Region",              # Col 10 (K)
    "Customer Micro Region",            # Col 11 (L)
    "Primary Workload Pillar",          # Col 12 (M)
    "Sales Play",                       # Col 13 (N)
    "Workload Solution",                # Col 14 (O)
    "Begin Migration Date",             # Col 15 (P)
    "Production Date",                  # Col 16 (Q)
    "Annual Gross Revenue (ARR USD)",   # Col 17 (R)
    "Last Touch",                       # Col 18 (S)
    "Link"                              # Col 19 (T)
]

GLOBAL_COL_WIDTHS = {
    0: 160,  # Partner Engineer (PE)
    1: 250,  # Partner Name
    2: 280,  # Customer Account Name
    3: 90,   # Account Tier
    4: 240,  # Workload Name
    5: 180,  # Workload Owner
    6: 170,  # Workload Progress
    7: 200,  # Capacity Status
    8: 260,  # Opportunity Name
    9: 180,  # Expert Requests
    10: 120, # Customer Sub Region
    11: 130, # Customer Micro Region
    12: 180, # Primary Workload Pillar
    13: 220, # Sales Play
    14: 220, # Workload Solution
    15: 130, # Begin Migration Date
    16: 130, # Production Date
    17: 150, # ARR USD
    18: 160, # Last Touch
    19: 160  # Link
}

GLOBAL_DRP_HEADERS = [
    "Partner Name",
    "Pillar",
    "Solution (Sales Play)",
    "Product",
    "Tier 1 Profiles Count",
    "Tier 2 Profiles Count",
    "Total Tier 1 & 2 Profiles",
    "Capacity Status (DRP vs Workloads)"
]

GLOBAL_ACCRED_HEADERS = [
    "Partner Name",
    "Certification / Accreditation Name",
    "Type",
    "Level / Sub Type",
    "Candidate Name",
    "Candidate Email",
    "Issued Date",
    "Expiration Date",
    "Partner Legal Entity"
]

def norm_str(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def extract_hyperlink_label(val):
    if not val:
        return ""
    val_str = str(val).strip()
    if '","' in val_str:
        try:
            return val_str.split('","')[1].rstrip('")').strip()
        except:
            pass
    if '", "' in val_str:
        try:
            return val_str.split('", "')[1].rstrip('")').strip()
        except:
            pass
    return val_str

def ensure_sheet_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
            # If only Sheet1 exists, rename it
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

def format_executive_summary(ssid, sid_exec, total_rows):
    if sid_exec is None:
        return
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_exec), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", str(sid_exec),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "9",
        "--bold",
        "--bg-color", "#1A73E8",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", str(sid_exec),
        "--start-row", str(total_rows - 1), "--end-row", str(total_rows),
        "--start-col", "0", "--end-col", "9",
        "--bold",
        "--bg-color", "#E8F0FE"
    ], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", str(sid_exec),
        "--start-row", "1", "--end-row", str(total_rows),
        "--start-col", "4", "--end-col", "8",
        "--align", "CENTER"
    ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_exec), "--start-col", "0", "--end-col", "9"], capture_output=True)

def format_all_workloads_followup(ssid, sid_gwkl, total_rows, all_followup_rows, title_label):
    grid_info = get_grid_info(ssid)
    gw_info = grid_info.get("All_Workloads_Follow_up", {"sheetId": sid_gwkl, "rowCount": total_rows, "columnCount": 20})
    sid = gw_info["sheetId"]
    gw_rows = max(total_rows, gw_info["rowCount"])
    has_data = total_rows > 5
    
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid), "--rows", "5"], capture_output=True)
    
    batch_req = {
      "requests": [
        # Reset top & table area
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"unmergeCells": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": min(10, gw_rows), "startColumnIndex": 0, "endColumnIndex": 20}}},
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 5}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        
        # Row 1 (Top Partner & Date)
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 3 (Alert Criteria in Light Purple)
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.953, "green": 0.910, "blue": 0.992}, "textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.408, "green": 0.114, "blue": 0.659}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.40, "green": 0.05, "blue": 0.05}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.15, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.45, "green": 0.30, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 5 (Main Header)
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 18, "endColumnIndex": 20}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

        # Borders
        {
          "updateBorders": {
            "range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20},
            "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
            "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
          }
        },
        # Basic Filter
        {"clearBasicFilter": {"sheetId": sid}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}}}},

        # Row heights
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}}
      ]
    }

    if has_data:
        batch_req["requests"].extend([
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 4, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 8, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            # Centered: Tier (Col 3), Capacity (Col 7), Dates (Cols 15-16)
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 15, "endColumnIndex": 17}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            # ARR Currency (Col 17)
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 17, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
            # Manual Note Columns (Cols 18-19)
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 18, "endColumnIndex": 20}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},

            # Hyperlinks (Cols 1, 2, 4, 8)
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 1, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 8, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

            # Conditional Formatting Rules (Progress is Col G [$G6], Production Date is Col Q [$Q6])
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($G6,3)=\"0-2\",LEFT($G6,2)=\"3:\"), $Q6<>\"\", ($Q6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.949, "green": 0.545, "blue": 0.510}}}}, "index": 0}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($G6,3)=\"0-2\",LEFT($G6,2)=\"3:\"), $Q6<>\"\", ($Q6-TODAY())>=15, ($Q6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.718, "blue": 0.302}}}}, "index": 1}},
            {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": 5, "endRowIndex": gw_rows, "startColumnIndex": 0, "endColumnIndex": 20}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($G6,3)=\"0-2\",LEFT($G6,2)=\"3:\"), $Q6<>\"\", ($Q6-TODAY())>=31, ($Q6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.961, "blue": 0.616}}}}, "index": 2}},

            {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 5, "endIndex": gw_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
        ])

        # Zebra striping
        for r_idx in range(5, gw_rows):
            if r_idx % 2 == 1:
                batch_req["requests"].append({
                    "repeatCell": {
                        "range": {"sheetId": sid, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 18},
                        "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                        "fields": "userEnteredFormat(backgroundColor)"
                    }
                })

        # ER links
        for r_idx in range(5, gw_rows):
            if r_idx < len(all_followup_rows):
                val = all_followup_rows[r_idx][9]
                if "ER-" in val and ("HYPERLINK" in val or "http" in val):
                    batch_req["requests"].append({
                        "repeatCell": {
                            "range": {"sheetId": sid, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 9, "endColumnIndex": 10},
                            "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}},
                            "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
                        }
                    })

    # Column widths
    for col_idx, width in GLOBAL_COL_WIDTHS.items():
        batch_req["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    tmp_batch = f"temp_batch_{ssid}.json"
    with open(tmp_batch, "w") as f:
        json.dump(batch_req, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_batch], capture_output=True)
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)

def format_all_drp_status(ssid, sid_drp, total_rows):
    if sid_drp is None:
        return
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_drp), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", str(sid_drp),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "8",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    if total_rows > 1:
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sid_drp),
            "--start-row", "1", "--end-row", str(total_rows),
            "--start-col", "4", "--end-col", "8",
            "--align", "CENTER"
        ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_drp), "--start-col", "0", "--end-col", "8"], capture_output=True)

def format_all_accreditaciones(ssid, sid_accred, total_rows):
    if sid_accred is None:
        return
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_accred), "--rows", "1"], capture_output=True)
    subprocess.run([
        GSHEETS, "mutate", "format", ssid,
        "--sheet-id", str(sid_accred),
        "--start-row", "0", "--end-row", "1",
        "--start-col", "0", "--end-col", "9",
        "--bold",
        "--bg-color", "#E8F0FE",
        "--align", "CENTER",
        "--wrap"
    ], capture_output=True)
    if total_rows > 1:
        subprocess.run([
            GSHEETS, "mutate", "format", ssid,
            "--sheet-id", str(sid_accred),
            "--start-row", "1", "--end-row", str(total_rows),
            "--start-col", "6", "--end-col", "8",
            "--align", "CENTER"
        ], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "autosize", ssid, "--sheet-id", str(sid_accred), "--start-col", "0", "--end-col", "9"], capture_output=True)

# =========================================================================
# 1. LOAD DATASETS & MANUAL ENTRIES
# =========================================================================
print("\n--- 1. Loading datasets & manual entries ---")
with open("partner_manual_entries.json") as f:
    partner_manual = json.load(f)

# Build normalized lookup map:
manual_lookup = {}
for p, wkls in partner_manual.items():
    np = norm_str(p)
    np_short = re.sub(r"\([^)]*\)", "", p).strip()
    np_short_norm = norm_str(np_short)
    for w, entry in wkls.items():
        nw = norm_str(w)
        manual_lookup.setdefault(np, {})[nw] = entry
        if np_short_norm != np:
            manual_lookup.setdefault(np_short_norm, {})[nw] = entry

with open("pe_dashboards.json") as f:
    pe_dashboards = json.load(f)

with open("created_trackers.json") as f:
    trackers = json.load(f)

# Load global executive summary
with open("global_dashboard_data/executive_summary_latest.csv") as f:
    exec_rows = list(csv.reader(f))
exec_headers = exec_rows[0]
exec_data_rows = [r for r in exec_rows[1:] if not r[0].startswith("TOTAL")]

# Load global workloads followup
with open("global_dashboard_data/all_workloads_followup_latest.csv") as f:
    wkl_rows = list(csv.reader(f))
wkl_data_rows = wkl_rows[5:]

# Load global DRP status
with open("global_dashboard_data/all_drp_status_latest.csv") as f:
    drp_rows = list(csv.reader(f))
drp_headers = drp_rows[0]
drp_data_rows = drp_rows[1:]

# Load global accreditations
with open("global_dashboard_data/all_accreditations_latest.csv") as f:
    accred_rows = list(csv.reader(f))
accred_headers = accred_rows[0]
accred_data_rows = accred_rows[1:]

# Sync manual entries into global workloads
print("\n--- 2. Applying One-Way Sync of Last Touch & Link to Global Workloads ---")
synced_global_count = 0
for r in wkl_data_rows:
    p_name = extract_hyperlink_label(r[1])
    w_name = extract_hyperlink_label(r[4])
    np = norm_str(p_name)
    nw = norm_str(w_name)
    
    if np in manual_lookup and nw in manual_lookup[np]:
        entry = manual_lookup[np][nw]
        r[18] = entry.get("last_touch", "")
        r[19] = entry.get("link", "")
        synced_global_count += 1
    else:
        r[18] = ""
        r[19] = ""

print(f"Total workload rows updated with partner notes: {synced_global_count} (out of {len(wkl_data_rows)} rows)")

# Re-write global followup CSV
global_top_block = [
    ["Partner:", f"All {len(trackers)} Partners (Global Management Dashboard)", "", "", "", "Last Update:", DATE_FORMATTED] + [""] * 13,
    [""] * 20,
    ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)"] + [""] * 12,
    [""] * 20,
    GLOBAL_FOLLOWUP_HEADERS
]
all_global_followup_rows = global_top_block + wkl_data_rows
global_followup_csv = "global_dashboard_data/all_workloads_followup_latest.csv"
with open(global_followup_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(all_global_followup_rows)

print("\n--- 3. Refreshing Global Master Dashboard ---")
sid_gwkl = ensure_sheet_tab(GLOBAL_SSID, "All_Workloads_Follow_up")
subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Workloads_Follow_up'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Workloads_Follow_up'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, global_followup_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True)
format_all_workloads_followup(GLOBAL_SSID, sid_gwkl, len(all_global_followup_rows), all_global_followup_rows, "Global Management Dashboard")
print("✓ Global Master Dashboard updated with clean one-way synced notes.")

# =========================================================================
# 4. BUILD & POPULATE EACH PE DASHBOARD
# =========================================================================
print("\n--- 4. Building and Populating PE Dashboards ---")

for pe, d in pe_dashboards.items():
    pe_ssid = d["sheet_id"]
    print(f"\n========================================================")
    print(f"Processing PE: {pe}")
    print(f"Spreadsheet ID: {pe_ssid}")
    print(f"========================================================")
    
    # Determine partners belonging to this PE
    pe_partners = [t["partner"] for t in trackers if pe in [p.strip() for p in t.get("pe", "").split(",")]]
    pe_norm_set = set(norm_str(p) for p in pe_partners)
    for p in pe_partners:
        pe_norm_set.add(norm_str(re.sub(r"\([^)]*\)", "", p).strip()))
        
    print(f"Assigned Partners ({len(pe_partners)}): {', '.join(pe_partners)}")
    
    # --- Tab 1: Executive_Summary ---
    print("-> Populating Executive_Summary...")
    pe_exec_data = [r for r in exec_data_rows if norm_str(extract_hyperlink_label(r[1])) in pe_norm_set]
    
    tot_wkl = 0
    tot_arr = 0.0
    tot_drp = 0
    tot_certs = 0
    for r in pe_exec_data:
        try:
            tot_wkl += int(r[4].replace(",", ""))
        except:
            pass
        try:
            tot_arr += float(r[5].replace("$", "").replace(",", ""))
        except:
            pass
        try:
            tot_drp += int(r[6].replace(",", ""))
        except:
            pass
        try:
            tot_certs += int(r[7].replace(",", ""))
        except:
            pass
            
    pe_total_row = [
        f"TOTAL (All {len(pe_partners)} Partners)",
        "-",
        "-",
        "-",
        str(tot_wkl),
        f"${tot_arr:,.2f}",
        str(tot_drp),
        str(tot_certs),
        "-"
    ]
    pe_exec_rows = [exec_headers] + pe_exec_data + [pe_total_row]
    
    pe_clean = pe.replace(" ", "_").replace("ñ", "n")
    pe_exec_csv = f"global_dashboard_data/exec_summary_{pe_clean}.csv"
    with open(pe_exec_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(pe_exec_rows)
        
    sid_exec = ensure_sheet_tab(pe_ssid, "Executive_Summary")
    subprocess.run([GSHEETS, "mutate", "clear", pe_ssid, "'Executive_Summary'!A1:Z500"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", pe_ssid, "--range", "'Executive_Summary'!2:500"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", pe_ssid, pe_exec_csv, "--sheet", "Executive_Summary"], capture_output=True)
    format_executive_summary(pe_ssid, sid_exec, len(pe_exec_rows))
    print(f"✓ Executive_Summary populated ({len(pe_exec_data)} partner rows).")
    
    # --- Tab 2: All_Workloads_Follow_up ---
    print("-> Populating All_Workloads_Follow_up...")
    pe_wkl_data = [r for r in wkl_data_rows if norm_str(extract_hyperlink_label(r[1])) in pe_norm_set]
    pe_top_block = [
        ["Partner:", f"{pe} Partners (Partner Management Dashboard)", "", "", "", "Last Update:", DATE_FORMATTED] + [""] * 13,
        [""] * 20,
        ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)"] + [""] * 12,
        [""] * 20,
        GLOBAL_FOLLOWUP_HEADERS
    ]
    all_pe_followup_rows = pe_top_block + pe_wkl_data
    pe_followup_csv = f"global_dashboard_data/all_workloads_followup_{pe_clean}.csv"
    with open(pe_followup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(all_pe_followup_rows)
        
    sid_wkl = ensure_sheet_tab(pe_ssid, "All_Workloads_Follow_up")
    subprocess.run([GSHEETS, "mutate", "clear", pe_ssid, "'All_Workloads_Follow_up'!A1:Z5000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", pe_ssid, "--range", "'All_Workloads_Follow_up'!2:5000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", pe_ssid, pe_followup_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True)
    format_all_workloads_followup(pe_ssid, sid_wkl, len(all_pe_followup_rows), all_pe_followup_rows, f"{pe} Dashboard")
    print(f"✓ All_Workloads_Follow_up populated ({len(pe_wkl_data)} workloads).")
    
    # --- Tab 3: All_DRP_Status ---
    print("-> Populating All_DRP_Status...")
    pe_drp_data = [r for r in drp_data_rows if norm_str(r[0]) in pe_norm_set]
    all_pe_drp_rows = [drp_headers] + pe_drp_data
    pe_drp_csv = f"global_dashboard_data/all_drp_status_{pe_clean}.csv"
    with open(pe_drp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(all_pe_drp_rows)
        
    sid_drp = ensure_sheet_tab(pe_ssid, "All_DRP_Status")
    subprocess.run([GSHEETS, "mutate", "clear", pe_ssid, "'All_DRP_Status'!A1:Z3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", pe_ssid, "--range", "'All_DRP_Status'!2:3000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", pe_ssid, pe_drp_csv, "--sheet", "All_DRP_Status"], capture_output=True)
    format_all_drp_status(pe_ssid, sid_drp, len(all_pe_drp_rows))
    print(f"✓ All_DRP_Status populated ({len(pe_drp_data)} rows).")
    
    # --- Tab 4: All_Acreditaciones ---
    print("-> Populating All_Acreditaciones...")
    pe_accred_data = [r for r in accred_data_rows if norm_str(r[0]) in pe_norm_set]
    all_pe_accred_rows = [accred_headers] + pe_accred_data
    pe_accred_csv = f"global_dashboard_data/all_accreditations_{pe_clean}.csv"
    with open(pe_accred_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(all_pe_accred_rows)
        
    sid_accred = ensure_sheet_tab(pe_ssid, "All_Acreditaciones")
    subprocess.run([GSHEETS, "mutate", "clear", pe_ssid, "'All_Acreditaciones'!A1:Z10000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", pe_ssid, "--range", "'All_Acreditaciones'!2:10000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", pe_ssid, pe_accred_csv, "--sheet", "All_Acreditaciones"], capture_output=True)
    format_all_accreditaciones(pe_ssid, sid_accred, len(all_pe_accred_rows))
    print(f"✓ All_Acreditaciones populated ({len(pe_accred_data)} rows).")
    
    # Cleanup default Sheet1 if present
    cleanup_default_sheets(pe_ssid)
    print(f"✓ Cleaned up default Sheet1 for {pe}.")

print("\n========================================================")
print("SUCCESS: ALL PE DASHBOARDS & GLOBAL DASHBOARD POPULATED & FORMATTED!")
print("========================================================")
