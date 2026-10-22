#!/usr/bin/env python3
"""
repair_roberta.py
Targeted script to completely repair and reformat Roberta Coelho's FSR Action Tracker Follow_up tab,
matching Felipe Pilon's format and cell colors 100%.
"""

import os
import sys
import json
import time
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1wBiY2bqGo-NJaVeET6g8GRKfOTMDkQaSUhbD5xPfb5M"
CSV_PATH = "fsr_decks_data/robertacoelho_followup.csv"

FOLLOWUP_COL_WIDTHS = {
    0: 260,  # Customer Account Name
    1: 260,  # Opportunity Name
    2: 260,  # Workload Name
    3: 150,  # Annual Gross Revenue (ARR USD)
    4: 170,  # Opportunity Stage
    5: 130,  # Workload Progress
    6: 140,  # Implementation Date
    7: 140,  # Days Until Implementation
    8: 130,  # Production Date
    9: 140,  # Days Until Production
    10: 160, # Cual es el bloqueo?
    11: 220, # Status Tecnico
    12: 340, # AI Summary Next Steps
    13: 240, # Opportunity Partner
    14: 240, # Workload Partner
    15: 200, # Workload Owner Email
    16: 200, # Primary CE Technical Owner Email
    17: 240, # Partner Technical Contact
    18: 240, # Client Technical Contact
    19: 130, # Technical win
    20: 170  # Propousal sent to client
}

def run_gsheets(args):
    for attempt in range(12):
        res = subprocess.run([GSHEETS] + args, capture_output=True, text=True)
        if res.returncode == 0:
            return res
        if "429" in res.stderr or "RATE_LIMIT_EXCEEDED" in res.stderr:
            wait_sec = 6 + (attempt * 3)
            print(f"  [429 rate limit] Sleeping {wait_sec}s before retry {attempt+1}...")
            time.sleep(wait_sec)
            continue
        print(f"  Command error (RC {res.returncode}): {res.stderr}")
        return res
    return res

