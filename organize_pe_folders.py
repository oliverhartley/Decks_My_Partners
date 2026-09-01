import json
import subprocess
import os

GDRIVE = "/google/bin/releases/gemini-agents-gdrive/gdrive"
ROOT_FOLDER = "1lYosvTFvXxhSAOzH7NQyJMgdXS-Gsz1t"

PE_FOLDERS = {
    "Fernando Laguna": "1lcH8eS61zjvZzk2WloNL6hU6OZwDyF2L",
    "Ignacio Rauda": "1T8-rGuqaRgExlqkneM4ZqR5lXNAAoAyC",
    "Jaquelyn Montañez": "1I6CQXCgHoBNy6wvrwcj_4O_yi6dGWBoL",
    "Luna Longo": "1KkI9RuO6Qxoi03MmMJ48jlTMeAmkNNrZ",
    "Oliver Hartley": "1WG2zMHJXRU8HnSCVR2cTN_5KeAUm5kQ3",
    "Thiago da Ponte": "1tK_qO-SjBD6YbWV9NF9XfvgtXoJs8Jrq"
}

with open("created_trackers.json", "r") as f:
    trackers = json.load(f)

print(f"Total trackers to organize: {len(trackers)}")

for t in trackers:
    partner = t["partner"]
    pe_raw = t["pe"]
    sheet_id = t["sheet_id"]
    
    # Split PEs in case of co-management
    pes = [p.strip() for p in pe_raw.split(",")]
    primary_pe = pes[0]
    secondary_pes = pes[1:]
    
    primary_folder_id = PE_FOLDERS.get(primary_pe)
    if not primary_folder_id:
        print(f"ERROR: No folder found for PE {primary_pe} (Partner: {partner})")
        continue
    
    # Move file to primary PE folder
    print(f"\nMoving '{partner}' ({sheet_id}) to '{primary_pe}' folder ({primary_folder_id})...")
    res = subprocess.run([GDRIVE, "mutate", "mv", sheet_id, primary_folder_id], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"✓ Moved to {primary_pe}")
    else:
        print(f"Status/Err: {res.stdout.strip() or res.stderr.strip()}")
        
    # If co-managed, create shortcut in secondary PE folders
    for sec_pe in secondary_pes:
        sec_folder_id = PE_FOLDERS.get(sec_pe)
        if sec_folder_id:
            print(f"Creating shortcut for '{partner}' in '{sec_pe}' folder ({sec_folder_id})...")
            res_sc = subprocess.run([GDRIVE, "mutate", "create-shortcut", sheet_id, sec_folder_id], capture_output=True, text=True)
            if res_sc.returncode == 0:
                print(f"✓ Created shortcut in {sec_pe}")
            else:
                print(f"Status/Err shortcut: {res_sc.stdout.strip() or res_sc.stderr.strip()}")

print("\n========================================================")
print("ALL PARTNER TRACKERS ORGANIZED INTO PE FOLDERS!")
print("========================================================")
