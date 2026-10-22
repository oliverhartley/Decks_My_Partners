#!/usr/bin/env python3
"""
build_oliver_fsr_rollup.py
Generates and formats the consolidated FSR Rollup Management Dashboard
for Oliver Hartley (PE) & Diego Baldini (CE), covering all 4 assigned Brazil FSRs:
1. Felipe Pilon (fpilon@google.com)
2. Roberta Coelho (robertacoelho@google.com)
3. Vanessa Moyses (vmmoyses@google.com)
4. Ana Luiza Gama (anagama@google.com)

Spreadsheet ID: 1JbaDkmltkqu6aaAKRszEwVFRsJxUSCofCWUKtwcjAhs
Drive Folder: 1WG2zMHJXRU8HnSCVR2cTN_5KeAUm5kQ3
"""

import os
import sys
import json
import csv
import re
import time
import subprocess

BASE_DIR = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners"
sys.path.insert(0, BASE_DIR)
os.environ["GOOGLE_CLOUD_PROJECT"] = "ohl-ge-demo-gen"

from create_fsr_decks import (
    make_hyperlink, get_account_tier, match_partners_for_workload,
    get_ai_next_steps_summary, get_grid_info, norm_str,
    DATE_FORMATTED, AI_SUMMARIES_FILE
)

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GDRIVE = "/google/bin/releases/gemini-agents-gdrive/gdrive"

ROLLUP_SSID = "1JbaDkmltkqu6aaAKRszEwVFRsJxUSCofCWUKtwcjAhs"
OLIVER_FOLDER_ID = "1WG2zMHJXRU8HnSCVR2cTN_5KeAUm5kQ3"

OLIVER_FSRS = [
    {
        "name": "Felipe Pilon",
        "email": "fpilon@google.com",
        "username": "fpilon",
        "ssid": "1gS9JWRb-aReMKOiJzhlKEu0TFTb4fF8fNROcTKWf7jU"
    },
    {
        "name": "Roberta Coelho",
        "email": "robertacoelho@google.com",
        "username": "robertacoelho",
        "ssid": "1wBiY2bqGo-NJaVeET6g8GRKfOTMDkQaSUhbD5xPfb5M"
    },
    {
        "name": "Vanessa Moyses",
        "email": "vmmoyses@google.com",
        "username": "vmmoyses",
        "ssid": "1UXbDWQNf1_wvm6_WHtKX2QIWXzRgib_xMpMGfnu5nKg"
    },
    {
        "name": "Ana Luiza Gama",
        "email": "anagama@google.com",
        "username": "anagama",
        "ssid": "1VMLeUmBjnucCwW98Z4ElVdusQSOhQgIrWrKlQOGeZdA"
    }
]

FOLLOWUP_HEADERS = [
    "FSR Name",                         # Col 0 (A)
    "Customer Account Name",            # Col 1 (B)
    "Opportunity Name",                 # Col 2 (C)
    "Workload Name",                    # Col 3 (D)
    "Annual Gross Revenue (ARR USD)",   # Col 4 (E)
    "Opportunity Stage",                # Col 5 (F)
    "Workload Progress",                # Col 6 (G)
    "Implementation Date",              # Col 7 (H)
    "Days Until Implementation",        # Col 8 (I)
    "Production Date",                  # Col 9 (J)
    "Days Until Production",            # Col 10 (K)
    "Cual es el bloqueo?",              # Col 11 (L)
    "Status Tecnico",                   # Col 12 (M)
    "AI Summary Next Steps",            # Col 13 (N)
    "Opportunity Partner",              # Col 14 (O)
    "Workload Partner",                 # Col 15 (P)
    "Workload Owner Email",             # Col 16 (Q)
    "Primary CE Technical Owner Email", # Col 17 (R)
    "Partner Technical Contact",        # Col 18 (S)
    "Client Technical Contact",         # Col 19 (T)
    "Technical win",                    # Col 20 (U)
    "Propousal sent to client"          # Col 21 (V)
]

FOLLOWUP_COL_WIDTHS = {
    0: 160,  # FSR Name
    1: 260,  # Customer Account Name
    2: 260,  # Opportunity Name
    3: 260,  # Workload Name
    4: 150,  # ARR USD
    5: 170,  # Opportunity Stage
    6: 130,  # Workload Progress
    7: 140,  # Implementation Date
    8: 140,  # Days Until Implementation
    9: 130,  # Production Date
    10: 140, # Days Until Production
    11: 160, # Cual es el bloqueo?
    12: 300, # Status Tecnico
    13: 350, # AI Summary Next Steps
    14: 250, # Opportunity Partner
    15: 250, # Workload Partner
    16: 200, # Workload Owner Email
    17: 200, # Primary CE Technical Owner Email
    18: 240, # Partner Technical Contact
    19: 240, # Client Technical Contact
    20: 130, # Technical win
    21: 170  # Propousal sent to client
}

