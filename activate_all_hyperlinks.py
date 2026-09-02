#!/usr/bin/env python3
import json
import re
import subprocess
import os

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

def activate_sheet_hyperlinks(ssid, tab_title, start_row_1indexed, end_row_1indexed, max_col="Z"):
    print(f"\nProcessing {ssid} ('{tab_title}'!A{start_row_1indexed}:{max_col}{end_row_1indexed})...")
    
    # Get sheetId for tab_title
    res_info = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    sheet_id = 0
    if res_info.returncode == 0:
        try:
            sheets_meta = json.loads(res_info.stdout)
            for sm in sheets_meta:
                if sm.get("title") == tab_title:
                    sheet_id = sm.get("id", 0)
                    break
        except:
            pass

    # Read all formulas
    read_range = f"'{tab_title}'!A{start_row_1indexed}:{max_col}{end_row_1indexed}"
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, read_range, "--value-render-option", "FORMULA", "--json"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error reading {ssid}: {res.stderr}")
        return
    try:
        grid = json.loads(res.stdout)
    except Exception as e:
        print(f"Failed to parse JSON for {ssid}: {e}")
        return

    if not grid:
        print(f"No data found in {ssid} ('{tab_title}').")
        return

    requests = []
    # Pattern to match =HYPERLINK("url", "label")
    pattern = re.compile(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', re.IGNORECASE)

    base_row_0indexed = start_row_1indexed - 1
    for r_idx, row in enumerate(grid):
        sheet_row = base_row_0indexed + r_idx
        for c_idx, cell_val in enumerate(row):
            if not cell_val or not isinstance(cell_val, str):
                continue
            m = pattern.match(cell_val.strip())
            if m:
                url, label = m.group(1), m.group(2)
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": sheet_row,
                            "endRowIndex": sheet_row + 1,
                            "startColumnIndex": c_idx,
                            "endColumnIndex": c_idx + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "hyperlinkDisplayType": "LINKED",
                                "textFormat": {
                                    "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000},
                                    "underline": True,
                                    "link": {"uri": url}
                                }
                            }
                        },
                        "fields": "userEnteredFormat(hyperlinkDisplayType,textFormat(foregroundColor,underline,link))"
                    }
                })

    print(f"Found {len(requests)} hyperlink cells to activate in {ssid} ({tab_title}).")
    if not requests:
        return

    # Chunk requests in batches of 500 to avoid request size limits
    chunk_size = 500
    for i in range(0, len(requests), chunk_size):
        chunk = requests[i:i + chunk_size]
        tmp_f = f"/tmp/activate_links_{ssid}_{sheet_id}_{i}.json"
        with open(tmp_f, "w") as f:
            json.dump({"requests": chunk}, f)

        res_batch = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_f], capture_output=True, text=True)
        if os.path.exists(tmp_f):
            os.remove(tmp_f)

        if res_batch.returncode == 0:
            print(f"✓ Successfully activated chunk {i//chunk_size + 1} ({len(chunk)} links) for {ssid} ({tab_title})!")
        else:
            print(f"✗ Batch error for {ssid}: {res_batch.stderr.strip()}")

def main():
    with open("oliver_new_trackers.json") as f:
        oliver_trackers = json.load(f)

    # 1. Activate all 6 partner trackers
    for pname, ssid in oliver_trackers.items():
        print(f"\n==========================================")
        print(f"Activating hyperlinks for Partner: {pname} ({ssid})")
        activate_sheet_hyperlinks(ssid, "Follow_up", start_row_1indexed=6, end_row_1indexed=100)

    # 2. Activate Oliver Hartley Dashboard
    oliver_dash_ssid = "1VkmmtXJopJ57K_XL3jwdqk8LrN6qw0_iGrBbl5deYpI"
    print(f"\n==========================================")
    print(f"Activating hyperlinks for Oliver Hartley Dashboard ({oliver_dash_ssid})")
    activate_sheet_hyperlinks(oliver_dash_ssid, "Executive_Summary", start_row_1indexed=2, end_row_1indexed=20)
    activate_sheet_hyperlinks(oliver_dash_ssid, "All_Workloads_Follow_up", start_row_1indexed=6, end_row_1indexed=450)

if __name__ == "__main__":
    main()
