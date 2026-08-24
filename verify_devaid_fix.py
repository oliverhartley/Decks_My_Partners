import json
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
ssid = "1UqYI0iTbxFL1f8ohC3e-uMQCD2we_8Ne3ODmDjnT8U8"

res_f = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Follow_up'!A1:R4", "--json"], capture_output=True, text=True)
data_f = json.loads(res_f.stdout)
print("--- Verified Devaid Follow_up Rows ---")
for idx, r in enumerate(data_f):
    w_name = r[3] if len(r) > 3 else ""
    play = r[9] if len(r) > 9 else ""
    sol = r[10] if len(r) > 10 else ""
    rag = r[15] if len(r) > 15 else ""
    print(f"Row {idx}: {w_name[:30]} | Sol: {sol[:20]} | RAG: {rag}")

res_d = subprocess.run([GSHEETS, "readonly", "read", ssid, "'DRP_Status'!A1:G6", "--json"], capture_output=True, text=True)
data_d = json.loads(res_d.stdout)
print("\n--- Verified Devaid DRP_Status Row 5 ---")
for idx, r in enumerate(data_d):
    print(f"Row {idx+1}: {r}")
