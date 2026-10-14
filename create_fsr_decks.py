#!/usr/bin/env python3
"""
create_fsr_decks.py
Generates & updates 3 dedicated Action Trackers ("decks") for Brazil Field Sales Representatives:
1. Felipe Pilon (fpilon@google.com)
2. Roberta Coelho (robertacoelho@google.com)
3. Vanessa Moyses (vmmoyses@google.com)

Each deck contains:
- Tab 1: Follow_up (Full 32-column interactive workload & opportunity pipeline tracker, with/without partners,
  sorted by fill color hierarchy & ARR descending, Estados Q3 conditional formatting, clip wrap, active links,
  and 7 persistent manual fields including Ask FSR, Status Tecnico, Blocker Tecnico, Plano de Execução)
- Tab 2: Executive_Summary (Vital KPIs, Stage distribution, Partner concentration, Top strategic deals)
- Tab 3: Unpartnered_Matchmaker (Unpartnered deals with top 2 recommended Brazil partners and transparent selection logic)
"""

import os
import sys
import json
import csv
import re
import datetime
import subprocess
import time

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners")
from update_all_partner_decks import (
    get_account_tier, parse_expert_requests, get_latest_update_str, make_hyperlink, norm_str, extract_hyperlink_label
)
from copilot_engine import match_partners_for_workload

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GDRIVE = "/google/bin/releases/gemini-agents-gdrive/gdrive"
OLIVER_FOLDER_ID = "1WG2zMHJXRU8HnSCVR2cTN_5KeAUm5kQ3"
LUNA_FOLDER_ID = "1KkI9RuO6Qxoi03MmMJ48jlTMeAmkNNrZ"

now = datetime.datetime.now()
DATE_FORMATTED = f"{now.day} - {now.strftime('%b')} {now.year}"

FSR_CONFIGS = [
    {
        "name": "Felipe Pilon",
        "email": "fpilon@google.com",
        "username": "fpilon",
        "title": "FSR Action Tracker - Felipe Pilon",
        "ssid": "1gS9JWRb-aReMKOiJzhlKEu0TFTb4fF8fNROcTKWf7jU",
        "folder_id": OLIVER_FOLDER_ID,
        "supporting_ce": "Diego Baldini",
        "supporting_ce_user": "diegobaldini",
        "pe_name": "Oliver Hartley"
    },
    {
        "name": "Roberta Coelho",
        "email": "robertacoelho@google.com",
        "username": "robertacoelho",
        "title": "FSR Action Tracker - Roberta Coelho",
        "ssid": "1wBiY2bqGo-NJaVeET6g8GRKfOTMDkQaSUhbD5xPfb5M",
        "folder_id": OLIVER_FOLDER_ID,
        "supporting_ce": "Diego Baldini",
        "supporting_ce_user": "diegobaldini",
        "pe_name": "Oliver Hartley"
    },
    {
        "name": "Vanessa Moyses",
        "email": "vmmoyses@google.com",
        "username": "vmmoyses",
        "title": "FSR Action Tracker - Vanessa Moyses",
        "ssid": "1UXbDWQNf1_wvm6_WHtKX2QIWXzRgib_xMpMGfnu5nKg",
        "folder_id": OLIVER_FOLDER_ID,
        "supporting_ce": "Diego Baldini",
        "supporting_ce_user": "diegobaldini",
        "pe_name": "Oliver Hartley"
    },
    {
        "name": "Daniela Benevides",
        "email": "dbenevides@google.com",
        "username": "dbenevides",
        "title": "FSR Action Tracker - Daniela Benevides",
        "ssid": "1PlnciU1NuNuo7SL0Jxb-X3HWksLzRXpYOVFk8UqmdAI",
        "folder_id": LUNA_FOLDER_ID,
        "supporting_ce": "Victor Hugo Ferreira",
        "supporting_ce_user": "vhferreira",
        "pe_name": "Luna Longo"
    },
    {
        "name": "Daniel Prudencio",
        "email": "dprudencio@google.com",
        "username": "dprudencio",
        "title": "FSR Action Tracker - Daniel Prudencio",
        "ssid": "1qOUzmqu0vrZ7a19oSDR8KZTuDAfbdkJLiCDMoql9iqM",
        "folder_id": LUNA_FOLDER_ID,
        "supporting_ce": "Victor Hugo Ferreira",
        "supporting_ce_user": "vhferreira",
        "pe_name": "Luna Longo"
    },
    {
        "name": "Sarah Tobias",
        "email": "tobiassarah@google.com",
        "username": "tobiassarah",
        "title": "FSR Action Tracker - Sarah Tobias",
        "ssid": "1eB2g5osFTKxH0i9B7AoddQO-MJ_qnewu3nwIozquTIs",
        "folder_id": LUNA_FOLDER_ID,
        "supporting_ce": "Victor Hugo Ferreira",
        "supporting_ce_user": "vhferreira",
        "pe_name": "Luna Longo"
    },
    {
        "name": "Ana Luiza Gama",
        "email": "anagama@google.com",
        "username": "anagama",
        "title": "FSR Action Tracker - Ana Luiza Gama",
        "ssid": "1VMLeUmBjnucCwW98Z4ElVdusQSOhQgIrWrKlQOGeZdA",
        "folder_id": OLIVER_FOLDER_ID,
        "supporting_ce": "Diego Baldini",
        "supporting_ce_user": "diegobaldini",
        "pe_name": "Oliver Hartley"
    },
    {
        "name": "Renan Valadares",
        "email": "renanvaladares@google.com",
        "username": "renanvaladares",
        "title": "FSR Action Tracker - Renan Valadares",
        "ssid": "1YmVIhMxpaQpCV4DHP-cN3g4AFt5d2jCDHpQZaeF_soU",
        "folder_id": LUNA_FOLDER_ID,
        "supporting_ce": "Victor Hugo Ferreira",
        "supporting_ce_user": "vhferreira",
        "pe_name": "Luna Longo"
    }
]

FOLLOWUP_HEADERS = [
    "Customer Account Name",            # Col 0 (A)
    "Opportunity Name",                 # Col 1 (B)
    "Workload Name",                    # Col 2 (C)
    "Annual Gross Revenue (ARR USD)",   # Col 3 (D)
    "Opportunity Stage",                # Col 4 (E)
    "Workload Progress",                # Col 5 (F)
    "Implementation Date",              # Col 6 (G)
    "Days Until Implementation",        # Col 7 (H)
    "Production Date",                  # Col 8 (I)
    "Days Until Production",            # Col 9 (J)
    "Cual es el bloqueo?",              # Col 10 (K)
    "Status Tecnico",                   # Col 11 (L)
    "AI Summary Next Steps",            # Col 12 (M)
    "Opportunity Partner",              # Col 13 (N)
    "Workload Partner",                 # Col 14 (O)
    "Workload Owner Email",             # Col 15 (P)
    "Primary CE Technical Owner Email", # Col 16 (Q)
    "Partner Technical Owner Email",    # Col 17 (R)
    "Technical win",                    # Col 18 (S)
    "Propousal sent to client"          # Col 19 (T)
]

FOLLOWUP_COL_WIDTHS = {
    0: 260,  # Customer Account Name
    1: 260,  # Opportunity Name
    2: 260,  # Workload Name
    3: 150,  # Annual Gross Revenue (ARR USD)
    4: 170,  # Opportunity Stage
    5: 130,  # Workload Progress
    6: 140,  # Implementation Date
    7: 140,  # Days Until Implementation
    8: 130,  # Production Date
    9: 140,  # Days Until Production
    10: 160, # Cual es el bloqueo?
    11: 220, # Status Tecnico
    12: 340, # AI Summary Next Steps
    13: 240, # Opportunity Partner
    14: 240, # Workload Partner
    15: 200, # Workload Owner Email
    16: 200, # Primary CE Technical Owner Email
    17: 220, # Partner Technical Owner Email
    18: 130, # Technical win
    19: 170  # Propousal sent to client
}

