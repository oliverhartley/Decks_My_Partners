import json
import os
import re
import subprocess

TARGET_FOLDER_ID = "1lYosvTFvXxhSAOzH7NQyJMgdXS-Gsz1t"
ARTIFACT_DIR = "/usr/local/google/home/oliverhartley/.gemini/jetski/brain/f55c8ba7-034d-4340-a132-e046ed54ab4c"

PARTNERS = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "provided_id": "0014M00001h39BLQAY",
        "verified_id": "0014M00001h39BLQAY",
        "title": "Comercializadora Zenta Group SPA action tracker",
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "provided_id": "0014M00002JmizDQAR",
        "verified_id": "0014M00002JmizDQAR",
        "title": "Tech Pulse SPA (Axmos) action tracker",
    },
    {
        "partner": "Devaid SPA",
        "provided_id": "0014M00001h38aiQAA",
        "verified_id": "0014M00001h38aiQAA",
        "title": "Devaid SPA action tracker",
    },
    {
        "partner": "UCLOUD STORE COLOMBIA S A S",
        "provided_id": "0014M00002M7lcJQAR",
        "verified_id": "0014M00002M7lcJQAR",
        "title": "UCLOUD STORE COLOMBIA S A S action tracker",
    },
    {
        "partner": "TIVIT COLOMBIA S A S",
        "provided_id": "001Kf0000150rJ2IAI",
        "verified_id": "0014M00001kxZPMQA2",
        "title": "TIVIT COLOMBIA S A S action tracker",
    },
    {
        "partner": "VPN Soluçoes em TI LTDA (Venha para Nuvem)",
        "provided_id": "0014M00001uFlbSQAS",
        "verified_id": "0014M00001uFlbSQAS",
        "title": "VPN Soluçoes em TI LTDA (Venha para Nuvem) action tracker",
    },
    {
        "partner": "MadeinWeb S/A",
        "provided_id": "0014M00002GGNRCQA5",
        "verified_id": "0014M00002GGNRCQA5",
        "title": "MadeinWeb S/A action tracker",
    },
    {
        "partner": "CU2 CLOUD TEC STORE SL",
        "provided_id": "0014M00001h35nAQAQ",
        "verified_id": "0014M00001h35nAQAQ",
        "title": "CU2 CLOUD TEC STORE SL action tracker",
    },
    {
        "partner": "Consiti (Consultoría y Soluciones Informáticas)",
        "provided_id": "0014M00001jus6LQAQ",
        "verified_id": "001Kf000013fuVXIAY",
        "title": "Consiti (Consultoría y Soluciones Informáticas) action tracker",
    },
]

GSHEETS_BIN = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GDRIVE_BIN = "/google/bin/releases/gemini-agents-gdrive/gdrive"

os.makedirs(ARTIFACT_DIR, exist_ok=True)
created_sheets = []

for p in PARTNERS:
    title = p["title"]
    print(f"Creating spreadsheet: {title}")
    res = subprocess.check_output([GSHEETS_BIN, "mutate", "create", "--title", title]).decode("utf-8")
    print("Create output:", res.strip())
    match = re.search(r"ID:\s*([a-zA-Z0-9_\-]+)", res)
    if not match:
        raise RuntimeError(f"Could not parse spreadsheet ID from: {res}")
    sheet_id = match.group(1)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    
    print(f"Moving {sheet_id} to folder {TARGET_FOLDER_ID}")
    subprocess.check_call([GDRIVE_BIN, "mutate", "mv", sheet_id, TARGET_FOLDER_ID])
    
    # Create URL artifact
    safe_title = re.sub(r'[\/\\:\*\?"<>\|]', '_', title)
    artifact_path = os.path.join(ARTIFACT_DIR, f"{safe_title}.url.json")
    with open(artifact_path, "w") as f:
        json.dump({
            "url": sheet_url,
            "title": title,
            "description": f"Action Tracker spreadsheet for {p['partner']}"
        }, f, indent=2)
    
    p["sheet_id"] = sheet_id
    p["sheet_url"] = sheet_url
    created_sheets.append(p)

print("\n--- Successfully Created All 9 Trackers ---")
with open("created_trackers.json", "w") as f:
    json.dump(created_sheets, f, indent=2)
print("Saved created_trackers.json")
