#!/usr/bin/env python3
"""
sync_engine.py
True Bidirectional (Last-Write-Wins / 3-Way State-Aware) Synchronization Engine
between the Agentic Workload Command Center Web UI and the 6 Brazil FSR Google Sheets.

Tracked fields (per workload, per column):
- Col K (10): 'Cual es el bloqueo?'             -> key: 'blocker'            (str)
- Col L (11): 'Status Tecnico'                  -> key: 'status_tecnico'     (str)
- Col R (17): 'Partner Technical Owner Email'   -> key: 'partner_tech_email' (str)
- Col S (18): 'Technical win'                   -> key: 'technical_win'      (bool)
- Col T (19): 'Propousal sent to client'        -> key: 'proposal_sent'      (bool)
"""

import os
import re
import json
import tempfile
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from copilot_engine import enrich_portfolio_cache

BASE_DIR = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners"
GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"

PORTFOLIO_CACHE_FILE = os.path.join(BASE_DIR, "data", "portfolio_cache.json")
ENRICHED_FILE = os.path.join(BASE_DIR, "data", "enriched_portfolio.json")
MANUAL_FILE = os.path.join(BASE_DIR, "fsr_manual_entries.json")
USER_DATA_FILE = os.path.join(BASE_DIR, "data", "workload_user_data.json")
BASELINE_FILE = os.path.join(BASE_DIR, "data", "last_synced_sheet_state.json")

FSR_SHEET_CONFIGS = [
    {"username": "fpilon", "name": "Felipe Pilon", "ssid": "1gS9JWRb-aReMKOiJzhlKEu0TFTb4fF8fNROcTKWf7jU"},
    {"username": "robertacoelho", "name": "Roberta Coelho", "ssid": "1wBiY2bqGo-NJaVeET6g8GRKfOTMDkQaSUhbD5xPfb5M"},
    {"username": "vmmoyses", "name": "Vanessa Moyses", "ssid": "1UXbDWQNf1_wvm6_WHtKX2QIWXzRgib_xMpMGfnu5nKg"},
    {"username": "dbenevides", "name": "Daniela Benevides", "ssid": "1PlnciU1NuNuo7SL0Jxb-X3HWksLzRXpYOVFk8UqmdAI"},
    {"username": "dprudencio", "name": "Daniel Prudencio", "ssid": "1qOUzmqu0vrZ7a19oSDR8KZTuDAfbdkJLiCDMoql9iqM"},
    {"username": "tobiassarah", "name": "Sarah Tobias", "ssid": "1eB2g5osFTKxH0i9B7AoddQO-MJ_qnewu3nwIozquTIs"},
    {"username": "anagama", "name": "Ana Luiza Gama", "ssid": "1VMLeUmBjnucCwW98Z4ElVdusQSOhQgIrWrKlQOGeZdA"},
    {"username": "renanvaladares", "name": "Renan Valadares", "ssid": "1YmVIhMxpaQpCV4DHP-cN3g4AFt5d2jCDHpQZaeF_soU"},
]

FIELD_SPECS = [
    {"key": "blocker", "user_key": "blocker_tecnico", "col_idx": 10, "header": "Cual es el bloqueo?", "is_bool": False},
    {"key": "status_tecnico", "user_key": "status_tecnico", "col_idx": 11, "header": "Status Tecnico", "is_bool": False},
    {"key": "partner_tech_email", "user_key": "partner_technical_email", "col_idx": 17, "header": "Partner Technical Owner Email", "is_bool": False},
    {"key": "technical_win", "user_key": "technical_win", "col_idx": 18, "header": "Technical win", "is_bool": True},
    {"key": "proposal_sent", "user_key": "proposal_sent", "col_idx": 19, "header": "Propousal sent to client", "is_bool": True},
]


def extract_hyperlink_label(cell_val):
    if not cell_val:
        return ""
    s = str(cell_val).strip()
    m = re.match(r'^=HYPERLINK\("[^"]*",\s*"(.*)"\)$', s, re.IGNORECASE)
    if m:
        return m.group(1).replace('""', '"').strip()
    return s


