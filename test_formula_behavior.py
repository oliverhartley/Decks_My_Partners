import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q"

# We will test adding a helper formula or reading what Sheets evaluates
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
                  "userEnteredValue": "=AND(OR(LEFT($M2,3)=\"0-2\",LEFT($M2,2)=\"3:\"), $O2<>\"\", (IFERROR(DATEVALUE(TEXT($O2,\"yyyy-mm-dd\")),$O2)-TODAY())<=14)"
                }
              ]
            },
            "format": {
              "backgroundColor": {
                "red": 0.918,
                "green": 0.263,
                "blue": 0.208
              },
              "textFormat": {
                "bold": True,
                "foregroundColor": {
                  "red": 1.0,
                  "green": 1.0,
                  "blue": 1.0
                }
              }
            }
          }
        },
        "index": 0
      }
    }
  ]
}

with open("test_formula_req.json", "w") as f:
    json.dump(req, f, indent=2)

res = subprocess.run([GSHEETS, "mutate", "raw-batch", SSID, "-f", "test_formula_req.json"], capture_output=True, text=True)
print("Returncode:", res.returncode)
print("Stdout:", res.stdout)
