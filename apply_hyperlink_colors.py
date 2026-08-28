import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1oPv0eexAbvaP_sGQx70X8gEiooR9dXCFuFv1QDFhUew" # CU2

batch_req = {
  "requests": [
    # 1. Format Customer Account Name (Col 0) with standard Google Hyperlink styling (#1155cc, underline)
    {
      "repeatCell": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 5,
          "endRowIndex": 20,
          "startColumnIndex": 0,
          "endColumnIndex": 1
        },
        "cell": {
          "userEnteredFormat": {
            "textFormat": {
              "underline": True,
              "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000} # #1155cc
            }
          }
        },
        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
      }
    },
    # 2. Format Workload Name (Col 2) with standard Google Hyperlink styling (#1155cc, underline)
    {
      "repeatCell": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 5,
          "endRowIndex": 20,
          "startColumnIndex": 2,
          "endColumnIndex": 3
        },
        "cell": {
          "userEnteredFormat": {
            "textFormat": {
              "underline": True,
              "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000} # #1155cc
            }
          }
        },
        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
      }
    },
    # 3. Format Opportunity Name (Col 4) with standard Google Hyperlink styling (#1155cc, underline)
    {
      "repeatCell": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 5,
          "endRowIndex": 20,
          "startColumnIndex": 4,
          "endColumnIndex": 5
        },
        "cell": {
          "userEnteredFormat": {
            "textFormat": {
              "underline": True,
              "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000} # #1155cc
            }
          }
        },
        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
      }
    },
    # 4. Format Expert Requests (Col 5) row 15 (G4 Solutions) with standard Google Hyperlink styling
    {
      "repeatCell": {
        "range": {
          "sheetId": 0,
          "startRowIndex": 15,
          "endRowIndex": 16,
          "startColumnIndex": 5,
          "endColumnIndex": 6
        },
        "cell": {
          "userEnteredFormat": {
            "textFormat": {
              "underline": True,
              "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000} # #1155cc
            }
          }
        },
        "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"
      }
    }
  ]
}

tmp_f = "apply_hyperlink_colors.json"
with open(tmp_f, "w") as f:
    json.dump(batch_req, f, indent=2)

res = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", tmp_f], capture_output=True, text=True)
print("Batch Returncode:", res.returncode)
if res.returncode == 0:
    print("✓ Successfully applied typical hyperlink colors and underline!")
else:
    print("Error:", res.stderr)