def extract_workload_id_from_formula(cell_val):
    if not cell_val:
        return ""
    s = str(cell_val).strip()
    m = re.search(r'/Workload__c/([a-zA-Z0-9]+)/view', s)
    if m:
        return m.group(1).strip()
    return ""


def norm_val(val, is_bool=False):
    if is_bool:
        if isinstance(val, bool):
            return val
        return str(val or "").strip().upper() in ("TRUE", "1", "YES")
    return str(val or "").strip()


def load_json_safe(path, default_val):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val


def save_json_safe(path, data):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def read_sheet_followup_state(cfg):
    """
    Reads Follow_up!A5:S300 from a single FSR Google Sheet, returning:
    {
      "username": ...,
      "ssid": ...,
      "sheet_id": 0,
      "rows_by_wname": {
         workload_name: {
            "row_index": 0-based row index in sheet,
            "values": {
               "blocker": str,
               "status_tecnico": str,
               "partner_tech_email": str,
               "technical_win": bool,
               "proposal_sent": bool
            }
         }
      }
    }
    """
    ssid = cfg["ssid"]
    result = {
        "username": cfg["username"],
        "name": cfg["name"],
        "ssid": ssid,
        "sheet_id": 0,
        "rows_by_wname": {}
    }

    # 1. Get Follow_up sheetId (defaults to 0, check list-sheets in case it's non-zero)
    res_sheets = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res_sheets.returncode == 0 and res_sheets.stdout.strip():
        try:
            for s in json.loads(res_sheets.stdout):
                if s.get("title") == "Follow_up":
                    result["sheet_id"] = int(s.get("id") or 0)
                    break
        except Exception:
            pass

    # 2. Read values & formulas from Follow_up!A5:T300 so we get exact Salesforce Workload IDs from Col C HYPERLINK
    res_read = subprocess.run(
        [GSHEETS, "readonly", "read", ssid, "'Follow_up'!A5:T300", "--value-render-option", "FORMULA", "--json"],
        capture_output=True, text=True
    )
    if res_read.returncode != 0 or not res_read.stdout.strip() or res_read.stdout.strip() == "null":
        res_read = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Follow_up'!A5:T300", "--json"], capture_output=True, text=True)
    if res_read.returncode != 0 or not res_read.stdout.strip() or res_read.stdout.strip() == "null":
        return result

    try:
        rows = json.loads(res_read.stdout)
        if not rows or len(rows) < 2:
            return result

        headers = [str(h).strip() for h in rows[0]]
        col_map = {h: i for i, h in enumerate(headers)}

        for offset, r in enumerate(rows[1:]):
            sheet_row_idx = 5 + offset  # 0-based row index (Row 6 is index 5)
            if len(r) <= 2 or not r[2]:
                continue
            wname = extract_hyperlink_label(r[2])
            if not wname:
                continue
            wid = extract_workload_id_from_formula(r[2])
            aname = extract_hyperlink_label(r[0]) if len(r) > 0 else ""
            oname = extract_hyperlink_label(r[1]) if len(r) > 1 else ""

            vals = {}
            for spec in FIELD_SPECS:
                c_idx = col_map.get(spec["header"], spec["col_idx"])
                if spec["key"] == "proposal_sent" and c_idx not in col_map.values():
                    c_idx = col_map.get("Proposal sent to client", spec["col_idx"])
                raw_v = r[c_idx] if c_idx < len(r) else ""
                vals[spec["key"]] = norm_val(raw_v, spec["is_bool"])

            row_key = wid if wid else f"{cfg['username']}||{aname}||{oname}||{wname}"
            result["rows_by_wname"][row_key] = {
                "row_index": sheet_row_idx,
                "workload_id": wid,
                "workload_name": wname,
                "account_name": aname,
                "opportunity_name": oname,
                "values": vals
            }
    except Exception as e:
        print(f"Warning reading sheet {ssid}: {e}")

    return result