def main():
    print("=" * 60)
    print("REPAIRING ROBERTA COELHO'S SHEET (100% MATCH FELIPE PILON)")
    print("=" * 60)

    # 1. Read CSV to determine rows and cols
    with open(CSV_PATH) as f:
        lines = f.readlines()
    f_rows = len(lines)
    p_cols = 21
    sid = 0
    print(f"Data rows: {f_rows}, Columns: {p_cols}, Sheet ID: {sid}")

    # 2. Clear all values on Follow_up
    print("Step 1: Clearing Follow_up tab values...")
    run_gsheets(["mutate", "clear", SSID, "'Follow_up'!A1:AJ1000"])

    # 3. Import fresh clean CSV
    print("Step 2: Re-importing clean CSV...")
    run_gsheets(["mutate", "import-csv", SSID, CSV_PATH, "--sheet", "Follow_up"])

    # 4. Construct comprehensive styling & layout requests
    print("Step 3: Constructing batch format payload...")
    reqs = [
        # A. Unmerge ALL cells across sheet 0 (0 to 1000, 0 to 26)
        {
            "unmergeCells": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 0,
                    "endColumnIndex": 26
                }
            }
        },

        # B. Reset all cell styles (white background, Arial 10pt plain black text, no borders)
        {
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 0,
                    "endColumnIndex": 26
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "textFormat": {
                            "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},
                            "fontSize": 10,
                            "bold": False,
                            "underline": False,
                            "fontFamily": "Arial"
                        },
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "CLIP"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        },

        # C. Clear all borders across entire sheet
        {
            "updateBorders": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": 0,
                    "endRowIndex": 1000,
                    "startColumnIndex": 0,
                    "endColumnIndex": 26
                },
                "top": {"style": "NONE"},
                "bottom": {"style": "NONE"},
                "left": {"style": "NONE"},
                "right": {"style": "NONE"},
                "innerHorizontal": {"style": "NONE"},
                "innerVertical": {"style": "NONE"}
            }
        },

        # D. Row 1 Pill merge & formats
        {
            "mergeCells": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 1,
                    "endColumnIndex": 4
                },
                "mergeType": "MERGE_ALL"
            }
        },
        {
            "updateCells": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 8
                },
                "rows": [{
                    "values": [
                        {"userEnteredValue": {"stringValue": "FSR:"}},
                        {"userEnteredValue": {"stringValue": "Roberta Coelho (robertacoelho@google.com)"}},
                        {"userEnteredValue": {"stringValue": ""}},
                        {"userEnteredValue": {"stringValue": ""}},
                        {"userEnteredValue": {"stringValue": "Supporting CE:"}},
                        {"userEnteredValue": {"stringValue": "Diego Baldini"}},
                        {"userEnteredValue": {"stringValue": "Last Update:"}},
                        {"userEnteredValue": {"stringValue": "22 - Oct 2026"}}
                    ]
                }],
                "fields": "userEnteredValue"
            }
        },
        # Row 1 Labels & Pills formatting
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                        "horizontalAlignment": "RIGHT"
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0},
                        "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                        "horizontalAlignment": "RIGHT"
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.95, "green": 0.91, "blue": 0.99},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 0.41, "green": 0.11, "blue": 0.66}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}},
                        "horizontalAlignment": "RIGHT"
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 7, "endColumnIndex": 8},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },

        # E. Row 3 Alert Banner
        {
            "mergeCells": {
                "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": p_cols},
                "mergeType": "MERGE_ALL"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": p_cols},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.949, "blue": 0.800},
                        "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 0.58, "green": 0.35, "blue": 0.0}},
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "CLIP"
                    },
                    "note": "Workloads in stage 4.3 (Migrated/Implemented) are now included. Added new field 'Opportunity Stage' between ARR and Workload Progress."
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy),note"
            }
        },

        # F. Row 5 Google Blue Table Headers (Cols 0 to 20)
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": p_cols},
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910},
                        "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        },

        # G. Data Rows (Rows 5 to f_rows): formatting & data types
        # Col 3 (D): ARR USD Currency
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 3, "endColumnIndex": 4},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        },
        # Col 4 (E): Opportunity Stage as TEXT (Center aligned)
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 4, "endColumnIndex": 5},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}, "horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
            }
        },
        # Col 5 (F): Workload Progress as plain TEXT (Center aligned)
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 5, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}, "horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
            }
        },
        # Col 7 (H) & Col 9 (J): Days Until Implementation / Production as integer NUMBER (#,##0)
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 7, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 9, "endColumnIndex": 10},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        },
        # Col 10 (K): Dropdown validation (Comercial, Tecnico)
        {
            "setDataValidation": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 10, "endColumnIndex": 11},
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": "Comercial"}, {"userEnteredValue": "Tecnico"}]
                    },
                    "showCustomUi": True,
                    "strict": False
                }
            }
        },
        # Col 19 (T) & Col 20 (U): Boolean checkboxes
        {
            "setDataValidation": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 19, "endColumnIndex": 21},
                "rule": {"condition": {"type": "BOOLEAN"}, "showCustomUi": True, "strict": False}
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 19, "endColumnIndex": 21},
                "cell": {
                    "userEnteredValue": {"boolValue": False},
                    "userEnteredFormat": {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE"}
                },
                "fields": "userEnteredValue,userEnteredFormat(horizontalAlignment,verticalAlignment)"
            }
        },

        # H. Clear and reset basic filter on row 5
        {"clearBasicFilter": {"sheetId": sid}},
        {
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sid,
                        "startRowIndex": 4,
                        "endRowIndex": f_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": p_cols
                    }
                }
            }
        },

        # I. Row heights
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "ROWS", "startIndex": 5, "endIndex": f_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}},

        # J. Trim columnCount to exactly 21 columns
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sid, "gridProperties": {"columnCount": p_cols}},
                "fields": "gridProperties.columnCount"
            }
        },

        # K. Copy-paste activation of interactive hyperlinks
        {
            "copyPaste": {
                "source": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
                "destination": {"sheetId": sid, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
                "pasteType": "PASTE_NORMAL",
                "pasteOrientation": "NORMAL"
            }
        }
    ]

    # Add column widths
    for c_idx, width in FOLLOWUP_COL_WIDTHS.items():
        reqs.append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c_idx, "endIndex": c_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    tmp_batch = f"/tmp/roberta_full_repair_{SSID}.json"
    with open(tmp_batch, "w") as f:
        json.dump({"requests": reqs}, f)

    print("Step 4: Executing raw-batch on Follow_up...")
    res_b = run_gsheets(["mutate", "raw-batch", SSID, "-f", tmp_batch])
    print(f"  Result: {res_b.stdout.strip()}")
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)

    # 5. Freeze top 5 rows
    print("Step 5: Freezing top 5 rows...")
    run_gsheets(["mutate", "freeze", SSID, "--sheet-id", str(sid), "--rows", "5"])

    print("\n✅ Roberta Coelho Follow_up tab successfully repaired and formatted!")

if __name__ == "__main__":
    main()