MATCHMAKER_HEADERS = [
    "Customer Account Name",            # Col 0 (A)
    "Account Tier",                     # Col 1 (B)
    "Workload Name",                    # Col 2 (C)
    "Annual Gross Revenue (ARR USD)",   # Col 3 (D)
    "Workload Progress",                # Col 4 (E)
    "Primary Pillar",                   # Col 5 (F)
    "Key Products / Solution",          # Col 6 (G)
    "Top Proposed Partner 1",           # Col 7 (H)
    "Partner 1 Standing & Bench",       # Col 8 (I)
    "Partner 1 Selection Logic",        # Col 9 (J)
    "Alternative Partner 2",            # Col 10 (K)
    "Partner 2 Standing & Bench",       # Col 11 (L)
    "Partner 2 Selection Logic",        # Col 12 (M)
    "Target Production Date",           # Col 13 (N)
    "Opportunity Name",                 # Col 14 (O)
    "Next Steps"                        # Col 15 (P)
]

MATCHMAKER_COL_WIDTHS = {
    0: 280,
    1: 90,
    2: 260,
    3: 150,
    4: 170,
    5: 180,
    6: 220,
    7: 240,
    8: 200,
    9: 340,
    10: 240,
    11: 200,
    12: 340,
    13: 140,
    14: 260,
    15: 350
}

SUMMARY_COL_WIDTHS = {
    0: 280,
    1: 180,
    2: 180,
    3: 160,
    4: 220,
    5: 160,
    6: 140
}


def get_grid_info(ssid):
    res = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return {}
    data = json.loads(res.stdout)
    grid_info = {}
    for s in data.get("sheets", []):
        props = s.get("properties", {})
        grid_info[props.get("title")] = {
            "sheetId": props.get("sheetId", 0),
            "rowCount": props.get("gridProperties", {}).get("rowCount", 1000),
            "columnCount": props.get("gridProperties", {}).get("columnCount", 26)
        }
    return grid_info


