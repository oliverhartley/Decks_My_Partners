import subprocess
import json

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GLOBAL_SSID = "17Xp09vIQdRpMVvdC0RaRpq_xT4wYe96hZ9brQ0yyKBA"
res = subprocess.run([GSHEETS, "readonly", "read", GLOBAL_SSID, "'All_Workloads_Follow_up'!A1:R5", "--json"], capture_output=True, text=True)
data = json.loads(res.stdout)
for idx, r in enumerate(data):
    w_name = r[3] if len(r) > 3 else ""
    play = r[9] if len(r) > 9 else ""
    sol = r[10] if len(r) > 10 else ""
    rag = r[15] if len(r) > 15 else ""
    lt = r[16] if len(r) > 16 else ""
    link = r[17] if len(r) > 17 else ""
    print(f"Row {idx}: {w_name[:25]} | Play: {play[:20]} | Sol: {sol[:20]} | RAG: {rag} | LastTouch: '{lt}' | Link: '{link}'")
