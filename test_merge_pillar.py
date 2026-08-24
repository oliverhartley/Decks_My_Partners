import subprocess
import json

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
ssid = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q" # Zenta

# Read DRP_Status rows
res = subprocess.run([GSHEETS, "readonly", "read", ssid, "'DRP_Status'!A1:F20", "--json"], capture_output=True, text=True)
data = json.loads(res.stdout)
print("Current DRP rows:")
for idx, r in enumerate(data):
    print(idx, r)

# Get sheet ID for DRP_Status
res_meta = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
sheets = json.loads(res_meta.stdout)
sheet_id = None
for s in sheets:
    if s["title"] == "DRP_Status":
        sheet_id = s["id"]
print("DRP_Status sheet ID:", sheet_id)

# Find contiguous Pillar blocks (0-indexed row numbers in Sheets, row 0 is header)
# Data rows start at row 1
pillar_blocks = []
current_pillar = None
start_r = 1

for r_idx in range(1, len(data)):
    p = data[r_idx][0] if len(data[r_idx]) > 0 else ""
    if current_pillar is None:
        current_pillar = p
        start_r = r_idx
    elif p != current_pillar:
        if r_idx - start_r > 1:
            pillar_blocks.append((current_pillar, start_r, r_idx))
        current_pillar = p
        start_r = r_idx

if current_pillar and (len(data) - start_r > 1):
    pillar_blocks.append((current_pillar, start_r, len(data)))

print("Pillar blocks to merge:", pillar_blocks)

# Execute merge for Pillar
for p, s_r, e_r in pillar_blocks:
    cmd = [
        GSHEETS, "mutate", "merge", ssid,
        "--sheet-id", str(sheet_id),
        "--start-row", str(s_r),
        "--end-row", str(e_r),
        "--start-col", "0",
        "--end-col", "1",
        "--merge-type", "MERGE_ALL"
    ]
    print("Running:", " ".join(cmd))
    res_m = subprocess.run(cmd, capture_output=True, text=True)
    print("Result:", res_m.stdout, res_m.stderr)