MATCHMAKER_HEADERS = [
    "FSR Name",                         # Col 0 (A)
    "Customer Account Name",            # Col 1 (B)
    "Account Tier",                     # Col 2 (C)
    "Workload Name",                    # Col 3 (D)
    "Annual Gross Revenue (ARR USD)",   # Col 4 (E)
    "Opportunity Stage",                # Col 5 (F)
    "Workload Progress",                # Col 6 (G)
    "Primary Pillar",                   # Col 7 (H)
    "Key Products / Solution",          # Col 8 (I)
    "Opportunity Partner",              # Col 9 (J)
    "Top Proposed Partner 1",           # Col 10 (K)
    "Partner 1 Standing & Bench",       # Col 11 (L)
    "Partner 1 Selection Logic",        # Col 12 (M)
    "Alternative Partner 2",            # Col 13 (N)
    "Partner 2 Standing & Bench",       # Col 14 (O)
    "Partner 2 Selection Logic",        # Col 15 (P)
    "Target Production Date",           # Col 16 (Q)
    "Opportunity Name",                 # Col 17 (R)
    "Next Steps"                        # Col 18 (S)
]

MATCHMAKER_COL_WIDTHS = {
    0: 150,  # FSR Name
    1: 280,  # Customer Account Name
    2: 90,   # Account Tier
    3: 260,  # Workload Name
    4: 150,  # ARR USD
    5: 170,  # Opportunity Stage
    6: 130,  # Workload Progress
    7: 150,  # Primary Pillar
    8: 260,  # Key Products / Solution
    9: 250,  # Opportunity Partner
    10: 220, # Top Proposed Partner 1
    11: 220, # Partner 1 Standing & Bench
    12: 300, # Partner 1 Selection Logic
    13: 220, # Alternative Partner 2
    14: 220, # Partner 2 Standing & Bench
    15: 300, # Partner 2 Selection Logic
    16: 140, # Target Production Date
    17: 240, # Opportunity Name
    18: 350  # Next Steps
}


