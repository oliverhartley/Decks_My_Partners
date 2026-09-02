import json
import csv
import subprocess
import os
import re

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"
OLIVER_DASHBOARD_SSID = "1VkmmtXJopJ57K_XL3jwdqk8LrN6qw0_iGrBbl5deYpI"

with open("oliver_new_trackers.json") as f:
    new_ids = json.load(f)

# 1. Update created_trackers.json
with open("created_trackers.json") as f:
    trackers = json.load(f)

for t in trackers:
    p = t["partner"]
    if p in new_ids:
        t["sheet_id"] = new_ids[p]
        t["url"] = f"https://docs.google.com/spreadsheets/d/{new_ids[p]}/edit"

with open("created_trackers.json", "w") as f:
    json.dump(trackers, f, indent=2)
print("✓ Updated created_trackers.json")

# 2. Update update_all_partner_decks.py
with open("update_all_partner_decks.py") as f:
    content = f.read()

for p, new_ssid in new_ids.items():
    escaped_p = re.escape(p)
    pattern = rf'({escaped_p}.*?["\']sheet_id["\']:\s*["\'])([a-zA-Z0-9_\-]+)(["\'])'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        old_id = m.group(2)
        content = content.replace(f'"sheet_id": "{old_id}"', f'"sheet_id": "{new_ssid}"')
        print(f"✓ Replaced sheet_id in update_all_partner_decks.py for {p}: {old_id} -> {new_ssid}")

with open("update_all_partner_decks.py", "w") as f:
    f.write(content)
print("✓ Saved update_all_partner_decks.py")

# 3. Update Executive_Summary on Global Dashboard and Oliver Hartley Dashboard
def update_exec_summary(ssid, title_name):
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Executive_Summary'!A1:I50", "--json"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        print(f"Could not read Executive_Summary from {ssid}")
        return
    rows = json.loads(res.stdout)
    if not rows:
        return
    
    updated = False
    for r_idx in range(1, len(rows)):
        r = rows[r_idx]
        if len(r) > 8:
            p_val = r[1]
            for p, new_ssid in new_ids.items():
                if p.split()[0].lower() in p_val.lower():
                    tracker_url = f"https://docs.google.com/spreadsheets/d/{new_ssid}/edit#gid=0"
                    r[8] = f'=HYPERLINK("{tracker_url}","Open Partner Tracker ↗")'
                    updated = True
                    print(f"[{title_name}] Updated row {r_idx+1} ({p}) link to {new_ssid}")
    
    if updated:
        tmp_csv = f"temp_exec_{ssid}.csv"
        with open(tmp_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Executive_Summary'!A1:I50"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", "'Executive_Summary'!2:50"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "import-csv", ssid, tmp_csv, "--sheet", "Executive_Summary"], capture_output=True)
        if os.path.exists(tmp_csv):
            os.remove(tmp_csv)
        print(f"✓ Re-imported updated Executive_Summary for {title_name}")

update_exec_summary(GLOBAL_SSID, "Global Dashboard")
update_exec_summary(OLIVER_DASHBOARD_SSID, "Oliver Hartley Dashboard")
print("✓ Completed updating dashboards with new tracker links!")
