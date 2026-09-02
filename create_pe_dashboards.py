import json
import re
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GDRIVE = "/google/bin/releases/gemini-agents-gdrive/gdrive"

PE_FOLDERS = {
    "Fernando Laguna": "1lcH8eS61zjvZzk2WloNL6hU6OZwDyF2L",
    "Ignacio Rauda": "1T8-rGuqaRgExlqkneM4ZqR5lXNAAoAyC",
    "Jaquelyn Montañez": "1I6CQXCgHoBNy6wvrwcj_4O_yi6dGWBoL",
    "Luna Longo": "1KkI9RuO6Qxoi03MmMJ48jlTMeAmkNNrZ",
    "Oliver Hartley": "1WG2zMHJXRU8HnSCVR2cTN_5KeAUm5kQ3",
    "Thiago da Ponte": "1tK_qO-SjBD6YbWV9NF9XfvgtXoJs8Jrq"
}

dashboards = {}
if os.path.exists("pe_dashboards.json"):
    with open("pe_dashboards.json") as f:
        dashboards = json.load(f)

for pe, folder_id in PE_FOLDERS.items():
    if pe in dashboards and dashboards[pe].get("sheet_id"):
        print(f"PE Dashboard for {pe} already exists: {dashboards[pe]['sheet_id']}")
        continue
        
    title = f"Partner Management Dashboard - {pe}"
    print(f"Creating '{title}'...")
    res = subprocess.check_output([GSHEETS, "mutate", "create", "--title", title]).decode("utf-8")
    match = re.search(r"ID:\s*([a-zA-Z0-9_\-]+)", res)
    if not match:
        raise RuntimeError(f"Could not parse sheet ID from {res}")
    sheet_id = match.group(1)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    print(f"Created: {sheet_id}")
    
    print(f"Moving to folder {folder_id}...")
    subprocess.check_call([GDRIVE, "mutate", "mv", sheet_id, folder_id])
    print(f"Moved successfully.")
    
    dashboards[pe] = {
        "pe": pe,
        "sheet_id": sheet_id,
        "sheet_url": sheet_url,
        "folder_id": folder_id,
        "title": title
    }

with open("pe_dashboards.json", "w") as f:
    json.dump(dashboards, f, indent=2)

print("\nAll PE Dashboards recorded in pe_dashboards.json:")
for pe, d in dashboards.items():
    print(f"  - {pe}: {d['sheet_id']} ({d['sheet_url']})")
