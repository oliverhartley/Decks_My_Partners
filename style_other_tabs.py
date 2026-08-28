import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew" # CU2

SID_DRP = 414658505
SID_ACCRED = 1627216995

batch_req = {
  "requests": [
    # ----------------------------------------------------
    # DRP_Status (SID_DRP)
    # ----------------------------------------------------
    # 1. Reset formatting
    {
      "repeatCell": {
        "range": {"sheetId": SID_DRP, "startRowIndex": 0, "endRowIndex": 40, "startColumnIndex": 0, "endColumnIndex": 10},
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
    # 2. Header (Row 1, index 0)
    {
      "repeatCell": {
        "range": {"sheetId": SID_DRP, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 7},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, # #1A73E8
            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
      }
    },
    # 3. Alignments (Pillar, Solution, Product = Left; Counts & Status = Center)
    {
      "repeatCell": {
        "range": {"sheetId": SID_DRP, "startRowIndex": 1, "endRowIndex": 35, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
        "fields": "userEnteredFormat(textFormat)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": SID_DRP, "startRowIndex": 1, "endRowIndex": 35, "startColumnIndex": 3, "endColumnIndex": 7},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # 4. Borders
    {
      "updateBorders": {
        "range": {"sheetId": SID_DRP, "startRowIndex": 0, "endRowIndex": 35, "startColumnIndex": 0, "endColumnIndex": 7},
        "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
      }
    },
    # 5. Row Heights
    {
      "updateDimensionProperties": {
        "range": {"sheetId": SID_DRP, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 36},
        "fields": "pixelSize"
      }
    },
    {
      "updateDimensionProperties": {
        "range": {"sheetId": SID_DRP, "dimension": "ROWS", "startIndex": 1, "endIndex": 35},
        "properties": {"pixelSize": 24},
        "fields": "pixelSize"
      }
    },

    # ----------------------------------------------------
    # Acreditaciones (SID_ACCRED)
    # ----------------------------------------------------
    # 1. Reset formatting
    {
      "repeatCell": {
        "range": {"sheetId": SID_ACCRED, "startRowIndex": 0, "endRowIndex": 35, "startColumnIndex": 0, "endColumnIndex": 10},
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
    # 2. Header (Row 1, index 0)
    {
      "repeatCell": {
        "range": {"sheetId": SID_ACCRED, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 8},
        "cell": {
          "userEnteredFormat": {
            "backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, # #1A73E8
            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
            "horizontalAlignment": "CENTER",
            "verticalAlignment": "MIDDLE",
            "wrapStrategy": "WRAP"
          }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
      }
    },
    # 3. Alignments (Cert Name = Left Bold; Type, Level = Left; Candidate ID, Dates = Center)
    {
      "repeatCell": {
        "range": {"sheetId": SID_ACCRED, "startRowIndex": 1, "endRowIndex": 30, "startColumnIndex": 0, "endColumnIndex": 1},
        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
        "fields": "userEnteredFormat(textFormat)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": SID_ACCRED, "startRowIndex": 1, "endRowIndex": 30, "startColumnIndex": 3, "endColumnIndex": 4},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    {
      "repeatCell": {
        "range": {"sheetId": SID_ACCRED, "startRowIndex": 1, "endRowIndex": 30, "startColumnIndex": 5, "endColumnIndex": 7},
        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
        "fields": "userEnteredFormat(horizontalAlignment)"
      }
    },
    # 4. Borders
    {
      "updateBorders": {
        "range": {"sheetId": SID_ACCRED, "startRowIndex": 0, "endRowIndex": 30, "startColumnIndex": 0, "endColumnIndex": 8},
        "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
        "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
        "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
      }
    },
    # 5. Row Heights
    {
      "updateDimensionProperties": {
        "range": {"sheetId": SID_ACCRED, "dimension": "ROWS", "startIndex": 0, "endIndex": 1},
        "properties": {"pixelSize": 36},
        "fields": "pixelSize"
      }
    },
    {
      "updateDimensionProperties": {
        "range": {"sheetId": SID_ACCRED, "dimension": "ROWS", "startIndex": 1, "endIndex": 30},
        "properties": {"pixelSize": 24},
        "fields": "pixelSize"
      }
    }
  ]
}

# Add zebra striping for DRP
for r in range(1, 35):
    if r % 2 == 1:
        batch_req["requests"].append({
            "repeatCell": {
                "range": {"sheetId": SID_DRP, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 7},
                "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                "fields": "userEnteredFormat(backgroundColor)"
            }
        })

# Add zebra striping for Accred
for r in range(1, 30):
    if r % 2 == 1:
        batch_req["requests"].append({
            "repeatCell": {
                "range": {"sheetId": SID_ACCRED, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 0, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                "fields": "userEnteredFormat(backgroundColor)"
            }
        })

# Column widths for DRP
drp_widths = {0: 220, 1: 240, 2: 240, 3: 110, 4: 110, 5: 120, 6: 200}
for c, w in drp_widths.items():
    batch_req["requests"].append({
        "updateDimensionProperties": {
            "range": {"sheetId": SID_DRP, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1},
            "properties": {"pixelSize": w},
            "fields": "pixelSize"
        }
    })

# Column widths for Accred
accred_widths = {0: 260, 1: 100, 2: 180, 3: 120, 4: 220, 5: 120, 6: 120, 7: 280}
for c, w in accred_widths.items():
    batch_req["requests"].append({
        "updateDimensionProperties": {
            "range": {"sheetId": SID_ACCRED, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1},
            "properties": {"pixelSize": w},
            "fields": "pixelSize"
        }
    })

tmp_f = "style_other_tabs.json"
with open(tmp_f, "w") as f:
    json.dump(batch_req, f, indent=2)

res = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", tmp_f], capture_output=True, text=True)
print("Batch Returncode:", res.returncode)
if res.returncode == 0:
    print("✓ Successfully styled DRP_Status and Acreditaciones tabs!")
else:
    print("Error:", res.stderr)