def write_cell_updates_to_sheet(ssid, sheet_id, cell_updates):
    """
    Executes a single raw-batch updateCells call for all modified cells in a spreadsheet.
    cell_updates: list of {"row_index": int, "col_idx": int, "value": str|bool, "is_bool": bool}
    """
    if not cell_updates:
        return True

    reqs = []
    for u in cell_updates:
        r_idx = u["row_index"]
        c_idx = u["col_idx"]
        if u["is_bool"]:
            cell_val = {"boolValue": bool(u["value"])}
        else:
            cell_val = {"stringValue": str(u["value"] or "")}

        reqs.append({
            "updateCells": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": r_idx,
                    "endRowIndex": r_idx + 1,
                    "startColumnIndex": c_idx,
                    "endColumnIndex": c_idx + 1
                },
                "rows": [{"values": [{"userEnteredValue": cell_val}]}],
                "fields": "userEnteredValue"
            }
        })

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump({"requests": reqs}, tf)
        tmp_path = tf.name

    try:
        res = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_path], capture_output=True, text=True)
        return res.returncode == 0
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def sync_bidirectional(fsr_filter=None):
    """
    Performs a true bidirectional sync between local Web UI state and the 6 FSR Google Sheets.
    - Reads live values from the 6 Google Sheets in parallel.
    - Compares Sheet value vs Local Web value vs Last-Synced Baseline (and pending_web_edits).
    - Whichever side changed since the baseline wins and updates the other side.
    - If both changed, compares pending_web_edits timestamp vs sheet change (or lets the latest explicit edit win).
    """
    portfolio = load_json_safe(PORTFOLIO_CACHE_FILE, {})
    workloads = portfolio.get("fsr_workloads", [])
    wname_to_wid = {}
    triplet_to_wid = {}
    wid_to_default_email = {}
    wname_to_default_email = {}
    wname_counts = {}
    for w in workloads:
        wn = (w.get("workload_name") or "").strip()
        wid = (w.get("workload_id") or "").strip()
        uname = (w.get("workload_owner_username") or "").strip()
        aname = (w.get("account_name") or "").strip()
        oname = (w.get("opportunity_name") or "").strip()
        if wn:
            wname_counts[wn] = wname_counts.get(wn, 0) + 1
        if wn and wid:
            wname_to_wid[wn] = wid
            triplet_to_wid[(uname, aname, oname, wn)] = wid
            def_email = (w.get("partner_technical_email") or "").strip()
            wid_to_default_email[wid] = def_email
            wname_to_default_email[wn] = def_email

    manual_entries = load_json_safe(MANUAL_FILE, {})
    user_data = load_json_safe(USER_DATA_FILE, {})
    baseline = load_json_safe(BASELINE_FILE, {})

    target_cfgs = FSR_SHEET_CONFIGS
    if fsr_filter and fsr_filter.lower() not in ("all", ""):
        q = fsr_filter.lower().strip()
        target_cfgs = [
            c for c in FSR_SHEET_CONFIGS
            if q in c["username"].lower() or q in c["name"].lower()
        ]

    # 1. Read all target sheets in parallel
    sheet_states = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        fut_map = {pool.submit(read_sheet_followup_state, cfg): cfg["username"] for cfg in target_cfgs}
        for fut in as_completed(fut_map):
            uname = fut_map[fut]
            try:
                sheet_states[uname] = fut.result()
            except Exception as e:
                print(f"Error reading sheet for {uname}: {e}")

    now_iso = datetime.now().isoformat()
    pulled_from_sheets = []
    pushed_to_sheets = []
    sheet_write_batches = {}  # username -> (ssid, sheet_id, list of cell_updates)

    # 2. Reconcile every workload row
    for uname, s_state in sheet_states.items():
        ssid = s_state["ssid"]
        sheet_id = s_state["sheet_id"]
        cell_updates = []

        for row_key, row_info in s_state["rows_by_wname"].items():
            row_idx = row_info["row_index"]
            sheet_vals = row_info["values"]
            wname = row_info.get("workload_name") or row_key
            aname = row_info.get("account_name") or ""
            oname = row_info.get("opportunity_name") or ""
            wid = (
                row_info.get("workload_id")
                or triplet_to_wid.get((uname, aname, oname, wname))
                or (wname_to_wid.get(wname, "") if wname_counts.get(wname, 0) <= 1 else "")
            )
            default_bq_email = wid_to_default_email.get(wid) or wname_to_default_email.get(wname, "")
            is_unique_wname = wname_counts.get(wname, 0) <= 1
            primary_key = wid if wid else row_key

            m_entry = dict(manual_entries.get(primary_key) or (manual_entries.get(wname, {}) if is_unique_wname else {}))
            u_entry = dict(user_data.get(wid, {"notes": "", "attachments": []})) if wid else {}
            b_entry = dict(baseline.get(primary_key) or (baseline.get(wname, {}) if is_unique_wname else {}))
            pending_web = dict(m_entry.get("pending_web_edits", {}))

            row_local_changed = False

            for spec in FIELD_SPECS:
                fkey = spec["key"]
                ukey = spec["user_key"]
                is_bool = spec["is_bool"]
                col_idx = spec["col_idx"]

                s_val = norm_val(sheet_vals.get(fkey), is_bool)

                # Resolve current local value
                if fkey in m_entry:
                    raw_l = m_entry.get(fkey)
                elif ukey in u_entry:
                    raw_l = u_entry.get(ukey)
                elif fkey == "partner_tech_email":
                    raw_l = default_bq_email
                else:
                    raw_l = False if is_bool else ""
                l_val = norm_val(raw_l, is_bool)

                # Resolve baseline value (if no prior baseline exists, use l_val unless pending_web is set)
                has_baseline = fkey in b_entry
                b_val = norm_val(b_entry.get(fkey), is_bool) if has_baseline else l_val

                is_pending_web = fkey in pending_web
                sheet_changed_since_baseline = (s_val != b_val)
                local_changed_since_baseline = is_pending_web or (l_val != b_val)

                if s_val == l_val:
                    # Already in sync! Clear any pending flag and record baseline
                    winning_val = l_val
                    if is_pending_web:
                        pending_web.pop(fkey, None)
                        row_local_changed = True
                elif is_pending_web and not sheet_changed_since_baseline:
                    # Edited in Web UI, Sheet still has old baseline value -> Push Web UI value to Sheet!
                    winning_val = l_val
                    cell_updates.append({
                        "row_index": row_idx,
                        "col_idx": col_idx,
                        "value": winning_val,
                        "is_bool": is_bool
                    })
                    pushed_to_sheets.append({
                        "fsr": s_state["name"],
                        "workload_id": wid,
                        "workload_name": wname,
                        "field": spec["header"],
                        "old_sheet_value": s_val,
                        "new_value": winning_val
                    })
                    pending_web.pop(fkey, None)
                    row_local_changed = True
                elif sheet_changed_since_baseline and not is_pending_web:
                    # Edited in Google Sheet, Web UI was not touched -> Pull Sheet value into Web UI!
                    winning_val = s_val
                    m_entry[fkey] = winning_val
                    if wid:
                        u_entry[ukey] = winning_val
                    row_local_changed = True
                    pulled_from_sheets.append({
                        "fsr": s_state["name"],
                        "workload_id": wid,
                        "workload_name": wname,
                        "field": spec["header"],
                        "old_local_value": l_val,
                        "new_value": winning_val
                    })
                elif is_pending_web and sheet_changed_since_baseline:
                    # Both sides changed since last sync: Web UI has an unpushed edit AND Sheet changed.
                    # Let the explicit pending Web UI edit push to Sheet (since Web UI edit also attempts immediate write-through).
                    winning_val = l_val
                    cell_updates.append({
                        "row_index": row_idx,
                        "col_idx": col_idx,
                        "value": winning_val,
                        "is_bool": is_bool
                    })
                    pushed_to_sheets.append({
                        "fsr": s_state["name"],
                        "workload_id": wid,
                        "workload_name": wname,
                        "field": spec["header"],
                        "old_sheet_value": s_val,
                        "new_value": winning_val
                    })
                    pending_web.pop(fkey, None)
                    row_local_changed = True
                elif local_changed_since_baseline and not sheet_changed_since_baseline:
                    # Local differs from baseline while Sheet equals baseline -> Push Local to Sheet
                    winning_val = l_val
                    cell_updates.append({
                        "row_index": row_idx,
                        "col_idx": col_idx,
                        "value": winning_val,
                        "is_bool": is_bool
                    })
                    pushed_to_sheets.append({
                        "fsr": s_state["name"],
                        "workload_id": wid,
                        "workload_name": wname,
                        "field": spec["header"],
                        "old_sheet_value": s_val,
                        "new_value": winning_val
                    })
                else:
                    # Fallback when no baseline existed yet and not pending_web: Sheet value wins
                    winning_val = s_val
                    m_entry[fkey] = winning_val
                    if wid:
                        u_entry[ukey] = winning_val
                    row_local_changed = True
                    pulled_from_sheets.append({
                        "fsr": s_state["name"],
                        "workload_id": wid,
                        "workload_name": wname,
                        "field": spec["header"],
                        "old_local_value": l_val,
                        "new_value": winning_val
                    })

                b_entry[fkey] = winning_val

            baseline[primary_key] = b_entry
            if is_unique_wname:
                baseline[wname] = b_entry
            if row_local_changed or primary_key not in manual_entries:
                if pending_web:
                    m_entry["pending_web_edits"] = pending_web
                else:
                    m_entry.pop("pending_web_edits", None)
                if row_local_changed:
                    m_entry["updated_at"] = now_iso
                manual_entries[primary_key] = m_entry
                if is_unique_wname:
                    manual_entries[wname] = m_entry
                if wid and row_local_changed:
                    u_entry["updated_at"] = now_iso
                    user_data[wid] = u_entry

        if cell_updates:
            sheet_write_batches[uname] = (ssid, sheet_id, cell_updates)

    # 3. Execute cell writes in parallel for any sheets that have pushed changes
    if sheet_write_batches:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futs = [
                pool.submit(write_cell_updates_to_sheet, ssid, sheet_id, updates)
                for ssid, sheet_id, updates in sheet_write_batches.values()
            ]
            for f in as_completed(futs):
                f.result()

    # 4. Persist updated manual_entries, user_data, baseline, and re-enrich portfolio cache
    save_json_safe(MANUAL_FILE, manual_entries)
    save_json_safe(USER_DATA_FILE, user_data)
    save_json_safe(BASELINE_FILE, baseline)
    enrich_portfolio_cache()
    sync_drive_json_caches()

    return {
        "status": "ok",
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pulled_count": len(pulled_from_sheets),
        "pushed_count": len(pushed_to_sheets),
        "pulled_from_sheets": pulled_from_sheets,
        "pushed_to_sheets": pushed_to_sheets
    }


