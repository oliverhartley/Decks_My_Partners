import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q" # Zenta

# In Follow_up, sheetId is 0.
# Range is Column O (startCol 14, endCol 15), rows 1 to 2000 (startRow 1, endRow 2000).
# Also let's check Column M (Workload Progress, startCol 12, endCol 13).

req = {
  "requests": [
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [
            {
              "sheetId": 0,
              "startRowIndex": 1,
              "endRowIndex": 2000,
              "startColumnIndex": 14,
              "endColumnIndex": 15
            }
          ],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [
                {
                  "userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), ISNUMBER($O2), $O2-TODAY()<=14, $O2<>\"\")"
                }
              ]
            },
            "format": {
              "backgroundColor": {
                "red": 0.949,
                "green": 0.545,
                "blue": 0.510
              },
              "textFormat": {
                "bold": True
              }
            }
          }
        },
        "index": 0
      }
    },
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [
            {
              "sheetId": 0,
              "startRowIndex": 1,
              "endRowIndex": 2000,
              "startColumnIndex": 14,
              "endColumnIndex": 15
            }
          ],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [
                {
                  "userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), ISNUMBER($O2), $O2-TODAY()>=15, $O2-TODAY()<=30)"
                }
              ]
            },
            "format": {
              "backgroundColor": {
                "red": 0.988,
                "green": 0.910,
                "blue": 0.902
              }
            }
          }
        },
        "index": 1
      }
    },
    {
      "addConditionalFormatRule": {
        "rule": {
          "ranges": [
            {
              "sheetId": 0,
              "startRowIndex": 1,
              "endRowIndex": 2000,
              "startColumnIndex": 14,
              "endColumnIndex": 15
            }
          ],
          "booleanRule": {
            "condition": {
              "type": "CUSTOM_FORMULA",
              "values": [
                {
                  "userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), ISNUMBER($O2), $O2-TODAY()>=31, $O2-TODAY()<=45)"
                }
              ]
            },
            "format": {
              "backgroundColor": {
                "red": 1.0,
                "green": 0.949,
                "blue": 0.800
              }
            }
          }
        },
        "index": 2
      }
    }
  ]
}

with open("test_cond_req.json", "w") as f:
    json.dump(req, f, indent=2)

res = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", "test_cond_req.json"], capture_output=True, text=True)
print("Returncode:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
