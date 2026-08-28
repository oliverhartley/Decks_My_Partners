import json
import csv
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

PARTNERS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "sheet_id": "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q",
        "csv_name": "Comercializadora_Zenta_Group_SPA_followup.csv"
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "sheet_id": "1qWdLgRDmHG9wMGjiOZ1fJvj4AmHbfKwrBPpuV8r2uwI",
        "csv_name": "Tech_Pulse_SPA__Axmos__followup.csv"
    },
    {
        "partner": "Devaid SPA",
        "sheet_id": "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8",
        "csv_name": "Devaid_SPA_followup.csv"
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "sheet_id": "1yOtNpVu8O8QQFeRx96s8TmgUtKcXAHYBdsoiZSmnSOI",
        "csv_name": "UCLOUD_STORE_COLOMBIA_S_A_S_followup.csv"
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "sheet_id": "1nUwpOaqhvpBmVoEb7i_M3C18jhmrJ7bQ1mrfwyXo02o",
        "csv_name": "TIVIT_COLOMBIA_S_A_S_followup.csv"
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "sheet_id": "1zcIQXnDbrR_WRhciVOD0XCN8RXK0_gHT0MUSExcqBbo",
        "csv_name": "VPN_Soluçoes_em_TI_LTDA__Venha_para_Nuvem__followup.csv"
    },
    {
        "partner": "MadeinWeb S/A",
        "sheet_id": "1K2_rFQ5tFMvvk_DnRNxbg3iJ9ZP-MkXtrrcuo04qTOI",
        "csv_name": "MadeinWeb_S_A_followup.csv"
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "sheet_id": "1jsiE3qCJxv5EnxnKJzBdoNFOENc1HA8TdlEXGgnUelo",
        "csv_name": "Consiti__Consultoría_y_Soluciones_Informáticas__followup.csv"
    }
]

PARTNER_COL_WIDTHS = {
    0: 280,  # Customer Account Name
    1: 90,   # Account Tier
    2: 240,  # Workload Name
    3: 200,  # Capacity Status
    4: 260,  # Opportunity Name
    5: 180,  # Expert Requests
    6: 120,  # Customer Sub Region
    7: 130,  # Customer Micro Region
    8: 180,  # Primary Workload Pillar
    9: 220,  # Sales Play
    10: 220, # Workload Solution
    11: 170, # Workload Progress
    12: 130, # Begin Migration Date
    13: 130, # Production Date
    14: 150, # ARR USD
    15: 160, # Last Touch
    16: 160  # Link
}

def get_grid_info(ssid):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        return {}
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