GDRIVE_BIN = "/google/bin/releases/gemini-agents-gdrive/gdrive"
PORTFOLIO_DRIVE_FILE_ID = "1cm_QlMMNbnqv0zeyD3HfmRO1xGZxvYBX"
MANUAL_ENTRIES_DRIVE_FILE_ID = "1CnhVKamb5IWUQ6uFxnNDHFSBaM4unvOG"
ENRICHED_WEB_FILE = os.path.join(BASE_DIR, "data", "enriched_portfolio_web.json")

SLIM_WORKLOAD_KEYS = [
    "workload_id", "account_name", "sfdc_account_id",
    "opportunity_name", "opportunity_id",
    "workload_name",
    "arr", "stage", "workload_progress_short",
    "implementation_date", "days_until_implementation",
    "production_date", "days_until_production",
    "blocker", "status_tecnico",
    "ai_summary_next_steps", "is_partnered",
    "opportunity_partner", "opportunity_partner_id",
    "workload_partner",
    "partner_technical_email", "primary_ce_email", "workload_owner_email",
    "fsr_name", "fsr_ldap",
    "pdm_owner", "supporting_ce", "technical_win", "proposal_sent"
]


def build_slim_web_portfolio():
    """
    Creates a compact (<500 KB) version of enriched_portfolio.json tailored for
    Google Apps Script Drive & HtmlService payload limits.
    """
    if not os.path.exists(ENRICHED_FILE):
        return None
    raw = load_json_safe(ENRICHED_FILE, {})
    src_workloads = raw.get("fsr_workloads") or raw.get("workloads") or []
    slim_list = []
    for w in src_workloads:
        item = {k: w.get(k) for k in SLIM_WORKLOAD_KEYS if k in w and w.get(k) not in (None, "")}
        item["workload_id"] = w.get("workload_id", "")
        item["account_name"] = w.get("account_name", "")
        item["workload_name"] = w.get("workload_name", "")
        item["arr"] = w.get("arr", 0)
        item["is_partnered"] = bool(w.get("is_partnered"))
        item["technical_win"] = bool(w.get("technical_win"))
        item["proposal_sent"] = bool(w.get("proposal_sent"))
        tel = w.get("activity_telemetry") or {}
        item["activity_telemetry"] = {
            "last_activity_date": tel.get("last_activity_date"),
            "days_inactive": tel.get("days_inactive"),
            "inactivity_tier": tel.get("inactivity_tier", "ACTIVE")
        }
        ns = str(w.get("next_steps") or "")
        if ns:
            item["next_steps"] = ns[:450] + ("..." if len(ns) > 450 else "")
        h = w.get("health") or {}
        if isinstance(h, dict) and h.get("status") == "RED":
            item["health"] = {"status": "RED"}
        recs = w.get("partner_recommendations") or (w.get("diagnosis") or {}).get("matched_partners") or []
        slim_recs = []
        for r in recs[:2]:
            if isinstance(r, dict):
                p_name = r.get("partner") or r.get("partner_name") or ""
                reason = str(r.get("reason") or r.get("selection_logic") or "")[:110]
                slim_recs.append({"partner": p_name, "reason": reason})
        if slim_recs and not item["is_partnered"]:
            item["partner_recommendations"] = slim_recs
        slim_list.append(item)

    slim_payload = {
        "generated_at": raw.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "fsr_workloads": slim_list
    }
    os.makedirs(os.path.dirname(ENRICHED_WEB_FILE), exist_ok=True)
    with open(ENRICHED_WEB_FILE, "w", encoding="utf-8") as f:
        json.dump(slim_payload, f, separators=(",", ":"), ensure_ascii=False)
    return ENRICHED_WEB_FILE