def ensure_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
            for s in sheets:
                if s.get("title") in ["Sheet1", "Hoja 1", "Página1", "Página 1", "Sheet 1"] and tab_title == "Follow_up":
                    subprocess.run([GSHEETS, "mutate", "rename-sheet", ssid, "--sheet-id", str(s.get("id")), "--title", tab_title], capture_output=True)
                    return s.get("id")
        except:
            pass
    subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    res2 = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            sheets = json.loads(res2.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    return 0


def cleanup_default_sheet(ssid):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            if len(sheets) > 1:
                for s in sheets:
                    if s.get("title") in ["Sheet1", "Hoja 1", "Página1", "Página 1", "Sheet 1"]:
                        subprocess.run([GSHEETS, "mutate", "delete-sheet", ssid, "--sheet-id", str(s["id"])], capture_output=True)
        except:
            pass


def fetch_existing_fsr_manual_entries(ssid):
    """Reads existing manual entries from Follow_up tab to ensure they persist across updates."""
    if not ssid:
        return {}
    res = subprocess.run([GSHEETS, "readonly", "read", ssid, "'Follow_up'!A5:AF250", "--json"], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip() or res.stdout.strip() == "null":
        return {}
    try:
        data = json.loads(res.stdout)
        if not data or len(data) < 2:
            return {}
        headers = [str(h).strip() for h in data[0]]
        col_map = {h: idx for idx, h in enumerate(headers)}

        def get_col(row, col_name, fallback_idx=None):
            idx = col_map.get(col_name, fallback_idx)
            if idx is not None and idx < len(row) and row[idx]:
                return str(row[idx]).strip()
            return ""

        entries = {}
        for r in data[1:]:
            if len(r) > 2 and r[2]:
                wname = extract_hyperlink_label(r[2])
                notes_tasks = get_col(r, "Notes / Tasks")
                blocker = get_col(r, "Cual es el bloqueo?")
                solution = get_col(r, "Como se soluciona")
                ask_fsr = get_col(r, "Ask FSR")
                status_tecnico = get_col(r, "Status Tecnico")
                blocker_tecnico = get_col(r, "Blocker Tecnico")
                plano_execucao = get_col(r, "Plano de Execução")
                partner_tech_email = get_col(r, "Partner Technical Owner Email")
                tech_win_raw = get_col(r, "Technical win")
                prop_sent_raw = get_col(r, "Propousal sent to client") or get_col(r, "Proposal sent to client")

                tech_win_bool = str(tech_win_raw).strip().upper() == "TRUE"
                prop_sent_bool = str(prop_sent_raw).strip().upper() == "TRUE"

                if any([notes_tasks, blocker, solution, ask_fsr, status_tecnico, blocker_tecnico, plano_execucao, partner_tech_email, tech_win_bool, prop_sent_bool]):
                    entries[wname] = {
                        "notes_tasks": notes_tasks,
                        "blocker": blocker,
                        "solution": solution,
                        "ask_fsr": ask_fsr,
                        "status_tecnico": status_tecnico,
                        "blocker_tecnico": blocker_tecnico,
                        "plano_execucao": plano_execucao,
                        "partner_tech_email": partner_tech_email,
                        "technical_win": tech_win_bool,
                        "proposal_sent": prop_sent_bool
                    }
        return entries
    except Exception as e:
        print(f"Warning fetching manual entries for {ssid}: {e}")
        return {}


def get_color_rank(status):
    s = (status or "").strip()
    if s == "High risk":
        return 1  # Red (#FF0000)
    elif s == "Validate Commit":
        return 2  # Yellow (#FFFF00)
    elif s == "Pull-in":
        return 3  # Orange (#FF9900)
    elif s == "Medium risk":
        return 4  # Pale Orange / Beige (#fff2cc)
    elif s == "Critical Path":
        return 5  # Purple (#674ea7)
    elif s == "Hygiene Review":
        return 6  # Gray (#cccccc)
    elif s == "Low Priority":
        return 7  # Light Gray (#f3f3f3)
    elif s == "On Track":
        return 8  # Soft Blue (#ddedf7)
    else:
        return 9  # White / None / Unprioritized


AI_SUMMARIES_FILE = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners/data/next_steps_ai_summaries.json"
GENERATE_BIN = "/google/bin/releases/gemini-agents-generate/generate"


def get_ai_next_steps_summary(w, ai_cache):
    import hashlib
    wid = w.get("workload_id") or ""
    hist = w.get("next_steps_history") or []
    ns = (w.get("next_steps") or "").strip()
    if not hist and not ns:
        return "", False

    raw_payload = json.dumps({"hist": hist, "ns": ns}, sort_keys=True, ensure_ascii=False)
    h = hashlib.md5(raw_payload.encode("utf-8")).hexdigest()

    cached = ai_cache.get(wid)
    if cached and cached.get("history_hash") == h and cached.get("summary"):
        return cached["summary"], False

    # Build timeline text
    lines = []
    for item in hist[:6]:
        d_str = item.get("date") or ""
        txt = (item.get("text") or "").replace("\r\n", " ").replace("\n", " ").strip()
        if txt:
            lines.append(f"[{d_str}] {txt}")
    if not lines and ns:
        lines.append(ns.replace("\r\n", " ").replace("\n", " ").strip())

    timeline_str = " | ".join(lines)
    summary_text = ""
    if os.path.exists(GENERATE_BIN):
        prompt = (
            "Summarize this Salesforce workload Next Steps History into a single concise executive sentence "
            "(max 22 words, in Portuguese, starting with the latest update date DD/MM if available, focusing on current status and next action/blocker):\n"
            f"{timeline_str}"
        )
        try:
            res = subprocess.run([GENERATE_BIN, "text", prompt], capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout.strip():
                summary_text = res.stdout.strip().splitlines()[-1].strip().strip('"')
        except Exception:
            pass

    if not summary_text:
        latest = lines[0]
        summary_text = latest[:160] + ("..." if len(latest) > 160 else "")

    ai_cache[wid] = {"history_hash": h, "summary": summary_text}
    return summary_text, True


def build_fsr_deck(fsr_cfg, cache, prio_map, user_data, existing_manual=None, out_dir="fsr_decks_data"):
    fsr_name = fsr_cfg["name"]
    fsr_email = fsr_cfg["email"]
    fsr_user = fsr_cfg["username"]
    fsr_title = fsr_cfg["title"]
    supporting_ce = fsr_cfg.get("supporting_ce", "Diego Baldini")
    supporting_ce_user = fsr_cfg.get("supporting_ce_user", "diegobaldini")
    pe_name = fsr_cfg.get("pe_name", "Oliver Hartley")
    folder_id = fsr_cfg.get("folder_id", OLIVER_FOLDER_ID)

    if existing_manual is None:
        existing_manual = {}

    ai_cache = {}
    if os.path.exists(AI_SUMMARIES_FILE):
        try:
            with open(AI_SUMMARIES_FILE, "r", encoding="utf-8") as af:
                ai_cache = json.load(af)
        except Exception:
            ai_cache = {}
    ai_cache_dirty = False

    all_workloads = cache.get("fsr_workloads", [])
    candidates = cache.get("candidate_partners", [])

    # Filter for this FSR, excluding stage 4.3 (Migrated/Implemented)
    wkls = [
        w for w in all_workloads
        if (w.get("workload_owner_username") == fsr_user or norm_str(w.get("workload_owner_name")) == norm_str(fsr_name))
        and not (w.get("workload_progress") or "").strip().startswith("4.3")
        and "4.3" not in (w.get("workload_progress") or "")
    ]
    
    # Sort by ARR descending
    wkls.sort(key=lambda x: -float(x.get("annual_gross_revenue") or 0.0))

    partnered_wkls = [w for w in wkls if w.get("is_partnered")]
    unpartnered_wkls = [w for w in wkls if not w.get("is_partnered")]
    unpartnered_wkls.sort(key=lambda x: -float(x.get("annual_gross_revenue") or 0.0))

    total_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in wkls)
    partnered_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in partnered_wkls)
    unpartnered_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in unpartnered_wkls)

    # -------------------------------------------------------------
    # 1. TAB 1: Follow_up CSV (20 Columns)
    # -------------------------------------------------------------
    num_cols = len(FOLLOWUP_HEADERS)
    followup_rows = []
    # Row 1: Header metadata (20 cols total)
    r1 = ["FSR:", f"{fsr_name} ({fsr_email})", "", "", "Supporting CE:", supporting_ce, "Last Update:", DATE_FORMATTED] + [""] * (num_cols - 8)
    # Rows 2-4: Row 3 alert note to alert users of stage 4.3 removal & Opportunity Stage addition
    r2 = [""] * num_cols
    alert_note_text = "📢 UPDATE: Workloads in stage 4.3 (Migrated/Implemented) have been removed. Added new field 'Opportunity Stage' between ARR and Workload Progress."
    r3 = [alert_note_text] + [""] * (num_cols - 1)
    r4 = [""] * num_cols
    # Row 5: Column Headers (20 cols total)
    r5 = list(FOLLOWUP_HEADERS)

    followup_rows.extend([r1, r2, r3, r4, r5])

    true_tech_wins = []
    true_prop_sents = []

    for idx, w in enumerate(wkls):
        row_num = idx + 6
        wid = w.get("workload_id") or ""
        wname = w.get("workload_name") or ""
        aid = w.get("sfdc_account_id") or ""
        aname = w.get("account_name") or ""
        opp_id = w.get("opportunity_id") or ""
        opp_name = w.get("opportunity_name") or ""
        pid = w.get("partner_id") or ""
        pname = w.get("partner_name") or ""
        is_part = w.get("is_partnered", False)
        opp_pid = w.get("opportunity_partner_id") or ""
        opp_pname = w.get("opportunity_partner_name") or ""
        arr_val = float(w.get("annual_gross_revenue") or 0.0)
        opp_stage = (w.get("stage_name") or "").strip()
        progress = w.get("workload_progress") or ""
        prog_short = progress.split(":")[0].strip() if ":" in progress else progress.strip()

        # Links
        acc_url = f"https://vector.lightning.force.com/lightning/r/Account/{aid}/view" if aid else ""
        acc_cell = make_hyperlink(acc_url, aname) if acc_url else aname

        opp_url = f"https://vector.lightning.force.com/lightning/r/Opportunity/{opp_id}/view" if opp_id else ""
        opp_cell = make_hyperlink(opp_url, opp_name) if opp_url else opp_name

        wkl_url = f"https://vector.lightning.force.com/lightning/r/Workload__c/{wid}/view" if wid else ""
        wkl_cell = make_hyperlink(wkl_url, wname) if wkl_url else wname

        if opp_pname:
            opp_p_url = f"https://vector.lightning.force.com/lightning/r/Account/{opp_pid}/view" if opp_pid else ""
            opp_partner_cell = make_hyperlink(opp_p_url, opp_pname) if opp_p_url else opp_pname
        else:
            opp_partner_cell = ""

        if is_part and pname:
            p_url = f"https://vector.lightning.force.com/lightning/r/Account/{pid}/view" if pid else ""
            wkl_partner_cell = make_hyperlink(p_url, pname) if p_url else pname
        else:
            wkl_partner_cell = ""

        # Owner & CE Emails
        owner_user = w.get("workload_owner_username") or fsr_user
        owner_email = f"{owner_user}@google.com" if "@" not in owner_user else owner_user

        ce_user = w.get("primary_ce_username") or supporting_ce_user
        ce_email = f"{ce_user}@google.com" if "@" not in ce_user else ce_user

        impl_date = str(w.get("begin_migration_date") or "").strip()
        prod_date = str(w.get("production_date") or "").strip()

        # Implementation is Col G (6), Production is Col I (8)
        days_impl = f'=IF(G{row_num}<>"", G{row_num}-TODAY(), "")'
        days_prod = f'=IF(I{row_num}<>"", I{row_num}-TODAY(), "")'

        # Notes / User Data Persistence: Prioritize existing sheet manual entries (by workload_id first, then workload_name), then local user_data cache
        m_entry = existing_manual.get(wid) or existing_manual.get(wname, {})
        u_info = user_data.get(wid, {})

        blocker_val = m_entry.get("blocker") or u_info.get("blocker_tecnico") or ""
        status_tecnico_val = m_entry.get("status_tecnico") or u_info.get("status_tecnico") or ""
        partner_tech_email = m_entry.get("partner_tech_email") or w.get("partner_technical_email") or ""

        def to_bool_str(val):
            if isinstance(val, bool):
                return "TRUE" if val else ""
            return "TRUE" if str(val or "").strip().upper() in ("TRUE", "1", "YES") else ""

        tech_win_val = to_bool_str(m_entry.get("technical_win") if "technical_win" in m_entry else u_info.get("technical_win"))
        prop_sent_val = to_bool_str(m_entry.get("proposal_sent") if "proposal_sent" in m_entry else u_info.get("proposal_sent"))

        if tech_win_val == "TRUE":
            true_tech_wins.append(row_num - 1)
        if prop_sent_val == "TRUE":
            true_prop_sents.append(row_num - 1)

        ai_summary_val, updated_ai = get_ai_next_steps_summary(w, ai_cache)
        if updated_ai:
            ai_cache_dirty = True

        row_data = [
            acc_cell,                   # 0 (A): Customer Account Name
            opp_cell,                   # 1 (B): Opportunity Name
            wkl_cell,                   # 2 (C): Workload Name
            f"${arr_val:,.2f}",         # 3 (D): Annual Gross Revenue (ARR USD)
            opp_stage,                  # 4 (E): Opportunity Stage
            prog_short,                 # 5 (F): Workload Progress (number only)
            impl_date,                  # 6 (G): Implementation Date
            days_impl,                  # 7 (H): Days Until Implementation
            prod_date,                  # 8 (I): Production Date
            days_prod,                  # 9 (J): Days Until Production
            blocker_val,                # 10 (K): Cual es el bloqueo?
            status_tecnico_val,         # 11 (L): Status Tecnico
            ai_summary_val,             # 12 (M): AI Summary Next Steps
            opp_partner_cell,           # 13 (N): Opportunity Partner
            wkl_partner_cell,           # 14 (O): Workload Partner
            owner_email,                # 15 (P): Workload Owner Email
            ce_email,                   # 16 (Q): Primary CE Technical Owner Email
            partner_tech_email,         # 17 (R): Partner Technical Owner Email
            tech_win_val,               # 18 (S): Technical win (Checkbox)
            prop_sent_val               # 19 (T): Propousal sent to client (Checkbox)
        ]
        followup_rows.append(row_data)

    if ai_cache_dirty:
        with open(AI_SUMMARIES_FILE, "w", encoding="utf-8") as af:
            json.dump(ai_cache, af, indent=2, ensure_ascii=False)

    followup_csv_path = os.path.join(out_dir, f"{fsr_user}_followup.csv")
    with open(followup_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(followup_rows)

    # -------------------------------------------------------------
    # 2. TAB 2: Executive_Summary CSV
    # -------------------------------------------------------------
    # Stage aggregates
    stages_agg = {
        "00-01: Qualify & Refine": {"count": 0, "arr": 0.0},
        "02: Tech Eval / Solution Dev": {"count": 0, "arr": 0.0},
        "03: Proposal & Negotiation": {"count": 0, "arr": 0.0},
        "04+: Implementation & Won": {"count": 0, "arr": 0.0}
    }
    for w in wkls:
        p_text = (w.get("workload_progress") or "").lower()
        arr = float(w.get("annual_gross_revenue") or 0.0)
        if "0-1" in p_text or "qualify" in p_text or "refine" in p_text or p_text.startswith("1."):
            stages_agg["00-01: Qualify & Refine"]["count"] += 1
            stages_agg["00-01: Qualify & Refine"]["arr"] += arr
        elif "0-2" in p_text or "tech eval" in p_text or "solution dev" in p_text or p_text.startswith("2."):
            stages_agg["02: Tech Eval / Solution Dev"]["count"] += 1
            stages_agg["02: Tech Eval / Solution Dev"]["arr"] += arr
        elif "3:" in p_text or "proposal" in p_text or "negotiation" in p_text or p_text.startswith("3."):
            stages_agg["03: Proposal & Negotiation"]["count"] += 1
            stages_agg["03: Proposal & Negotiation"]["arr"] += arr
        else:
            stages_agg["04+: Implementation & Won"]["count"] += 1
            stages_agg["04+: Implementation & Won"]["arr"] += arr

    # Partner aggregates
    partner_agg = {}
    for w in wkls:
        arr = float(w.get("annual_gross_revenue") or 0.0)
        if w.get("is_partnered") and w.get("partner_name"):
            pn = w.get("partner_name")
            if pn not in partner_agg:
                partner_agg[pn] = {"count": 0, "arr": 0.0}
            partner_agg[pn]["count"] += 1
            partner_agg[pn]["arr"] += arr
        else:
            if "⚠️ Unpartnered Deals" not in partner_agg:
                partner_agg["⚠️ Unpartnered Deals"] = {"count": 0, "arr": 0.0}
            partner_agg["⚠️ Unpartnered Deals"]["count"] += 1
            partner_agg["⚠️ Unpartnered Deals"]["arr"] += arr

    sorted_partners = sorted(partner_agg.items(), key=lambda x: x[1]["arr"], reverse=True)

    # High risk count
    high_risk_wkls = [w for w in wkls if prio_map.get(w.get("workload_id")) in ["High risk", "Critical Path"]]
    high_risk_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in high_risk_wkls)

    summary_rows = [
        [f"📊 EXECUTIVE SUMMARY & VELOCITY SCORECARD — {fsr_name.upper()}", "", "", "", "", "", ""],
        [f"FSR: {fsr_name} ({fsr_email}) | Supporting CE: {supporting_ce} | PE: {pe_name} | Last Update: {DATE_FORMATTED}", "", "", "", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["1. PORTFOLIO VITAL METRICS", "", "", "", "", "", ""],
        ["Metric", "Value", "Share / Detail", "Strategic Context", "", "", ""],
        ["Total Active Pipeline ARR", f"${total_arr:,.2f}", "100.0%", "Total commercial pipeline under active pursuit across all stages", "", "", ""],
        ["Total Active Workloads", str(len(wkls)), "100.0%", "Distinct workloads in Salesforce / Vector", "", "", ""],
        ["Partnered Workloads", str(len(partnered_wkls)), f"{(partnered_arr/total_arr*100) if total_arr else 0:.1f}% (${partnered_arr:,.2f})", "Deals with attached delivery partner supporting customer technical journey", "", "", ""],
        ["Unpartnered Workloads", str(len(unpartnered_wkls)), f"{(unpartnered_arr/total_arr*100) if total_arr else 0:.1f}% (${unpartnered_arr:,.2f})", "Deals requiring Brazil partner matchmaking to unblock architecture / delivery", "", "", ""],
        ["High Risk & Critical Path Deals", str(len(high_risk_wkls)), f"{(high_risk_arr/total_arr*100) if total_arr else 0:.1f}% (${high_risk_arr:,.2f})", "Priorizacion Q3 deals requiring urgent acceleration, pull-in, or hygiene review", "", "", ""],
        ["Dedicated Supporting CE", supporting_ce, "Lead CE Partner", "Primary Customer Engineering counterpart aligned to FSR pipeline", "", "", ""],
        ["", "", "", "", "", "", ""],
        ["2. PIPELINE BY COMMERCIAL PROGRESS STAGE", "", "", "", "", "", ""],
        ["Commercial Stage", "Stage Definition", "Workloads (#)", "Pipeline ARR ($ USD)", "ARR Share (%)", "Primary Acceleration Action", ""]
    ]

    actions_map = {
        "00-01: Qualify & Refine": "Complete discovery, align use case, introduce delivery partner early",
        "02: Tech Eval / Solution Dev": f"Accelerate architecture sizing, PoC validation with {supporting_ce}",
        "03: Proposal & Negotiation": "Finalize commercial proposal, commit validation, consumption pull-in",
        "04+: Implementation & Won": "Monitor go-live milestones, unblock technical delivery & support tickets"
    }

    for stg, s_data in stages_agg.items():
        s_cnt = s_data["count"]
        s_arr = s_data["arr"]
        pct = (s_arr / total_arr * 100) if total_arr > 0 else 0.0
        summary_rows.append([
            stg.split(":")[0],
            stg,
            str(s_cnt),
            f"${s_arr:,.2f}",
            f"{pct:.1f}%",
            actions_map.get(stg, ""),
            ""
        ])
    summary_rows.append([
        "TOTAL",
        "All Active Stages",
        str(len(wkls)),
        f"${total_arr:,.2f}",
        "100.0%",
        "Full Commercial Portfolio",
        ""
    ])

    summary_rows.extend([
        ["", "", "", "", "", "", ""],
        ["3. PARTNER ENGAGEMENT & DELIVERY CONCENTRATION", "", "", "", "", "", ""],
        ["Partner Organization", "Standing / Tier", "Workloads (#)", "Pipeline ARR ($ USD)", "ARR Share (%)", "Delivery Alignment", ""]
    ])

    for p_name, p_data in sorted_partners:
        p_cnt = p_data["count"]
        p_arr = p_data["arr"]
        p_pct = (p_arr / total_arr * 100) if total_arr > 0 else 0.0
        if "Unpartnered" in p_name:
            standing = "⚠️ No Partner Attached"
            align = "Immediate opportunity for partner matchmaking"
        else:
            standing = "Active Delivery Partner"
            align = "Co-selling & delivery tracking"
        summary_rows.append([
            p_name,
            standing,
            str(p_cnt),
            f"${p_arr:,.2f}",
            f"{p_pct:.1f}%",
            align,
            ""
        ])

    summary_rows.extend([
        ["", "", "", "", "", "", ""],
        ["4. TOP 10 STRATEGIC WORKLOADS (RANKED BY ARR)", "", "", "", "", "", ""],
        ["Workload Name", "Customer Account", "ARR ($ USD)", "Progress / Stage", "Partner Name", "Target Production Date", "Business Priority"]
    ])

    for top_w in wkls[:10]:
        t_wname = top_w.get("workload_name") or ""
        t_wid = top_w.get("workload_id") or ""
        t_aid = top_w.get("sfdc_account_id") or ""
        t_aname = top_w.get("account_name") or ""
        t_arr = float(top_w.get("annual_gross_revenue") or 0.0)
        t_prog = top_w.get("workload_progress") or ""
        t_pname = top_w.get("partner_name") if top_w.get("is_partnered") else "⚠️ Unpartnered"
        t_pdate = str(top_w.get("production_date") or "").strip()
        t_prio = prio_map.get(t_wid, "Normal")

        w_link = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Workload__c/{t_wid}/view", t_wname) if t_wid else t_wname
        a_link = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Account/{t_aid}/view", t_aname) if t_aid else t_aname

        summary_rows.append([
            w_link,
            a_link,
            f"${t_arr:,.2f}",
            t_prog,
            t_pname,
            t_pdate,
            t_prio
        ])

    summary_csv_path = os.path.join(out_dir, f"{fsr_user}_summary.csv")
    with open(summary_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(summary_rows)

    # -------------------------------------------------------------
    # 3. TAB 3: Unpartnered_Matchmaker CSV
    # -------------------------------------------------------------
    match_rows = [
        [f"🤝 UNPARTNERED DEALS & BRAZIL PARTNER MATCHMAKER — {fsr_name.upper()}", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["Deals lacking an attached delivery partner. Candidate Brazil partners ranked by certified DRP bench, product expertise, and delivery track record.", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        list(MATCHMAKER_HEADERS)
    ]

    for uw in unpartnered_wkls:
        uw_id = uw.get("workload_id") or ""
        uw_name = uw.get("workload_name") or ""
        uw_aid = uw.get("sfdc_account_id") or ""
        uw_aname = uw.get("account_name") or ""
        uw_opp_id = uw.get("opportunity_id") or ""
        uw_opp_name = uw.get("opportunity_name") or ""
        uw_arr = float(uw.get("annual_gross_revenue") or 0.0)
        uw_prog = uw.get("workload_progress") or ""
        uw_pillar = uw.get("pillar") or ""
        uw_prods = ", ".join(uw.get("key_workload_products") or []) or uw.get("workload_solutions") or "Cloud Architecture"
        uw_pdate = str(uw.get("production_date") or "").strip()
        uw_ns = (uw.get("next_steps") or "").replace("\r\n", " ").replace("\n", " ").strip()
        uw_tier = get_account_tier(uw_id, uw_aid, uw_aname, uw.get("segment"))

        acc_cell = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Account/{uw_aid}/view", uw_aname) if uw_aid else uw_aname
        wkl_cell = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Workload__c/{uw_id}/view", uw_name) if uw_id else uw_name
        opp_cell = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Opportunity/{uw_opp_id}/view", uw_opp_name) if uw_opp_id else uw_opp_name

        matches = match_partners_for_workload(uw, candidates)
        if len(matches) >= 1:
            p1 = matches[0]
            p1_name = p1["partner_name"]
            p1_bench = f"{p1['tier_level']} · T1: {p1['tier1_bench']}, T2: {p1['tier2_bench']} (Score: {p1['score']})"
            p1_logic = p1["selection_logic"]
        else:
            p1_name, p1_bench, p1_logic = "No Candidate Found", "-", "-"

        if len(matches) >= 2:
            p2 = matches[1]
            p2_name = p2["partner_name"]
            p2_bench = f"{p2['tier_level']} · T1: {p2['tier1_bench']}, T2: {p2['tier2_bench']} (Score: {p2['score']})"
            p2_logic = p2["selection_logic"]
        else:
            p2_name, p2_bench, p2_logic = "-", "-", "-"

        match_rows.append([
            acc_cell,
            uw_tier,
            wkl_cell,
            f"${uw_arr:,.2f}",
            uw_prog,
            uw_pillar,
            uw_prods,
            p1_name,
            p1_bench,
            p1_logic,
            p2_name,
            p2_bench,
            p2_logic,
            uw_pdate,
            opp_cell,
            uw_ns
        ])

    matchmaker_csv_path = os.path.join(out_dir, f"{fsr_user}_matchmaker.csv")
    with open(matchmaker_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(match_rows)

    return {
        "fsr_name": fsr_name,
        "fsr_email": fsr_email,
        "fsr_user": fsr_user,
        "fsr_title": fsr_title,
        "folder_id": folder_id,
        "pe_name": pe_name,
        "total_workloads": len(wkls),
        "total_arr": total_arr,
        "partnered_count": len(partnered_wkls),
        "unpartnered_count": len(unpartnered_wkls),
        "followup_csv": followup_csv_path,
        "summary_csv": summary_csv_path,
        "matchmaker_csv": matchmaker_csv_path,
        "followup_row_count": len(followup_rows),
        "summary_row_count": len(summary_rows),
        "matchmaker_row_count": len(match_rows),
        "true_tech_wins": true_tech_wins,
        "true_prop_sents": true_prop_sents
    }


def deploy_fsr_deck(deck_info):
    fsr_name = deck_info["fsr_name"]
    fsr_email = deck_info["fsr_email"]
    fsr_title = deck_info["fsr_title"]
    followup_csv = deck_info["followup_csv"]
    summary_csv = deck_info["summary_csv"]
    matchmaker_csv = deck_info["matchmaker_csv"]
    f_total_rows = deck_info["followup_row_count"]
    s_total_rows = deck_info["summary_row_count"]
    m_total_rows = deck_info["matchmaker_row_count"]
    target_folder_id = deck_info.get("folder_id", OLIVER_FOLDER_ID)
    pe_name = deck_info.get("pe_name", "Oliver Hartley")

    print(f"\n========================================================")
    print(f"Creating / Updating Spreadsheet for: {fsr_title}")
    print(f"========================================================")

    ssid = deck_info.get("ssid")
    if not ssid:
        # 1. Create Spreadsheet
        res = subprocess.check_output([GSHEETS, "mutate", "create", "--title", fsr_title]).decode("utf-8")
        m = re.search(r"ID:\s*([a-zA-Z0-9_\-]+)", res)
        if not m:
            raise RuntimeError(f"Could not parse sheet ID from: {res}")
        ssid = m.group(1)
        sheet_url = f"https://docs.google.com/spreadsheets/d/{ssid}/edit"
        print(f"Created: {ssid} ({sheet_url})")

        # 2. Move to PE's Folder
        print(f"Moving to {pe_name}'s Folder ({target_folder_id})...")
        subprocess.run([GDRIVE, "mutate", "mv", ssid, target_folder_id], capture_output=True)
    else:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{ssid}/edit"
        print(f"Updating existing spreadsheet: {ssid} ({sheet_url})")

    # 3. Ensure Tabs
    print("Setting up tabs: Follow_up, Executive_Summary, Unpartnered_Matchmaker...")
    sid_followup = ensure_tab(ssid, "Follow_up")
    sid_summary = ensure_tab(ssid, "Executive_Summary")
    sid_matchmaker = ensure_tab(ssid, "Unpartnered_Matchmaker")

    # Clear old data and delete old conditional formatting if existing spreadsheet
    if deck_info.get("ssid"):
        print("Clearing old data and conditional formatting...")
        subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Follow_up'!A1:AJ2000"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Executive_Summary'!A1:G500"], capture_output=True)
        subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Unpartnered_Matchmaker'!A1:P2000"], capture_output=True)

        try:
            res_info = subprocess.run([GSHEETS, "readonly", "info", ssid, "--json"], capture_output=True, text=True)
            if res_info.returncode == 0 and res_info.stdout.strip():
                info_data = json.loads(res_info.stdout)
                for s_item in info_data.get("sheets", []):
                    if s_item.get("properties", {}).get("sheetId", 0) == sid_followup:
                        cfs = s_item.get("conditionalFormats", [])
                        if cfs:
                            del_reqs = [{"deleteConditionalFormatRule": {"sheetId": sid_followup, "index": i}} for i in reversed(range(len(cfs)))]
                            tmp_cf = f"temp_del_cf_{ssid}.json"
                            with open(tmp_cf, "w") as df:
                                json.dump({"requests": del_reqs}, df)
                            subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_cf], capture_output=True)
                            if os.path.exists(tmp_cf):
                                os.remove(tmp_cf)
        except Exception as e:
            print(f"Warning clearing conditional formats: {e}")

    p_cols = len(FOLLOWUP_HEADERS)

    # Ensure Follow_up grid has at least p_cols columns, unhide all columns, and set Col 4 (Progress) as TEXT before CSV import
    prep_reqs = [
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sid_followup,
                    "gridProperties": {"columnCount": max(p_cols, 35)}
                },
                "fields": "gridProperties.columnCount"
            }
        },
        {
            "updateDimensionProperties": {
                "range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": 0, "endIndex": max(p_cols, 35)},
                "properties": {"hiddenByUser": False},
                "fields": "hiddenByUser"
            }
        },
        {
            "setDataValidation": {
                "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1000, "startColumnIndex": 0, "endColumnIndex": max(p_cols, 35)}
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": 1000, "startColumnIndex": 4, "endColumnIndex": 6},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": 1000, "startColumnIndex": 7, "endColumnIndex": 8},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        },
        {
            "repeatCell": {
                "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": 1000, "startColumnIndex": 9, "endColumnIndex": 10},
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        }
    ]
    tmp_exp = f"temp_exp_{ssid}.json"
    with open(tmp_exp, "w") as f:
        json.dump({"requests": prep_reqs}, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_exp], capture_output=True)
    if os.path.exists(tmp_exp):
        os.remove(tmp_exp)

    # 4. Import CSVs
    print(f"Importing Follow_up data ({p_cols} columns)...")
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, followup_csv, "--sheet", "Follow_up"], capture_output=True)

    print("Importing Executive_Summary data...")
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, summary_csv, "--sheet", "Executive_Summary"], capture_output=True)

    print("Importing Unpartnered_Matchmaker data...")
    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, matchmaker_csv, "--sheet", "Unpartnered_Matchmaker"], capture_output=True)

    # Cleanup default Sheet1 if exists
    cleanup_default_sheet(ssid)

    # Trim Follow_up columnCount to exactly p_cols (15)
    trim_req = {
        "requests": [{
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sid_followup,
                    "gridProperties": {"columnCount": p_cols}
                },
                "fields": "gridProperties.columnCount"
            }
        }]
    }
    tmp_trim = f"temp_trim_{ssid}.json"
    with open(tmp_trim, "w") as f:
        json.dump(trim_req, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_trim], capture_output=True)
    if os.path.exists(tmp_trim):
        os.remove(tmp_trim)

    # Fetch actual grid dimensions
    grid_info = get_grid_info(ssid)
    f_info = grid_info.get("Follow_up", {"sheetId": sid_followup, "rowCount": f_total_rows, "columnCount": p_cols})
    sid_followup = f_info["sheetId"]
    f_rows = max(f_total_rows, f_info["rowCount"])

    s_info = grid_info.get("Executive_Summary", {"sheetId": sid_summary, "rowCount": s_total_rows, "columnCount": 7})
    sid_summary = s_info["sheetId"]
    s_rows = max(s_total_rows, s_info["rowCount"])

    m_info = grid_info.get("Unpartnered_Matchmaker", {"sheetId": sid_matchmaker, "rowCount": m_total_rows, "columnCount": 16})
    sid_matchmaker = m_info["sheetId"]
    m_rows = max(m_total_rows, m_info["rowCount"])
    m_cols = 16

    # -------------------------------------------------------------
    # 5. Format Follow_up Tab (15 columns, minimal formatting)
    # -------------------------------------------------------------
    print("Formatting Follow_up tab...")
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_followup), "--rows", "5"], capture_output=True)

    batch_followup = {
        "requests": [
            # Reset all cell styles across entire sheet (white fill, plain black text, no underline, no bold)
            {
                "repeatCell": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "fontSize": 10, "bold": False, "underline": False, "fontFamily": "Arial"},
                            "horizontalAlignment": "LEFT",
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "CLIP"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
                }
            },
            # Clear all borders across entire sheet
            {
                "updateBorders": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
                    "top": {"style": "NONE"},
                    "bottom": {"style": "NONE"},
                    "left": {"style": "NONE"},
                    "right": {"style": "NONE"},
                    "innerHorizontal": {"style": "NONE"},
                    "innerVertical": {"style": "NONE"}
                }
            },
            # Unmerge top rows (clears merges on rows 1-10)
            {"unmergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": min(10, f_rows), "startColumnIndex": 0, "endColumnIndex": p_cols}}},
            # Maintain Row 1 merge & formatting
            {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.95, "green": 0.91, "blue": 0.99}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.41, "green": 0.11, "blue": 0.66}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Row 5 Main Header (Cols 0 to 14): Google Blue header
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": p_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

            # Row 3 Alert Banner: Notice on row 3 alerting users of stage 4.3 removal & Opportunity Stage addition
            {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": p_cols}, "mergeType": "MERGE_ALL"}},
            {
                "repeatCell": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 0, "endColumnIndex": p_cols},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 0.949, "blue": 0.800},
                            "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 0.58, "green": 0.35, "blue": 0.0}},
                            "horizontalAlignment": "LEFT",
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "CLIP"
                        },
                        "note": "Workloads in stage 4.3 (Migrated/Implemented) have been removed. Added new field 'Opportunity Stage' between ARR and Workload Progress."
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy),note"
                }
            },

            # Data types only (no colors or cell borders on data rows):
            # Col 3 (D): ARR USD Currency
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat.numberFormat"}},
            # Col 4 (E): Opportunity Stage as TEXT (Center aligned)
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}},
            # Col 5 (F): Workload Progress as plain TEXT so '0-2' is never parsed as a date (Center aligned)
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}},
            # Col 7 (H) & Col 9 (J): Days Until Implementation / Production as integer
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}}, "fields": "userEnteredFormat.numberFormat"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 9, "endColumnIndex": 10}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}}, "fields": "userEnteredFormat.numberFormat"}},
            # Col 10 (K): Cual es el bloqueo? dropdown (Comercial, Tecnico)
            {
                "setDataValidation": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 10, "endColumnIndex": 11},
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": "Comercial"},
                                {"userEnteredValue": "Tecnico"}
                            ]
                        },
                        "showCustomUi": True,
                        "strict": False
                    }
                }
            },
            # Col 18 (S) & Col 19 (T): Checkboxes for 'Technical win' and 'Propousal sent to client'
            {
                "setDataValidation": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 18, "endColumnIndex": 20},
                    "rule": {
                        "condition": {
                            "type": "BOOLEAN"
                        },
                        "showCustomUi": True,
                        "strict": False
                    }
                }
            },
            {
                "repeatCell": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 18, "endColumnIndex": 20},
                    "cell": {
                        "userEnteredValue": {"boolValue": False},
                        "userEnteredFormat": {
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredValue,userEnteredFormat(horizontalAlignment,verticalAlignment)"
                }
            },

            # Basic Filter on Row 5
            {"clearBasicFilter": {"sheetId": sid_followup}},
            {"setBasicFilter": {"filter": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols}}}},

            # Standard Row Heights
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_followup, "dimension": "ROWS", "startIndex": 5, "endIndex": f_rows}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}},
        ]
    }

    # Column widths for Follow_up (15 columns)
    for c_idx, width in FOLLOWUP_COL_WIDTHS.items():
        batch_followup["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": c_idx, "endIndex": c_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    # Re-apply any true boolean values for checkboxes
    for r_idx in deck_info.get("true_tech_wins", []):
        batch_followup["requests"].append({
            "updateCells": {
                "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 18, "endColumnIndex": 19},
                "rows": [{"values": [{"userEnteredValue": {"boolValue": True}}]}],
                "fields": "userEnteredValue"
            }
        })
    for r_idx in deck_info.get("true_prop_sents", []):
        batch_followup["requests"].append({
            "updateCells": {
                "range": {"sheetId": sid_followup, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 19, "endColumnIndex": 20},
                "rows": [{"values": [{"userEnteredValue": {"boolValue": True}}]}],
                "fields": "userEnteredValue"
            }
        })

    # Copy-paste activation of interactive hyperlinks
    batch_followup["requests"].append({
        "copyPaste": {
            "source": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
            "destination": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
            "pasteType": "PASTE_NORMAL",
            "pasteOrientation": "NORMAL"
        }
    })

    tmp_b_followup = f"temp_batch_f_{ssid}.json"
    with open(tmp_b_followup, "w") as f:
        json.dump(batch_followup, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_b_followup], capture_output=True)
    if os.path.exists(tmp_b_followup):
        os.remove(tmp_b_followup)
    print("✓ Follow_up tab formatted.")

    # -------------------------------------------------------------
    # 6. Format Executive_Summary Tab
    # -------------------------------------------------------------
    print("Formatting Executive_Summary tab...")
    batch_summary = {
        "requests": [
            # Reset cell styles
            {
                "repeatCell": {
                    "range": {"sheetId": sid_summary, "startRowIndex": 0, "endRowIndex": s_rows, "startColumnIndex": 0, "endColumnIndex": 7},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"},
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "CLIP"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
                }
            },
            # Row 1: Main Title
            {"mergeCells": {"range": {"sheetId": sid_summary, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Row 2: Subtitle
            {"mergeCells": {"range": {"sheetId": sid_summary, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Section 1 Header (Row 4)
            {"mergeCells": {"range": {"sheetId": sid_summary, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Section 1 Subheader (Row 5)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.93, "green": 0.95, "blue": 0.98}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            # Metric labels bold
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 5, "endRowIndex": 11, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}}, "fields": "userEnteredFormat.textFormat(bold)"}},
            # Metric values bold blue
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 5, "endRowIndex": 11, "startColumnIndex": 1, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},

            # Section 2 Header (Row 13)
            {"mergeCells": {"range": {"sheetId": sid_summary, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 12, "endRowIndex": 13, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            # Section 2 Subheader (Row 14)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 13, "endRowIndex": 14, "startColumnIndex": 0, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.93, "green": 0.95, "blue": 0.98}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Total row in Stage (Row 19)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 18, "endRowIndex": 19, "startColumnIndex": 0, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},

            # Section 3 Header (Row 21)
            {"mergeCells": {"range": {"sheetId": sid_summary, "startRowIndex": 20, "endRowIndex": 21, "startColumnIndex": 0, "endColumnIndex": 7}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 20, "endRowIndex": 21, "startColumnIndex": 0, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            # Section 3 Subheader (Row 22)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 21, "endRowIndex": 22, "startColumnIndex": 0, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.93, "green": 0.95, "blue": 0.98}, "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Borders across tables
            {
                "updateBorders": {
                    "range": {"sheetId": sid_summary, "startRowIndex": 3, "endRowIndex": s_rows, "startColumnIndex": 0, "endColumnIndex": 7},
                    "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
                    "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
                }
            }
        ]
    }

    # Column widths for Summary
    for c_idx, width in SUMMARY_COL_WIDTHS.items():
        batch_summary["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_summary, "dimension": "COLUMNS", "startIndex": c_idx, "endIndex": c_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    tmp_b_summary = f"temp_batch_s_{ssid}.json"
    with open(tmp_b_summary, "w") as f:
        json.dump(batch_summary, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_b_summary], capture_output=True)
    if os.path.exists(tmp_b_summary):
        os.remove(tmp_b_summary)
    print("✓ Executive_Summary tab formatted.")

    # -------------------------------------------------------------
    # 7. Format Unpartnered_Matchmaker Tab
    # -------------------------------------------------------------
    print("Formatting Unpartnered_Matchmaker tab...")
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_matchmaker), "--rows", "4"], capture_output=True)

    batch_matchmaker = {
        "requests": [
            # Reset styles
            {
                "repeatCell": {
                    "range": {"sheetId": sid_matchmaker, "startRowIndex": 0, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": m_cols},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "fontSize": 10, "bold": False, "fontFamily": "Arial"},
                            "verticalAlignment": "MIDDLE",
                            "wrapStrategy": "CLIP"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"
                }
            },
            # Row 1: Title
            {"mergeCells": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": m_cols}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": m_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Row 2: Subtitle
            {"mergeCells": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": m_cols}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": m_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Row 4: Header row
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": m_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

            # Left align: Account (0), Workload (2), Logic 1 (9), Logic 2 (12), Opp (14), Next Steps (15)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "textFormat": {"bold": True}, "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,textFormat,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 9, "endColumnIndex": 10}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 10, "endColumnIndex": 11}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "textFormat": {"bold": True}, "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,textFormat,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 12, "endColumnIndex": 13}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 14, "endColumnIndex": 16}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},

            # Center align: Tier (1), Progress (4), Pillar (5), Bench (8, 11), Prod Date (13)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 1, "endColumnIndex": 2}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 4, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 8, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 11, "endColumnIndex": 12}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 13, "endColumnIndex": 14}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}},

            # Currency Format: ARR (Col 3)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 3, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "wrapStrategy": "CLIP", "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy,numberFormat)"}},

            # Hyperlinks styling
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 2, "endColumnIndex": 3}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 14, "endColumnIndex": 15}, "cell": {"userEnteredFormat": {"textFormat": {"underline": True, "foregroundColor": {"red": 0.0667, "green": 0.3333, "blue": 0.8000}}}}, "fields": "userEnteredFormat.textFormat(underline,foregroundColor)"}},

            # Borders
            {
                "updateBorders": {
                    "range": {"sheetId": sid_matchmaker, "startRowIndex": 3, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": m_cols},
                    "top": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "bottom": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "left": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "right": {"style": "SOLID", "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                    "innerHorizontal": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
                    "innerVertical": {"style": "SOLID", "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
                }
            },

            # Basic Filter
            {"clearBasicFilter": {"sheetId": sid_matchmaker}},
            {"setBasicFilter": {"filter": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 3, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": m_cols}}}},

            # Row heights
            {"updateDimensionProperties": {"range": {"sheetId": sid_matchmaker, "dimension": "ROWS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 30}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_matchmaker, "dimension": "ROWS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_matchmaker, "dimension": "ROWS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 8}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_matchmaker, "dimension": "ROWS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 36}, "fields": "pixelSize"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid_matchmaker, "dimension": "ROWS", "startIndex": 4, "endIndex": m_rows}, "properties": {"pixelSize": 28}, "fields": "pixelSize"}}
        ]
    }

    # Zebra striping on Matchmaker
    for r_idx in range(4, m_rows):
        if r_idx % 2 == 1:
            batch_matchmaker["requests"].append({
                "repeatCell": {
                    "range": {"sheetId": sid_matchmaker, "startRowIndex": r_idx, "endRowIndex": r_idx + 1, "startColumnIndex": 0, "endColumnIndex": m_cols},
                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}}},
                    "fields": "userEnteredFormat(backgroundColor)"
                }
            })

    # Column widths on Matchmaker
    for c_idx, width in MATCHMAKER_COL_WIDTHS.items():
        batch_matchmaker["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_matchmaker, "dimension": "COLUMNS", "startIndex": c_idx, "endIndex": c_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    # Copy-paste activation of interactive hyperlinks
    batch_matchmaker["requests"].append({
        "copyPaste": {
            "source": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": m_cols},
            "destination": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": m_cols},
            "pasteType": "PASTE_NORMAL",
            "pasteOrientation": "NORMAL"
        }
    })

    tmp_b_matchmaker = f"temp_batch_m_{ssid}.json"
    with open(tmp_b_matchmaker, "w") as f:
        json.dump(batch_matchmaker, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_b_matchmaker], capture_output=True)
    if os.path.exists(tmp_b_matchmaker):
        os.remove(tmp_b_matchmaker)
    print("✓ Unpartnered_Matchmaker tab formatted.")

    return {
        "title": fsr_title,
        "fsr_name": fsr_name,
        "fsr_email": fsr_email,
        "ssid": ssid,
        "url": sheet_url,
        "total_workloads": deck_info["total_workloads"],
        "total_arr": deck_info["total_arr"],
        "partnered_count": deck_info["partnered_count"],
        "unpartnered_count": deck_info["unpartnered_count"]
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Update Brazil FSR Action Trackers")
    parser.add_argument("--fsr", type=str, default=None, help="Filter by FSR name, username, or email (e.g. robertacoelho)")
    args = parser.parse_args()

    print("=================================================================")
    print("🚀 Updating Brazil FSR Action Trackers ('Decks') with 20 Columns")
    print("=================================================================")

    os.makedirs("fsr_decks_data", exist_ok=True)

    cache_file = "data/portfolio_cache.json"
    prio_file = "priorizacion_q3_statuses.json"
    user_file = "data/workload_user_data.json"

    if not os.path.exists(cache_file):
        raise FileNotFoundError(f"Portfolio cache not found at: {cache_file}")

    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)

    prio_map = {}
    if os.path.exists(prio_file):
        with open(prio_file, "r", encoding="utf-8") as f:
            prio_map = json.load(f)

    user_data = {}
    if os.path.exists(user_file):
        with open(user_file, "r", encoding="utf-8") as f:
            user_data = json.load(f)

    existing_trackers = {}
    existing_tracker_objs = {}
    if os.path.exists("fsr_trackers.json"):
        try:
            with open("fsr_trackers.json", "r", encoding="utf-8") as tf:
                t_list = json.load(tf)
                for t in t_list:
                    if "fsr_email" in t and "ssid" in t:
                        existing_trackers[t["fsr_email"]] = t["ssid"]
                        existing_tracker_objs[t["fsr_email"]] = t
        except Exception:
            pass

    # 1. Reconcile live Google Sheets and local Web UI state via 3-way bidirectional sync
    print("\n>>> Running 3-way bidirectional reconciliation between Google Sheets and Web UI cache...")
    try:
        from sync_engine import sync_bidirectional
        sync_info = sync_bidirectional(fsr_filter=args.fsr)
        print(f"Reconciled: {sync_info.get('pulled_count', 0)} pulled from Sheets, {sync_info.get('pushed_count', 0)} pushed from Web UI.")
    except Exception as e:
        print(f"Warning running pre-build sync_bidirectional: {e}")

    # Reload reconciled manual_entries and user_data
    all_manual_entries = {}
    manual_cache_file = "fsr_manual_entries.json"
    if os.path.exists(manual_cache_file):
        try:
            with open(manual_cache_file, "r", encoding="utf-8") as mf:
                all_manual_entries = json.load(mf)
        except Exception:
            all_manual_entries = {}

    if os.path.exists(user_file):
        try:
            with open(user_file, "r", encoding="utf-8") as uf:
                user_data = json.load(uf)
        except Exception:
            pass

    results = []

    for cfg in FSR_CONFIGS:
        fsr_mail = cfg["email"]
        if args.fsr:
            q = args.fsr.lower().strip()
            if q not in cfg["name"].lower() and q not in cfg["username"].lower() and q not in fsr_mail.lower():
                if fsr_mail in existing_tracker_objs:
                    results.append(existing_tracker_objs[fsr_mail])
                continue

        target_ssid = cfg.get("ssid") or existing_trackers.get(fsr_mail)
        cfg["ssid"] = target_ssid

        print(f">>> Preparing CSV datasets for {cfg['name']} ({cfg['email']})...")
        deck_info = build_fsr_deck(cfg, cache, prio_map, user_data, existing_manual=all_manual_entries)
        deck_info["ssid"] = target_ssid
        print(f"Generated CSVs: Follow_up ({deck_info['total_workloads']} deals, {len(FOLLOWUP_HEADERS)} cols), Summary, Matchmaker ({deck_info['unpartnered_count']} unpartnered deals).")

        deploy_res = deploy_fsr_deck(deck_info)
        results.append(deploy_res)
        time.sleep(3)

    # Save summary mapping & manual entries to files
    out_manifest = "fsr_trackers.json"
    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(manual_cache_file, "w", encoding="utf-8") as mf:
        json.dump(all_manual_entries, mf, indent=2, ensure_ascii=False)

    try:
        from copilot_engine import enrich_portfolio_cache
        from sync_engine import sync_drive_json_caches
        enrich_portfolio_cache()
        sync_drive_json_caches()
        print("✓ Enriched portfolio cache and Google Drive Web App JSON caches updated.")
    except Exception as e:
        print(f"Warning updating enriched portfolio / Drive cache: {e}")

    print("\n=================================================================")
    print("🎉 FSR ACTION TRACKER(S) UPDATED!")
    print("=================================================================")
    for r in results:
        print(f"- {r['title']}: {r['url']}")
        print(f"  Workloads: {r['total_workloads']} | Pipeline: ${r['total_arr']:,.2f}")

    return results


if __name__ == "__main__":
    main()
