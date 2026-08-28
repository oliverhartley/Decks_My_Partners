import json
import csv
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"

GLOBAL_COL_WIDTHS = {
    0: 260,  # Partner Name
    1: 280,  # Customer Account Name
    2: 90,   # Account Tier
    3: 240,  # Workload Name
    4: 200,  # Capacity Status
    5: 260,  # Opportunity Name
    6: 180,  # Expert Requests
    7: 120,  # Customer Sub Region
    8: 130,  # Customer Micro Region
    9: 180,  # Primary Workload Pillar
    10: 220, # Sales Play
    11: 220, # Workload Solution
    12: 170, # Workload Progress
    13: 130, # Begin Migration Date
    14: 130, # Production Date
    15: 150, # ARR USD
    16: 160, # Last Touch
    17: 160  # Link
}

def get_grid_info(ssid):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    data = json.loads(res.stdout)
    grid_info = {}
    for s in data["sheets"]:
        props = s["properties"]
        grid_info[props["title"]] = {
            "sheetId": props["sheetId"],
            "rowCount": props["gridProperties"]["rowCount"],
            "columnCount": props["gridProperties"]["columnCount"]
        }
    return grid_info

# 1. All_Workloads_Follow_up Re-import
csv_file = "global_dashboard_data/all_workloads_followup_latest.csv"
rows = []
with open(csv_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for r in reader:
        rows.append(r)

header_row = [
    "Partner Name",
    "Customer Account Name",
    "Account Tier",
    "Workload Name",
    "Capacity Status (DRP Readiness)",
    "Opportunity Name",
    "Expert Requests",
    "Customer Sub Region",
    "Customer Micro Region",
    "Primary Workload Pillar",
    "Sales Play",
    "Workload Solution",
    "Workload Progress",
    "Begin Migration Date",
    "Production Date",
    "Annual Gross Revenue (ARR USD)",
    "Last Touch",
    "Link"
]
data_rows = rows[11:] if len(rows) > 11 else []

# Preserve manual notes if any
res_notes = subprocess.run([GSHEETS, "readonly", "read", GLOBAL_SSID, "'All_Workloads_Follow_up'!Q6:R2000", "--json"], capture_output=True, text=True)
if res_notes.returncode == 0 and res_notes.stdout.strip():
    try:
        existing_notes = json.loads(res_notes.stdout)
        for i, note_pair in enumerate(existing_notes):
            if i < len(data_rows):
                if len(note_pair) > 0 and note_pair[0] and not data_rows[i][16]:
                    data_rows[i][16] = note_pair[0]
                if len(note_pair) > 1 and note_pair[1] and not data_rows[i][17]:
                    data_rows[i][17] = note_pair[1]
    except:
        pass

new_rows = [
    ["Partner:", "All 9 Partners (Global Management Dashboard)", "", "", "Last Update:", "24 - Aug 2026", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)", "", "", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    header_row
]
new_rows.extend(data_rows)
num_total_rows = len(new_rows)

tmp_csv = "temp_global_wkl.csv"
with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(new_rows)

subprocess.run([GSHEETS, "mutate", "clear", GLOBAL_SSID, "'All_Workloads_Follow_up'!A1:Z5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "delete-rows", GLOBAL_SSID, "--range", "'All_Workloads_Follow_up'!2:5000"], capture_output=True)
subprocess.run([GSHEETS, "mutate", "import-csv", GLOBAL_SSID, tmp_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True)
if os.path.exists(tmp_csv):
    os.remove(tmp_csv)

grid_info = get_grid_info(GLOBAL_SSID)
w_info = grid_info.get("All_Workloads_Follow_up")
d_info = grid_info.get("All_DRP_Status")
a_info = grid_info.get("All_Acreditaciones")
e_info = grid_info.get("Executive_Summary")

SID_WKL = w_info["sheetId"]
w_rows = w_info["rowCount"]

batch_req = {
  "requests": [
    # ----------------------------------------------------
    # All_Workloads_Follow_up
    # ----------------------------------------------------
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
    {"unmergeCells": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": min(10, w_rows), "startColumnIndex": 0, "endColumnIndex": 18}}},
    {"mergeCells": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
    {"mergeCells": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
    
    # Row 1
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

    # Row 3
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.77, "green": 0.13, "blue": 0.12}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.69, "green": 0.38, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.49, "green": 0.29, "blue": 0.01}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

    # Row 5 Main Header
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 16, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

    # Data Rows Formatting
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 5, "endColumnIndex": 13}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 13, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 15, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 16, "endColumnIndex": 18}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},

    # Hyperlinks
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
    {"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

    # Borders
    {"updateBorders": {"range": {"sheetId": SID_WKL, "startRowIndex": 4, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 18}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
    {"clearBasicFilter": {"sheetId": SID_WKL}},
    {"setBasicFilter": {"filter": {"range": {"sheetId": SID_WKL, "startRowIndex": 4, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 18}}}},

    # Conditional formatting on Global ($M6 is Progress, $O6 is Prod Date)
    {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($M6,3)=\"0-2\",LEFT($M6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}}}}, "index": 0}},
    {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($M6,3)=\"0-2\",LEFT($M6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())>=15, ($O6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}}}}, "index": 1}},
    {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": SID_WKL, "startRowIndex": 5, "endRowIndex": w_rows, "startColumnIndex": 0, "endColumnIndex": 18}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($M6,3)=\"0-2\",LEFT($M6,2)=\"3:\"), $O6<>\"\", ($O6-TODAY())>=31, ($O6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}}}}, "index": 2}},

    # Row heights
    {"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
    {"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "ROWS", "startIndex": 5, "endIndex": w_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
  ]
}

# Zebra striping for Global Workloads
for r_idx in range(5, w_rows):
    if r_idx % 2 == 1:
        batch_req["requests"].append({"repeatCell": {"range": {"sheetId": SID_WKL, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})

# Column widths for Global Workloads
for col_idx, width in GLOBAL_COL_WIDTHS.items():
    batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": SID_WKL, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})

# Format ER links if any
for r_idx in range(5, w_rows):
    if r_idx < len(new_rows):
        val = new_rows[r_idx][6]
        if "ER-" in val and ("HYPERLINK" in val or "http" in val):
            batch_req["requests"].append({
                "repeatCell": {
                    "range": {"sheetId": SID_WKL, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 6, "endColumnIndex": 7},
                    "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}},
                    "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
                }
            })

# ----------------------------------------------------
# 2. All_DRP_Status
# ----------------------------------------------------
if d_info is not None:
    SID_DRP = d_info["sheetId"]
    d_rows = d_info["rowCount"]
    batch_req["requests"].extend([
        {"repeatCell": {"range": {"sheetId": SID_DRP, "startRowIndex": 0, "endRowIndex": d_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": SID_DRP, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": SID_DRP, "startRowIndex": 1, "endRowIndex": d_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat(textFormat)"}},
        {"repeatCell": {"range": {"sheetId": SID_DRP, "startRowIndex": 1, "endRowIndex": d_rows, "startColumnIndex": 4, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"updateBorders": {"range": {"sheetId": SID_DRP, "startRowIndex": 0, "endRowIndex": d_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
        {"updateDimensionProperties": {"range": {"sheetId": SID_DRP, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": SID_DRP, "dimension": "ROWS", "startIndex": 1, "endIndex": d_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}}
    ])
    for r in range(1, d_rows):
        if r % 2 == 1:
            batch_req["requests"].append({"repeatCell": {"range": {"sheetId": SID_DRP, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})
    gdrp_w = {0: 260, 1: 220, 2: 240, 3: 240, 4: 110, 5: 110, 6: 120, 7: 200}
    for c, w in gdrp_w.items():
        batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": SID_DRP, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})

# ----------------------------------------------------
# 3. All_Acreditaciones
# ----------------------------------------------------
if a_info is not None:
    SID_ACCRED = a_info["sheetId"]
    a_rows = a_info["rowCount"]
    batch_req["requests"].extend([
        {"repeatCell": {"range": {"sheetId": SID_ACCRED, "startRowIndex": 0, "endRowIndex": a_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": SID_ACCRED, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": SID_ACCRED, "startRowIndex": 1, "endRowIndex": a_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat(textFormat)"}},
        {"repeatCell": {"range": {"sheetId": SID_ACCRED, "startRowIndex": 1, "endRowIndex": a_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": SID_ACCRED, "startRowIndex": 1, "endRowIndex": a_rows, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"updateBorders": {"range": {"sheetId": SID_ACCRED, "startRowIndex": 0, "endRowIndex": a_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
        {"updateDimensionProperties": {"range": {"sheetId": SID_ACCRED, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": SID_ACCRED, "dimension": "ROWS", "startIndex": 1, "endIndex": a_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}}
    ])
    for r in range(1, a_rows):
        if r % 2 == 1:
            batch_req["requests"].append({"repeatCell": {"range": {"sheetId": SID_ACCRED, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})
    gacc_w = {0: 350, 1: 100, 2: 220, 3: 120, 4: 220, 5: 120, 6: 120, 7: 340}
    for c, w in gacc_w.items():
        batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": SID_ACCRED, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})

# ----------------------------------------------------
# 4. Executive_Summary
# ----------------------------------------------------
if e_info is not None:
    SID_EXEC = e_info["sheetId"]
    e_rows = e_info["rowCount"]
    batch_req["requests"].extend([
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 0, "endRowIndex": e_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        # Center numbers (Cols 3, 5, 6)
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 1, "endRowIndex": min(11, e_rows), "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 1, "endRowIndex": min(11, e_rows), "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        # Right-align ARR USD (Col 4)
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 1, "endRowIndex": min(11, e_rows), "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
        # Hyperlink styling on Col 0 & 7
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 1, "endRowIndex": min(11, e_rows), "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 1, "endRowIndex": min(11, e_rows), "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
        # Total row (Row 11 in 1-based, index 10)
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 10, "endRowIndex": min(11, e_rows), "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 10, "endRowIndex": min(11, e_rows), "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 10, "endRowIndex": min(11, e_rows), "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": 10, "endRowIndex": min(11, e_rows), "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        # Borders
        {"updateBorders": {"range": {"sheetId": SID_EXEC, "startRowIndex": 0, "endRowIndex": min(11, e_rows), "startColumnIndex": 0, "endColumnIndex": 8}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
        {"updateDimensionProperties": {"range": {"sheetId": SID_EXEC, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": SID_EXEC, "dimension": "ROWS", "startIndex": 1, "endIndex": min(11, e_rows)}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}}
    ])
    for r in range(1, min(10, e_rows)):
        if r % 2 == 1:
            batch_req["requests"].append({"repeatCell": {"range": {"sheetId": SID_EXEC, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})
    exec_w = {0: 300, 1: 200, 2: 160, 3: 140, 4: 160, 5: 140, 6: 140, 7: 200}
    for c, w in exec_w.items():
        batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": SID_EXEC, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})

tmp_f = "global_master_batch.json"
with open(tmp_f, "w") as f:
    json.dump(batch_req, f, indent=2)

res_b = subprocess.run([GSHEETS, "mutate", "raw-batch", GLOBAL_SSID, "-f", tmp_f], capture_output=True, text=True)
if res_b.returncode == 0:
    print("✓ Global Master Batch succeeded!")
else:
    print("✗ Global Master Batch error:", res_b.stderr)

if os.path.exists(tmp_f):
    os.remove(tmp_f)

subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(SID_WKL), "--rows", "5"], capture_output=True)
if d_info is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(d_info["sheetId"]), "--rows", "1"], capture_output=True)
if a_info is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(a_info["sheetId"]), "--rows", "1"], capture_output=True)
if e_info is not None:
    subprocess.run([GSHEETS, "mutate", "freeze", GLOBAL_SSID, "--sheet-id", str(e_info["sheetId"]), "--rows", "1"], capture_output=True)

print("Global Dashboard styling complete!")
