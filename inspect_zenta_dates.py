import subprocess
import json

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SSID = "1xG-27ye3Wk4ob9nr3N08KP2a1ufaPRCxAP4o93NKj1Q"
res = subprocess.run([GSHEETS, "readonly", "read", SSID, "'Follow_up'!M1:O15", "--json"], capture_output=True, text=True)
data = json.loads(res.stdout)
for idx, r in enumerate(data):
    m_val = r[0] if len(r) > 0 else ""
    n_val = r[1] if len(r) > 1 else ""
    o_val = r[2] if len(r) > 2 else ""
    print(f"Row {idx+1}: M='{m_val}' | N='{n_val}' | O='{o_val}'")