def process_partner(p):
    pname = p["partner"]
    ssid = p["sheet_id"]
    csv_file = os.path.join("followup_data_latest", p["csv_name"])
    print(f"\n==========================================")
    print(f"Processing Look & Feel for: {pname}")
    print(f"==========================================")

    # 1. READ CSV & RE-IMPORT Follow_up
    rows = []
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for r in reader:
                rows.append(r)
    
    header_row = [
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

    # Preserve manual notes if any in sheet
    res_notes = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Follow_up'!P6:Q2000", "--json"], capture_output=True, text=True)
    if res_notes.returncode == 0 and res_notes.stdout.strip():
        try:
            existing_notes = json.loads(res_notes.stdout)
            for i, note_pair in enumerate(existing_notes):
                if i < len(data_rows):
                    if len(note_pair) > 0 and note_pair[0] and not data_rows[i][15]:
                        data_rows[i][15] = note_pair[0]
                    if len(note_pair) > 1 and note_pair[1] and not data_rows[i][16]:
                        data_rows[i][16] = note_pair[1]
        except:
            pass

    # Build new 5-row structured layout
    new_rows = [
        ["Partner:", pname, "", "", "Last Update:", "24 - Aug 2026", "", "", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Alert Criteria:", "Target Go-Live risk for active pipeline (Stages 0-2 & 3)", "", "🔴 Critical (≤14d / Overdue)", "🌸 High (15-30d)", "🟡 Medium (31-45d)", "", "⚪ Normal (>45d / Stage 4+)", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        header_row
    ]
    new_rows.extend(data_rows)
    num_total_rows = len(new_rows)

    tmp_csv = f"temp_followup_{ssid}.csv"
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Follow_up'!2:2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, tmp_csv, "--sheet", "Follow_up"], capture_output=True)
    if os.path.exists(tmp_csv):
        os.remove(tmp_csv)

    # Fetch exact grid dimensions after import
    grid_info = get_grid_info(ssid)
    f_info = grid_info.get("Follow_up", {"sheetId": 0, "rowCount": num_total_rows, "columnCount": 17})
    d_info = grid_info.get("DRP_Status")
    a_info = grid_info.get("Acreditaciones")

    sid_followup = f_info["sheetId"]
    f_rows = f_info["rowCount"]

    batch_req = {
      "requests": [
        # Reset formatting
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 17},
            "cell": {
              "userEnteredFormat": {
                "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"},
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "OVERFLOW_CELL"
              }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
          }
        },
        # Unmerge
        {
          "unmergeCells": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": min(10, f_rows), "startColumnIndex": 0, "endColumnIndex": 17}
          }
        },
        # Merges
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        
        # Row 1 Format
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6},
            "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
          }
        },

        # Row 3 Format
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {
          "repeatCell": {
            "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 3},
            "cell": {"userEnteredFormat": {"textFormat": {"italic": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "LEFT"}},
            "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
          }
        },
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.77, "green": 0.13, "blue": 0.12}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.69, "green": 0.38, "blue": 0.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.49, "green": 0.29, "blue": 0.01}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 7, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.953, "blue": 0.957}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

        # Row 5 Main Header
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 15, "endColumnIndex": 17}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.075, "green": 0.451, "blue": 0.200}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

        # Data Rows Formatting
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 4, "endColumnIndex": 12}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 1, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 12, "endColumnIndex": 14}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 14, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 15, "endColumnIndex": 17}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.945, "green": 0.980, "blue": 0.957}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment)"}},

        # Hyperlinks
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
        {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

        # Borders
        {
          "updateBorders": {
            "range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 17},
            "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
            "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
          }
        },
        # Basic Filter
        {"clearBasicFilter": {"sheetId": sid_followup}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 17}}}},

        # Conditional Formatting Rules
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 17}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($L6,3)=\"0-2\",LEFT($L6,2)=\"3:\"), $N6<>\"\", ($N6-TODAY())<=14)"}]}, "format": {"backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}}}}, "index": 0}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 17}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($L6,3)=\"0-2\",LEFT($L6,2)=\"3:\"), $N6<>\"\", ($N6-TODAY())>=15, ($N6-TODAY())<=30)"}]}, "format": {"backgroundColor": {"red": 0.996, "green": 0.969, "blue": 0.878}}}}, "index": 1}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 17}], "booleanRule": {"condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": "=AND(OR(LEFT($L6,3)=\"0-2\",LEFT($L6,2)=\"3:\"), $N6<>\"\", ($N6-TODAY())>=31, ($N6-TODAY())<=45)"}]}, "format": {"backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}}}}, "index": 2}},

        # Row heights
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 5, "endIndex": f_rows}, "properties": {"pixelSize": 26}, "fields": "pixelSize"}}
      ]
    }

    # Zebra striping
    for r_idx in range(5, f_rows):
        if r_idx % 2 == 1:
            batch_req["requests"].append({
                "repeatCell": {
                    "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": 15},
                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                    "fields": "userEnteredFormat(backgroundColor)"
                }
            })

    # Column widths
    for col_idx, width in PARTNER_COL_WIDTHS.items():
        batch_req["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    # Format ER column if has links
    for r_idx in range(5, f_rows):
        if r_idx < len(new_rows):
            val = new_rows[r_idx][5]
            if "ER-" in val and ("HYPERLINK" in val or "http" in val):
                batch_req["requests"].append({
                    "repeatCell": {
                        "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 5, "endColumnIndex": 6},
                        "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}},
                        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
                    }
                })

    # 2. DRP_Status Formatting
    if d_info is not None:
        sid_drp = d_info["sheetId"]
        d_rows = d_info["rowCount"]
        batch_req["requests"].extend([
            {"repeatCell": {"range": {"sheetId": sid_drp, "startRowIndex": 0, "endRowIndex": d_rows, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_drp, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_drp, "startRowIndex": 1, "endRowIndex": d_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat(textFormat)"}},
            {"repeatCell": {"range": {"sheetId": sid_drp, "startRowIndex": 1, "endRowIndex": d_rows, "startColumnIndex": 3, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"updateBorders": {"range": {"sheetId": sid_drp, "startRowIndex": 0, "endRowIndex": d_rows, "startColumnIndex": 0, "endColumnIndex": 7}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_drp, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_drp, "dimension": "ROWS", "startIndex": 1, "endIndex": d_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}}
        ])
        for r in range(1, d_rows):
            if r % 2 == 1:
                batch_req["requests"].append({"repeatCell": {"range": {"sheetId": sid_drp, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})
        drp_w = {0: 220, 1: 240, 2: 240, 3: 110, 4: 110, 5: 120, 6: 200}
        for c, w in drp_w.items():
            batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": sid_drp, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    # 3. Acreditaciones Formatting
    if a_info is not None:
        sid_accred = a_info["sheetId"]
        a_rows = a_info["rowCount"]
        batch_req["requests"].extend([
            {"repeatCell": {"range": {"sheetId": sid_accred, "startRowIndex": 0, "endRowIndex": a_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"}, "verticalAlignment": "MIDDLE", "wrapStrategy": "OVERFLOW_CELL"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_accred, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_accred, "startRowIndex": 1, "endRowIndex": a_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat(textFormat)"}},
            {"repeatCell": {"range": {"sheetId": sid_accred, "startRowIndex": 1, "endRowIndex": a_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_accred, "startRowIndex": 1, "endRowIndex": a_rows, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(horizontalAlignment)"}},
            {"updateBorders": {"range": {"sheetId": sid_accred, "startRowIndex": 0, "endRowIndex": a_rows, "startColumnIndex": 0, "endColumnIndex": 8}, "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}, "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}, "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_accred, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_accred, "dimension": "ROWS", "startIndex": 1, "endIndex": a_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}}
        ])
        for r in range(1, a_rows):
            if r % 2 == 1:
                batch_req["requests"].append({"repeatCell": {"range": {"sheetId": sid_accred, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}}, "fields": "userEnteredFormat(backgroundColor)"}})
        acc_w = {0: 350, 1: 100, 2: 220, 3: 120, 4: 220, 5: 120, 6: 120, 7: 340}
        for c, w in acc_w.items():
            batch_req["requests"].append({"updateDimensionProperties": {"range": {"sheetId": sid_accred, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1}, "properties": {"pixelSize": w}, "fields": "pixelSize"}})

    tmp_f = f"batch_req_{ssid}.json"
    with open(tmp_f, "w") as f:
        json.dump(batch_req, f, indent=2)

    res_b = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_f], capture_output=True, text=True)
    if res_b.returncode == 0:
        print(f"✓ Batch formatting succeeded for {pname}")
    else:
        print(f"✗ Batch formatting error for {pname}: {res_b.stderr}")
    if os.path.exists(tmp_f):
        os.remove(tmp_f)

    # Freeze rows
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_followup), "--rows", "5"], capture_output=True)
    if d_info is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(d_info["sheetId"]), "--rows", "1"], capture_output=True)
    if a_info is not None:
        subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(a_info["sheetId"]), "--rows", "1"], capture_output=True)

# ----------------------------------------------------
# PROCESS ALL PARTNERS
# ----------------------------------------------------
for p in PARTNERS:
    process_partner(p)

print("\n==========================================")
print("ALL 8 PARTNERS UPDATED WITH NEW LOOK & FEEL!")
print("==========================================")
