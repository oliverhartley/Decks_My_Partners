import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
ssid = "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8"

res_f = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Follow_up'!A1:R4", "--json"], capture_output=True, text=True)
print("--- Devaid Follow_up Row 1-3 ---")
data_f = json.loads(res_f.stdout)
for idx, r in enumerate(data_f):
    print(f"Row {idx}:")
    for c_idx, c in enumerate(r):
        print(f"  Col {c_idx} ({chr(65+c_idx)}): {c}")

res_d = subprocess.run([GSHEETS, "readonly", "read", ssid, "'DRP_Status'!A1:G10", "--json"], capture_output=True, text=True)
print("\n--- Devaid DRP_Status Row 1-9 ---")
data_d = json.loads(res_d.stdout)
for idx, r in enumerate(data_d):
    print(f"Row {idx+1}: {r}")