def ensure_tab(ssid, tab_title):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
            for s in sheets:
                if s.get("title") in ["Sheet1", "Hoja 1", "Página1", "Página 1", "Sheet 1"]:
                    subprocess.run([GSHEETS, "mutate", "rename-sheet", ssid, "--sheet-id", str(s.get("id")), "--title", tab_title], capture_output=True)
                    return s.get("id")
        except Exception:
            pass
    subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    res2 = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            sheets = json.loads(res2.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except Exception:
            pass
    return 0


def build_rollup_datasets(cache, prio_map, user_data, manual_entries, ai_cache):
    all_workloads = cache.get("fsr_workloads", [])
    candidate_partners = cache.get("candidate_partners", [])

    # Filter for Oliver's 4 FSRs
    fsr_user_map = {f["username"]: f["name"] for f in OLIVER_FSRS}
    fsr_name_map = {norm_str(f["name"]): f["name"] for f in OLIVER_FSRS}

    oliver_wkls = []
    for w in all_workloads:
        # Enforce 2026 H2 onwards filter (>= 2026-07-01)
        if (w.get("begin_migration_date") or "") < "2026-07-01":
            continue
        u = (w.get("workload_owner_username") or "").lower()
        n = norm_str(w.get("workload_owner_name") or "")
        assigned_fsr = None
        if u in fsr_user_map:
            assigned_fsr = fsr_user_map[u]
        elif n in fsr_name_map:
            assigned_fsr = fsr_name_map[n]
        if assigned_fsr:
            w_copy = dict(w)
            w_copy["assigned_fsr"] = assigned_fsr
            oliver_wkls.append(w_copy)

    # Sort all workloads by ARR descending
    oliver_wkls.sort(key=lambda x: -float(x.get("annual_gross_revenue") or 0.0))

    partnered_wkls = [w for w in oliver_wkls if w.get("is_partnered")]
    unpartnered_wkls = [w for w in oliver_wkls if not w.get("is_partnered")]
    unpartnered_wkls.sort(key=lambda x: -float(x.get("annual_gross_revenue") or 0.0))

    total_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in oliver_wkls)
    partnered_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in partnered_wkls)
    unpartnered_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in unpartnered_wkls)

    # -------------------------------------------------------------
    # 1. TAB 1: Follow_up CSV (21 Columns)
    # -------------------------------------------------------------
    num_cols = len(FOLLOWUP_HEADERS)
    r1 = ["Team:", "Oliver Hartley FSR Team (Pilon, Coelho, Moyses, Gama)", "", "", "Supporting CE:", "Diego Baldini", "Last Update:", DATE_FORMATTED] + [""] * (num_cols - 8)
    r2 = [""] * num_cols
    alert_text = "📢 UPDATE: Consolidated rollup across all 4 Oliver Hartley FSRs (317 workloads, $45.30M ARR). Workloads in stage 4.3 (Migrated/Implemented) are included."
    r3 = [alert_text] + [""] * (num_cols - 1)
    r4 = [""] * num_cols
    r5 = list(FOLLOWUP_HEADERS)

    followup_rows = [r1, r2, r3, r4, r5]
    true_tech_wins = []
    true_prop_sents = []
    ai_cache_dirty = False

    for idx, w in enumerate(oliver_wkls):
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
        fsr_label = w.get("assigned_fsr") or "Oliver Hartley FSR"

        # Hyperlinks
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

        owner_user = w.get("workload_owner_username") or ""
        owner_email = f"{owner_user}@google.com" if owner_user and "@" not in owner_user else owner_user

        ce_user = w.get("primary_ce_username") or "diegobaldini"
        ce_email = f"{ce_user}@google.com" if "@" not in ce_user else ce_user

        impl_date = str(w.get("begin_migration_date") or "").strip()
        prod_date = str(w.get("production_date") or "").strip()

        # Implementation Date is Col H (index 7), Production Date is Col J (index 9)
        days_impl = f'=IF(H{row_num}<>"", H{row_num}-TODAY(), "")'
        days_prod = f'=IF(J{row_num}<>"", J{row_num}-TODAY(), "")'

        # Notes / User Data
        m_entry = manual_entries.get(wid) or manual_entries.get(wname, {})
        u_info = user_data.get(wid, {})

        blocker_val = m_entry.get("blocker") or u_info.get("blocker_tecnico") or ""
        status_tecnico_val = m_entry.get("status_tecnico") or u_info.get("status_tecnico") or ""
        partner_tech_val = (
            m_entry.get("partner_tech_contact")
            or m_entry.get("partner_tech_email")
            or u_info.get("partner_technical_contact")
            or u_info.get("partner_technical_email")
            or w.get("partner_technical_contact")
            or w.get("partner_technical_email")
            or ""
        )
        if partner_tech_val and "@" in partner_tech_val and "(" not in partner_tech_val:
            p_name = w.get("partner_technical_name") or ""
            if p_name:
                partner_tech_val = f"{p_name} ({partner_tech_val})"

        client_tech_val = (
            m_entry.get("client_tech_contact")
            or u_info.get("client_technical_contact")
            or w.get("client_technical_contact")
            or ""
        )

        def to_bool(val):
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.strip().lower() in ["true", "1", "yes", "checked", "x"]
            return False

        is_tech_win = to_bool(m_entry.get("technical_win")) or to_bool(u_info.get("technical_win"))
        is_prop_sent = to_bool(m_entry.get("proposal_sent")) or to_bool(u_info.get("proposal_sent"))

        tech_win_val = "TRUE" if is_tech_win else "FALSE"
        prop_sent_val = "TRUE" if is_prop_sent else "FALSE"

        if is_tech_win:
            true_tech_wins.append(row_num - 1)
        if is_prop_sent:
            true_prop_sents.append(row_num - 1)

        ai_summary_val, updated_ai = get_ai_next_steps_summary(w, ai_cache)
        if updated_ai:
            ai_cache_dirty = True

        row_data = [
            fsr_label,                  # 0 (A): FSR Name
            acc_cell,                   # 1 (B): Customer Account Name
            opp_cell,                   # 2 (C): Opportunity Name
            wkl_cell,                   # 3 (D): Workload Name
            f"${arr_val:,.2f}",         # 4 (E): ARR USD
            opp_stage,                  # 5 (F): Opportunity Stage
            prog_short,                 # 6 (G): Workload Progress
            impl_date,                  # 7 (H): Implementation Date
            days_impl,                  # 8 (I): Days Until Implementation
            prod_date,                  # 9 (J): Production Date
            days_prod,                  # 10 (K): Days Until Production
            blocker_val,                # 11 (L): Cual es el bloqueo?
            status_tecnico_val,         # 12 (M): Status Tecnico
            ai_summary_val,             # 13 (N): AI Summary Next Steps
            opp_partner_cell,           # 14 (O): Opportunity Partner
            wkl_partner_cell,           # 15 (P): Workload Partner
            owner_email,                # 16 (Q): Workload Owner Email
            ce_email,                   # 17 (R): Primary CE Technical Owner Email
            partner_tech_val,           # 18 (S): Partner Technical Contact
            client_tech_val,            # 19 (T): Client Technical Contact
            tech_win_val,               # 20 (U): Technical win (Checkbox)
            prop_sent_val               # 21 (V): Propousal sent to client (Checkbox)
        ]
        followup_rows.append(row_data)

    if ai_cache_dirty:
        with open(AI_SUMMARIES_FILE, "w", encoding="utf-8") as af:
            json.dump(ai_cache, af, indent=2, ensure_ascii=False)

    out_followup_csv = os.path.join(BASE_DIR, "fsr_decks_data", "rollup_oliver_followup.csv")
    with open(out_followup_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(followup_rows)

    # -------------------------------------------------------------
    # 2. TAB 2: Executive_Summary CSV
    # -------------------------------------------------------------
    summary_rows = [
        ["📊 EXECUTIVE SUMMARY & ROLLUP SCORECARD — OLIVER HARTLEY FSR PORTFOLIO", "", "", "", "", "", "", "", "", "", ""],
        [f"Partner Engineer (PE): Oliver Hartley | Supporting CE: Diego Baldini | Scope: Felipe Pilon, Roberta Coelho, Vanessa Moyses, Ana Luiza Gama | Last Update: {DATE_FORMATTED}", "", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", ""],
        ["1. FSR PORTFOLIO OVERVIEW & PERFORMANCE", "", "", "", "", "", "", "", "", "", ""],
        [
            "FSR Name",
            "Supporting CE",
            "FSR Email",
            "Total Workloads (#)",
            "Total Pipeline ARR ($ USD)",
            "Partnered Workloads (#)",
            "Partnered ARR ($ USD)",
            "Unpartnered Workloads (#)",
            "Unpartnered ARR ($ USD)",
            "% Partnered (ARR)",
            "Individual Action Tracker Spreadsheet"
        ]
    ]

    for f_cfg in OLIVER_FSRS:
        f_name = f_cfg["name"]
        f_user = f_cfg["username"]
        f_mail = f_cfg["email"]
        f_ssid = f_cfg["ssid"]
        f_wkls = [w for w in oliver_wkls if w.get("assigned_fsr") == f_name]
        f_part = [w for w in f_wkls if w.get("is_partnered")]
        f_unpart = [w for w in f_wkls if not w.get("is_partnered")]
        f_total_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in f_wkls)
        f_part_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in f_part)
        f_unpart_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in f_unpart)
        f_pct = (f_part_arr / f_total_arr * 100) if f_total_arr > 0 else 0.0

        tracker_link = make_hyperlink(f"https://docs.google.com/spreadsheets/d/{f_ssid}/edit", "Open FSR Tracker ↗")
        summary_rows.append([
            f_name,
            "Diego Baldini",
            f_mail,
            str(len(f_wkls)),
            f"${f_total_arr:,.2f}",
            str(len(f_part)),
            f"${f_part_arr:,.2f}",
            str(len(f_unpart)),
            f"${f_unpart_arr:,.2f}",
            f"{f_pct:.1f}%",
            tracker_link
        ])

    tot_part_pct = (partnered_arr / total_arr * 100) if total_arr > 0 else 0.0
    summary_rows.append([
        "TOTAL (All 4 FSRs)",
        "Diego Baldini",
        "oliverhartley@google.com",
        str(len(oliver_wkls)),
        f"${total_arr:,.2f}",
        str(len(partnered_wkls)),
        f"${partnered_arr:,.2f}",
        str(len(unpartnered_wkls)),
        f"${unpartnered_arr:,.2f}",
        f"{tot_part_pct:.1f}%",
        "-"
    ])

    # Commercial stage aggregates
    stages_agg = {
        "00-01: Qualify & Refine": {"count": 0, "arr": 0.0},
        "02: Tech Eval / Solution Dev": {"count": 0, "arr": 0.0},
        "03: Proposal & Negotiation": {"count": 0, "arr": 0.0},
        "04+: Implementation & Won": {"count": 0, "arr": 0.0}
    }
    for w in oliver_wkls:
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

    actions_map = {
        "00-01: Qualify & Refine": "Complete discovery, align use case, introduce delivery partner early",
        "02: Tech Eval / Solution Dev": "Accelerate architecture sizing, PoC validation with Diego Baldini",
        "03: Proposal & Negotiation": "Finalize commercial proposal, commit validation, consumption pull-in",
        "04+: Implementation & Won": "Monitor go-live milestones, unblock technical delivery & support tickets"
    }

    summary_rows.extend([
        ["", "", "", "", "", "", "", "", "", "", ""],
        ["2. PIPELINE BY COMMERCIAL PROGRESS STAGE", "", "", "", "", "", "", "", "", "", ""],
        ["Commercial Stage", "Stage Definition", "Workloads (#)", "Pipeline ARR ($ USD)", "ARR Share (%)", "Primary Acceleration Action", "", "", "", "", ""]
    ])

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
            "", "", "", "", ""
        ])
    summary_rows.append([
        "TOTAL",
        "All Active Stages",
        str(len(oliver_wkls)),
        f"${total_arr:,.2f}",
        "100.0%",
        "Full Oliver FSR Commercial Portfolio",
        "", "", "", "", ""
    ])

    # Partner concentration
    partner_agg = {}
    for w in oliver_wkls:
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

    summary_rows.extend([
        ["", "", "", "", "", "", "", "", "", "", ""],
        ["3. TOP PARTNER ENGAGEMENT & DELIVERY CONCENTRATION (TOP 15)", "", "", "", "", "", "", "", "", "", ""],
        ["Partner Organization", "Standing / Tier", "Workloads (#)", "Pipeline ARR ($ USD)", "ARR Share (%)", "Delivery Alignment", "", "", "", "", ""]
    ])

    for p_name, p_data in sorted_partners[:15]:
        p_cnt = p_data["count"]
        p_arr = p_data["arr"]
        p_pct = (p_arr / total_arr * 100) if total_arr > 0 else 0.0
        standing = "⚠️ No Partner Attached" if "Unpartnered" in p_name else "Active Delivery Partner"
        align = "Immediate partner matchmaking" if "Unpartnered" in p_name else "Co-selling & delivery tracking"
        summary_rows.append([
            p_name,
            standing,
            str(p_cnt),
            f"${p_arr:,.2f}",
            f"{p_pct:.1f}%",
            align,
            "", "", "", "", ""
        ])

    summary_rows.extend([
        ["", "", "", "", "", "", "", "", "", "", ""],
        ["4. TOP 15 STRATEGIC WORKLOADS (RANKED BY ARR)", "", "", "", "", "", "", "", "", "", ""],
        ["Workload Name", "Customer Account", "FSR Name", "ARR ($ USD)", "Opportunity Stage", "Workload Progress", "Partner Name", "Target Production Date", "", "", ""]
    ])

    for top_w in oliver_wkls[:15]:
        t_wname = top_w.get("workload_name") or ""
        t_wid = top_w.get("workload_id") or ""
        t_aid = top_w.get("sfdc_account_id") or ""
        t_aname = top_w.get("account_name") or ""
        t_fsr = top_w.get("assigned_fsr") or ""
        t_arr = float(top_w.get("annual_gross_revenue") or 0.0)
        t_opp_stage = top_w.get("stage_name") or ""
        t_prog = top_w.get("workload_progress") or ""
        t_pname = top_w.get("partner_name") if top_w.get("is_partnered") else "⚠️ Unpartnered"
        t_pdate = str(top_w.get("production_date") or "").strip()

        w_link = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Workload__c/{t_wid}/view", t_wname) if t_wid else t_wname
        a_link = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Account/{t_aid}/view", t_aname) if t_aid else t_aname

        summary_rows.append([
            w_link,
            a_link,
            t_fsr,
            f"${t_arr:,.2f}",
            t_opp_stage,
            t_prog,
            t_pname,
            t_pdate,
            "", "", ""
        ])

    out_summary_csv = os.path.join(BASE_DIR, "fsr_decks_data", "rollup_oliver_summary.csv")
    with open(out_summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(summary_rows)

    # -------------------------------------------------------------
    # 3. TAB 3: Unpartnered_Matchmaker CSV (19 Columns)
    # -------------------------------------------------------------
    num_m_cols = len(MATCHMAKER_HEADERS)
    match_rows = [
        ["🤝 UNPARTNERED DEALS & BRAZIL PARTNER MATCHMAKER — OLIVER HARTLEY FSR PORTFOLIO"] + [""] * (num_m_cols - 1),
        ["Consolidated unpartnered deals across Felipe Pilon, Roberta Coelho, Vanessa Moyses, and Ana Luiza Gama. Candidate Brazil partners ranked by certified DRP bench, product expertise, and delivery track record."] + [""] * (num_m_cols - 1),
        [""] * num_m_cols,
        list(MATCHMAKER_HEADERS)
    ]

    for uw in unpartnered_wkls:
        uw_id = uw.get("workload_id") or ""
        uw_name = uw.get("workload_name") or ""
        uw_aid = uw.get("sfdc_account_id") or ""
        uw_aname = uw.get("account_name") or ""
        uw_fsr = uw.get("assigned_fsr") or "Oliver Hartley FSR"
        uw_opp_id = uw.get("opportunity_id") or ""
        uw_opp_name = uw.get("opportunity_name") or ""
        uw_arr = float(uw.get("annual_gross_revenue") or 0.0)
        uw_opp_stage = uw.get("stage_name") or ""
        uw_prog = uw.get("workload_progress") or ""
        uw_pillar = uw.get("pillar") or ""
        uw_prods = ", ".join(uw.get("key_workload_products") or []) or uw.get("workload_solutions") or "Cloud Architecture"
        uw_pdate = str(uw.get("production_date") or "").strip()
        uw_ns = (uw.get("next_steps") or "").replace("\r\n", " ").replace("\n", " ").strip()
        uw_tier = get_account_tier(uw_id, uw_aid, uw_aname, uw.get("segment"))

        acc_cell = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Account/{uw_aid}/view", uw_aname) if uw_aid else uw_aname
        wkl_cell = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Workload__c/{uw_id}/view", uw_name) if uw_id else uw_name
        opp_cell = make_hyperlink(f"https://vector.lightning.force.com/lightning/r/Opportunity/{uw_opp_id}/view", uw_opp_name) if uw_opp_id else uw_opp_name

        opp_pid = uw.get("opportunity_partner_id") or ""
        opp_pname = uw.get("opportunity_partner_name") or ""
        if opp_pname:
            opp_p_url = f"https://vector.lightning.force.com/lightning/r/Account/{opp_pid}/view" if opp_pid else ""
            opp_partner_cell = make_hyperlink(opp_p_url, opp_pname) if opp_p_url else opp_pname
        else:
            opp_partner_cell = ""

        matches = match_partners_for_workload(uw, candidate_partners)
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
            uw_fsr,
            acc_cell,
            uw_tier,
            wkl_cell,
            f"${uw_arr:,.2f}",
            uw_opp_stage,
            uw_prog,
            uw_pillar,
            uw_prods,
            opp_partner_cell,
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

    out_matchmaker_csv = os.path.join(BASE_DIR, "fsr_decks_data", "rollup_oliver_matchmaker.csv")
    with open(out_matchmaker_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(match_rows)

    return {
        "ssid": ROLLUP_SSID,
        "title": "FSR Management Dashboard - Oliver Hartley",
        "url": f"https://docs.google.com/spreadsheets/d/{ROLLUP_SSID}/edit",
        "total_workloads": len(oliver_wkls),
        "total_arr": total_arr,
        "partnered_count": len(partnered_wkls),
        "unpartnered_count": len(unpartnered_wkls),
        "followup_csv": out_followup_csv,
        "summary_csv": out_summary_csv,
        "matchmaker_csv": out_matchmaker_csv,
        "followup_row_count": len(followup_rows),
        "summary_row_count": len(summary_rows),
        "matchmaker_row_count": len(match_rows),
        "true_tech_wins": true_tech_wins,
        "true_prop_sents": true_prop_sents
    }


def deploy_rollup_dashboard(rollup_info):
    ssid = rollup_info["ssid"]
    f_csv = rollup_info["followup_csv"]
    s_csv = rollup_info["summary_csv"]
    m_csv = rollup_info["matchmaker_csv"]
    f_total_rows = rollup_info["followup_row_count"]
    s_total_rows = rollup_info["summary_row_count"]
    m_total_rows = rollup_info["matchmaker_row_count"]
    true_tech_wins = rollup_info["true_tech_wins"]
    true_prop_sents = rollup_info["true_prop_sents"]

    print(f"\n========================================================")
    print(f"Deploying Rollup Dashboard: {rollup_info['title']}")
    print(f"Spreadsheet URL: {rollup_info['url']}")
    print(f"========================================================")

    # 1. Ensure tabs
    print("Setting up tabs: Executive_Summary, All_Workloads_Follow_up, Unpartnered_Matchmaker...")
    sid_summary = ensure_tab(ssid, "Executive_Summary")
    sid_followup = ensure_tab(ssid, "All_Workloads_Follow_up")
    sid_matchmaker = ensure_tab(ssid, "Unpartnered_Matchmaker")

    # Clear old data
    print("Clearing old data and previous formatting...")
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Executive_Summary'!A1:Z500"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'All_Workloads_Follow_up'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "clear", ssid, "'Unpartnered_Matchmaker'!A1:Z2000"], capture_output=True)

    # 2. Import CSVs
    print("Importing Executive_Summary CSV...")
    res_s = subprocess.run([GSHEETS, "mutate", "import-csv", ssid, s_csv, "--sheet", "Executive_Summary"], capture_output=True, text=True)
    if res_s.returncode != 0:
        print(f"ERROR importing Executive_Summary: {res_s.stderr}")

    print("Importing All_Workloads_Follow_up CSV...")
    res_f = subprocess.run([GSHEETS, "mutate", "import-csv", ssid, f_csv, "--sheet", "All_Workloads_Follow_up"], capture_output=True, text=True)
    if res_f.returncode != 0:
        print(f"ERROR importing All_Workloads_Follow_up: {res_f.stderr}")

    print("Importing Unpartnered_Matchmaker CSV...")
    res_m = subprocess.run([GSHEETS, "mutate", "import-csv", ssid, m_csv, "--sheet", "Unpartnered_Matchmaker"], capture_output=True, text=True)
    if res_m.returncode != 0:
        print(f"ERROR importing Unpartnered_Matchmaker: {res_m.stderr}")
    else:
        print("✓ Unpartnered_Matchmaker CSV imported.")

    # 3. Trim columns on All_Workloads_Follow_up
    p_cols = len(FOLLOWUP_HEADERS)
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
    tmp_trim = f"temp_trim_rollup_{ssid}.json"
    with open(tmp_trim, "w") as f:
        json.dump(trim_req, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_trim], capture_output=True)
    if os.path.exists(tmp_trim):
        os.remove(tmp_trim)

    # Grid info
    grid_info = get_grid_info(ssid)
    f_info = grid_info.get("All_Workloads_Follow_up", {"sheetId": sid_followup, "rowCount": f_total_rows, "columnCount": p_cols})
    sid_followup = f_info["sheetId"]
    f_rows = max(f_total_rows, f_info["rowCount"])

    s_info = grid_info.get("Executive_Summary", {"sheetId": sid_summary, "rowCount": s_total_rows, "columnCount": 11})
    sid_summary = s_info["sheetId"]
    s_rows = max(s_total_rows, s_info["rowCount"])

    m_info = grid_info.get("Unpartnered_Matchmaker", {"sheetId": sid_matchmaker, "rowCount": m_total_rows, "columnCount": len(MATCHMAKER_HEADERS)})
    sid_matchmaker = m_info["sheetId"]
    m_rows = max(m_total_rows, m_info["rowCount"])
    m_cols = len(MATCHMAKER_HEADERS)

    # -------------------------------------------------------------
    # 4. Format All_Workloads_Follow_up Tab
    # -------------------------------------------------------------
    print("Formatting All_Workloads_Follow_up tab...")
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_followup), "--rows", "5"], capture_output=True)

    batch_followup = {
        "requests": [
            # Clear all data validation across all columns
            {
                "setDataValidation": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1000, "startColumnIndex": 0, "endColumnIndex": max(p_cols, 35)}
                }
            },
            # Reset cell styles
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
            # Clear borders
            {
                "updateBorders": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols},
                    "top": {"style": "NONE"}, "bottom": {"style": "NONE"}, "left": {"style": "NONE"}, "right": {"style": "NONE"},
                    "innerHorizontal": {"style": "NONE"}, "innerVertical": {"style": "NONE"}
                }
            },
            # Unmerge ALL rows across sheet to clear any old merges
            {"unmergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": p_cols}}},
            # Row 1 Metadata formatting
            {"mergeCells": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "mergeType": "MERGE_ALL"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.95, "green": 0.91, "blue": 0.99}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.41, "green": 0.11, "blue": 0.66}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 0.37, "green": 0.39, "blue": 0.41}}, "horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat(textFormat,horizontalAlignment)"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.90, "green": 0.96, "blue": 0.92}, "textFormat": {"bold": True, "foregroundColor": {"red": 0.07, "green": 0.45, "blue": 0.20}}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},

            # Row 5 Header (Cols 0 to 20): Google Blue
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": p_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},

            # Row 3 Amber Alert Banner
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
                        "note": "Consolidated rollup across all 4 Oliver Hartley FSRs (317 workloads, $45.30M ARR). Workloads in stage 4.3 (Migrated/Implemented) are included."
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy),note"
                }
            },

            # Data types:
            # Col 0 (A): FSR Name (Center)
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "textFormat": {"bold": True}}}, "fields": "userEnteredFormat(horizontalAlignment,textFormat)"}},
            # Col 4 (E): ARR USD Currency
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat.numberFormat"}},
            # Col 5 (F): Opportunity Stage as TEXT (Center)
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 5, "endColumnIndex": 6}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}},
            # Col 6 (G): Workload Progress as TEXT (Center)
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"}},
            # Col 7 (H) & 9 (J): Dates (Center)
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 7, "endColumnIndex": 8}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 9, "endColumnIndex": 10}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
            # Col 8 (I) & Col 10 (K): Days Until Implementation / Production as NUMBER
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 8, "endColumnIndex": 9}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}}, "fields": "userEnteredFormat.numberFormat"}},
            {"repeatCell": {"range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 10, "endColumnIndex": 11}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}}, "fields": "userEnteredFormat.numberFormat"}},
            # Col 11 (L): Cual es el bloqueo? dropdown
            {
                "setDataValidation": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 11, "endColumnIndex": 12},
                    "rule": {
                        "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "Comercial"}, {"userEnteredValue": "Tecnico"}]},
                        "strict": True,
                        "showCustomUi": True
                    }
                }
            },
            # Col 20 (U) & Col 21 (V): Boolean Checkboxes
            {
                "setDataValidation": {
                    "range": {"sheetId": sid_followup, "startRowIndex": 5, "endRowIndex": f_rows, "startColumnIndex": 20, "endColumnIndex": 22},
                    "rule": {"condition": {"type": "BOOLEAN"}, "showCustomUi": True}
                }
            }
        ]
    }

    # Column widths
    for col_idx, width in FOLLOWUP_COL_WIDTHS.items():
        batch_followup["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_followup, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
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

    tmp_f_batch = f"temp_f_batch_{ssid}.json"
    with open(tmp_f_batch, "w") as f:
        json.dump(batch_followup, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_f_batch], capture_output=True)
    if os.path.exists(tmp_f_batch):
        os.remove(tmp_f_batch)

    # Checkbox boolean values
    for r_idx in true_tech_wins:
        subprocess.run([GSHEETS, "mutate", "update-cell", ssid, f"'All_Workloads_Follow_up'!U{r_idx + 1}", "TRUE"], capture_output=True)
    for r_idx in true_prop_sents:
        subprocess.run([GSHEETS, "mutate", "update-cell", ssid, f"'All_Workloads_Follow_up'!V{r_idx + 1}", "TRUE"], capture_output=True)
    print("✓ All_Workloads_Follow_up formatted.")

    # -------------------------------------------------------------
    # 5. Format Executive_Summary Tab
    # -------------------------------------------------------------
    print("Formatting Executive_Summary tab...")
    batch_summary = {
        "requests": [
            # Reset cell styles
            {
                "repeatCell": {
                    "range": {"sheetId": sid_summary, "startRowIndex": 0, "endRowIndex": s_rows, "startColumnIndex": 0, "endColumnIndex": 11},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "textFormat": {"foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0}, "fontSize": 10, "fontFamily": "Arial"},
                            "horizontalAlignment": "LEFT",
                            "verticalAlignment": "MIDDLE"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }
            },
            # Row 1 Title
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 11}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            # Section headers (Rows 3, 11, 19, etc.)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 11}, "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.12, "green": 0.20, "blue": 0.40}}}}, "fields": "userEnteredFormat.textFormat"}},
            # Table 1 Header (Row 5)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 11}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,wrapStrategy)"}},
            # Table 1 Total Row (Row 10)
            {"repeatCell": {"range": {"sheetId": sid_summary, "startRowIndex": 9, "endRowIndex": 10, "startColumnIndex": 0, "endColumnIndex": 11}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}}
        ]
    }

    # Summary Column widths
    summary_widths = {0: 180, 1: 160, 2: 200, 3: 130, 4: 160, 5: 140, 6: 150, 7: 140, 8: 150, 9: 130, 10: 220}
    for col_idx, width in summary_widths.items():
        batch_summary["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_summary, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    tmp_s_batch = f"temp_s_batch_{ssid}.json"
    with open(tmp_s_batch, "w") as f:
        json.dump(batch_summary, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_s_batch], capture_output=True)
    if os.path.exists(tmp_s_batch):
        os.remove(tmp_s_batch)
    print("✓ Executive_Summary formatted.")

    # -------------------------------------------------------------
    # 6. Format Unpartnered_Matchmaker Tab
    # -------------------------------------------------------------
    print("Formatting Unpartnered_Matchmaker tab...")
    subprocess.run([GSHEETS, "mutate", "freeze", ssid, "--sheet-id", str(sid_matchmaker), "--rows", "4"], capture_output=True)

    batch_matchmaker = {
        "requests": [
            # Reset cell styles
            {
                "repeatCell": {
                    "range": {"sheetId": sid_matchmaker, "startRowIndex": 0, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": m_cols},
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
            # Row 1 Title
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": m_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.91, "green": 0.94, "blue": 1.0}, "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 0.10, "green": 0.45, "blue": 0.91}}, "horizontalAlignment": "LEFT"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
            # Row 4 Header (Google Blue)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": m_cols}, "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.102, "green": 0.451, "blue": 0.910}, "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"}},
            # Col 0 (A): FSR Name (Center)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 0, "endColumnIndex": 1}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER", "textFormat": {"bold": True}}}, "fields": "userEnteredFormat(horizontalAlignment,textFormat)"}},
            # Col 4 (E): ARR USD Currency
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}}, "fields": "userEnteredFormat.numberFormat"}},
            # Col 5 (F) & Col 6 (G): Stage & Progress (Center)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 5, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
            # Col 9 (J): Opportunity Partner (Left align, text wrap clip)
            {"repeatCell": {"range": {"sheetId": sid_matchmaker, "startRowIndex": 4, "endRowIndex": m_rows, "startColumnIndex": 9, "endColumnIndex": 10}, "cell": {"userEnteredFormat": {"horizontalAlignment": "LEFT", "wrapStrategy": "CLIP"}}, "fields": "userEnteredFormat(horizontalAlignment,wrapStrategy)"}}
        ]
    }

    # Matchmaker Column widths
    for col_idx, width in MATCHMAKER_COL_WIDTHS.items():
        batch_matchmaker["requests"].append({
            "updateDimensionProperties": {
                "range": {"sheetId": sid_matchmaker, "dimension": "COLUMNS", "startIndex": col_idx, "endIndex": col_idx + 1},
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    tmp_m_batch = f"temp_m_batch_{ssid}.json"
    with open(tmp_m_batch, "w") as f:
        json.dump(batch_matchmaker, f)
    subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_m_batch], capture_output=True)
    if os.path.exists(tmp_m_batch):
        os.remove(tmp_m_batch)
    print("✓ Unpartnered_Matchmaker formatted.")

    print("\n========================================================")
    print(f"🎉 ROLLUP DASHBOARD DEPLOYED SUCCESSFULLY!")
    print(f"URL: {rollup_info['url']}")
    print(f"Total Workloads: {rollup_info['total_workloads']} | Pipeline: ${rollup_info['total_arr']:,.2f}")
    print(f"========================================================")
    return rollup_info


def main():
    print("=" * 70)
    print("🚀 BUILDING CONSOLIDATED OLIVER HARTLEY FSR ROLLUP DASHBOARD")
    print("=" * 70)

    cache = json.load(open(os.path.join(BASE_DIR, "data", "portfolio_cache.json")))
    prio_map = json.load(open(os.path.join(BASE_DIR, "priorizacion_q3_statuses.json")))
    user_data = json.load(open(os.path.join(BASE_DIR, "data", "workload_user_data.json")))
    manual_entries = json.load(open(os.path.join(BASE_DIR, "fsr_manual_entries.json")))
    ai_cache = json.load(open(AI_SUMMARIES_FILE))

    rollup_info = build_rollup_datasets(cache, prio_map, user_data, manual_entries, ai_cache)
    deploy_rollup_dashboard(rollup_info)

    # Save rollup manifest
    manifest_path = os.path.join(BASE_DIR, "fsr_rollup_oliver.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(rollup_info, f, indent=2)
    print(f"Rollup manifest saved to {manifest_path}")


if __name__ == "__main__":
    main()