def sync_drive_json_caches():
    """
    Pushes the latest compact enriched_portfolio_web.json and fsr_manual_entries.json
    to Google Drive so the shared Google Apps Script Web App stays in sync.
    """
    if not os.path.exists(GDRIVE_BIN):
        return
    try:
        web_file = build_slim_web_portfolio()
        if web_file and os.path.exists(web_file):
            subprocess.run(
                [GDRIVE_BIN, "mutate", "update", PORTFOLIO_DRIVE_FILE_ID, web_file, "--mime-type", "application/json"],
                capture_output=True, text=True, timeout=25
            )
        if os.path.exists(MANUAL_FILE):
            subprocess.run(
                [GDRIVE_BIN, "mutate", "update", MANUAL_ENTRIES_DRIVE_FILE_ID, MANUAL_FILE, "--mime-type", "application/json"],
                capture_output=True, text=True, timeout=25
            )
    except Exception as e:
        print(f"Drive cache sync warning: {e}")


def push_single_workload_to_sheet_async(fsr_username, workload_name):
    """
    Triggered in a background thread right after a Web UI inline edit so that
    the specific FSR's Google Sheet is updated within ~1.5 seconds and baseline is recorded.
    """
    try:
        sync_bidirectional(fsr_filter=fsr_username)
    except Exception as e:
        print(f"Background write-through warning for {workload_name}: {e}")


if __name__ == "__main__":
    res = sync_bidirectional()
    print(json.dumps(res, indent=2, ensure_ascii=False))
