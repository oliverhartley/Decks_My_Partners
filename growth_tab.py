import json
import csv
import subprocess
import os
import sys
import datetime
from collections import defaultdict

sys.path.append("/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners")
from query_bq import run_query

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
TOTAL_COLS = 14

def pad_row(row, target_len=TOTAL_COLS):
    if len(row) < target_len:
        return row + [""] * (target_len - len(row))
    return row[:target_len]

def make_hyperlink(url, label):
    clean_label = str(label).replace('"', '""').replace('\n', ' ').strip()
    return f'=HYPERLINK("{url}", "{clean_label}")'

def format_currency(val):
    return f"${val:,.2f}"

def fetch_all_workload_growth_data(all_pids_set):
    """
    Fetches all Q3 workload stage transitions (0-2 -> 3 and 3 -> 4.1) for all partner IDs.
    Returns a list of parsed transition dictionaries.
    """
    print(">>> Fetching all Q3 Workload Stage Transitions from BigQuery...")
    pids_str = ", ".join([f"'{x}'" for x in all_pids_set])
    sql_wkl = f"""
    SELECT 
      w.workload_id,
      w.workload_name,
      COALESCE(w.customer.account_name, o.account_name) AS account_name,
      COALESCE(w.sfdc_account_id, o.sfdc_account_id) AS account_id,
      w.workload_details.partner_id,
      w.metrics.annual_gross_revenue,
      w.workload_details.workload_progress AS current_progress,
      h.start_time,
      h.previous_value,
      h.value,
      w.owner_details.owner_name,
      w.owner_details.owner_user_name,
      w.workload_details.primary_workload_pillar,
      o.opportunity_id,
      o.opportunity_name
    FROM `concord-prod.service_cloudbi.workloads` w
    LEFT JOIN `concord-prod.service_cloudbi.opportunities` o
      ON w.opportunity_id = o.opportunity_id
    CROSS JOIN UNNEST(w.field_history.workload_progress_field_history) h
    WHERE (w.workload_details.partner_id IN ({pids_str}) OR w.workload_id = 'aBJKf000009oRYkOAM')
      AND h.start_time >= '2026-07-01'
      AND h.start_time < '2026-10-01'
    ORDER BY h.start_time ASC
    """
    _, rows_w = run_query(sql_wkl)
    print(f"Loaded {len(rows_w)} raw workload history records.")

    wkl_transitions = []
    for r in rows_w:
        c = [col.get('v') for col in r['f']]
        wid, wname, acc_name, acc_id, pid, arr, curr_prog, st_time_raw, prev_val, val, owner_name, owner_user, pillar, opp_id, opp_name = c
        
        trans_type = None
        if prev_val and prev_val.strip().startswith("0-2") and val and val.strip().startswith("3:"):
            trans_type = "Stage 0-2 ➔ Stage 3"
        elif prev_val and prev_val.strip().startswith("3:") and val and val.strip().startswith("4.1"):
            trans_type = "Stage 3 ➔ Stage 4.1"

        if trans_type:
            st_sec = float(st_time_raw)
            dt = datetime.datetime.fromtimestamp(st_sec, datetime.timezone.utc)
            date_str = dt.strftime("%Y-%m-%d")
            month_num = dt.month
            month_name = {7: "July", 8: "August", 9: "September"}.get(month_num, f"M{month_num}")
            arr_val = float(arr) if arr is not None else 0.0

            wkl_transitions.append({
                "workload_id": wid,
                "workload_name": wname or wid,
                "account_name": acc_name or "Unknown Account",
                "account_id": acc_id or "",
                "partner_id": pid,
                "arr": arr_val,
                "transition": trans_type,
                "date": date_str,
                "month_num": month_num,
                "month_name": month_name,
                "prev_val": prev_val,
                "val": val,
                "curr_prog": curr_prog,
                "owner": owner_name or owner_user or "Unassigned",
                "pillar": pillar or "Cross-Pillar",
                "opp_id": opp_id or "",
                "opp_name": opp_name or "Opportunity"
            })
    print(f"Filtered {len(wkl_transitions)} valid workload stage transitions across all partners.")
    return wkl_transitions

def fetch_all_drp_growth_data(all_drp_keys_set):
    """
    Fetches all Q3 DRP tier promotions (T4->T3, T3->T2, T2->T1) using Practice Area and Product.
    Returns a list of parsed DRP transition dictionaries.
    """
    print(">>> Fetching all Q3 DRP Tier Promotions from BigQuery...")
    drp_str = ", ".join([f"'{x}'" for x in all_drp_keys_set])
    sql_drp = f"""
    WITH DailyScores AS (
      SELECT 
        IFNULL(m.partner_details.consolidated_partner_id, m.partner_details.vector_details.parent_id) AS consolidated_partner_id,
        m.profile_details.profile_id,
        h.name as product_name,
        h.update_date,
        h.score,
        CASE 
          WHEN h.score >= 50 THEN 'Tier 1'
          WHEN h.score >= 35 THEN 'Tier 2'
          WHEN h.score >= 20 THEN 'Tier 3'
          ELSE 'Tier 4'
        END as tier
      FROM `concord-prod.service_partnercoe.drp_partner_master` m
      CROSS JOIN UNNEST(m.profile_details.score_history_details) h
      WHERE (m.partner_details.consolidated_partner_id IN ({drp_str}) OR m.partner_id IN ({drp_str}))
        AND h.type = 'Product'
        AND h.update_date >= '2026-06-25'
        AND h.update_date <= '2026-09-30'
    ),
    TierTransitions AS (
      SELECT 
        consolidated_partner_id,
        profile_id,
        product_name,
        update_date,
        score,
        tier,
        LAG(tier) OVER (PARTITION BY profile_id, product_name ORDER BY update_date) as prev_tier,
        LAG(score) OVER (PARTITION BY profile_id, product_name ORDER BY update_date) as prev_score
      FROM DailyScores
    ),
    PracticeAreaMapping AS (
      SELECT DISTINCT
        pillar as practice_area,
        COALESCE(p.scored_product, 'All Products') as product
      FROM `concord-prod.service_partnercoe_general.view_delivery_capacity_dri_profile` p
      CROSS JOIN UNNEST(p.parent_pillar) pillar
      WHERE pillar IS NOT NULL
    )
    SELECT 
      t.consolidated_partner_id,
      COALESCE(pm.practice_area, IF(t.product_name = 'Gemini Enterprise for Customer Experience', 'Artificial Intelligence', 'Other')) as practice_area,
      t.product_name,
      t.profile_id,
      t.prev_tier,
      t.tier,
      t.prev_score,
      t.score,
      t.update_date,
      EXTRACT(MONTH FROM t.update_date) as update_month
    FROM TierTransitions t
    LEFT JOIN PracticeAreaMapping pm
      ON t.product_name = pm.product
    WHERE t.update_date >= '2026-07-01'
      AND t.update_date <= '2026-09-30'
      AND t.prev_tier IS NOT NULL
      AND (
        (t.prev_tier = 'Tier 4' AND t.tier = 'Tier 3')
        OR (t.prev_tier = 'Tier 3' AND t.tier = 'Tier 2')
        OR (t.prev_tier = 'Tier 2' AND t.tier = 'Tier 1')
      )
    ORDER BY t.update_date ASC
    """
    _, rows_d = run_query(sql_drp)
    print(f"Loaded {len(rows_d)} raw DRP transition records.")

    drp_transitions = []
    for r in rows_d:
        c = [col.get('v') for col in r['f']]
        d_pid, pa, prod, prof_id, prev_t, new_t, prev_s, s, udate, umonth = c
        month_name = {7: "July", 8: "August", 9: "September"}.get(int(umonth), f"M{umonth}")
        trans_label = f"{prev_t} ➔ {new_t}"
        score_val = float(s) if s is not None else 0.0
        prev_score_val = float(prev_s) if prev_s is not None else 0.0
        score_delta = score_val - prev_score_val

        drp_transitions.append({
            "drp_key": d_pid,
            "practice_area": pa,
            "product": prod,
            "profile_id": prof_id,
            "prev_tier": prev_t,
            "new_tier": new_t,
            "transition": trans_label,
            "prev_score": prev_score_val,
            "score": score_val,
            "score_delta": score_delta,
            "date": udate,
            "month_num": int(umonth),
            "month_name": month_name
        })
    print(f"Filtered {len(drp_transitions)} valid DRP tier promotions across all partners.")
    return drp_transitions

def build_growth_csv_and_layout(cfg, partner_wkl_transitions, partner_drp_transitions, output_csv_path):
    """
    Builds the 14-column CSV rows and returns layout metadata for styling.
    """
    pname = cfg["partner"]
    pe_name = cfg.get("pe", "")
    drp_keys = cfg.get("drp_keys", [])

    now = datetime.datetime.now()
    date_formatted = f"{now.day} - {now.strftime('%b')} {now.year}"
    rows = []

    # Row 0-2: Header Block
    rows.append(pad_row([f"PARTNER GROWTH & VELOCITY: WORKLOAD STAGE PROGRESSION & DRP CAPABILITY"]))
    rows.append(pad_row([f"Partner: {pname} | Partner Engineer: {pe_name} | Scope: Q3 2026 (July, August, September)"]))
    rows.append(pad_row([f"Last Sync: {date_formatted} | Source: Concord BigQuery (Workload History & DRP Master) | Unified 14-Col Schema"]))
    rows.append(pad_row([]))  # Row 3 (Spacer & Freeze line)

    layout = {
        "header_indices": [0, 1, 2],
        "freeze_row": 4
    }

    # -------------------------------------------------------------
    # SECTION 1: WORKLOAD GROWTH
    # -------------------------------------------------------------
    layout["sec1_title_idx"] = len(rows)
    rows.append(pad_row(["1. WORKLOAD GROWTH: STAGE ADVANCEMENTS (0-2 ➔ 3 & 3 ➔ 4.1)"]))
    
    layout["t1a_header_idx"] = len(rows)
    rows.append(pad_row([
        "Stage Transition",
        "July (#)", "July ($ ARR)",
        "August (#)", "August ($ ARR)",
        "September (#)", "September ($ ARR)",
        "Q3 Total (#)", "Q3 Total ($ ARR)",
        "Share of Moved Deals",
        "Top Pillar",
        "Avg Deal ARR",
        "Velocity Momentum",
        "Status"
    ]))

    layout["t1a_data_start"] = len(rows)
    s02_3 = [w for w in partner_wkl_transitions if w["transition"] == "Stage 0-2 ➔ Stage 3"]
    s3_41 = [w for w in partner_wkl_transitions if w["transition"] == "Stage 3 ➔ Stage 4.1"]

    tot_wkl_cnt = len(partner_wkl_transitions)
    tot_wkl_arr = sum(w["arr"] for w in partner_wkl_transitions)

    for stg_label, stg_list in [("Stage 0-2 ➔ Stage 3 (Co-Pilot & Develop)", s02_3), ("Stage 3 ➔ Stage 4.1 (Build & Run / Delivery)", s3_41)]:
        cnt_j = sum(1 for w in stg_list if w["month_num"] == 7)
        arr_j = sum(w["arr"] for w in stg_list if w["month_num"] == 7)
        cnt_a = sum(1 for w in stg_list if w["month_num"] == 8)
        arr_a = sum(w["arr"] for w in stg_list if w["month_num"] == 8)
        cnt_s = sum(1 for w in stg_list if w["month_num"] == 9)
        arr_s = sum(w["arr"] for w in stg_list if w["month_num"] == 9)

        cnt_tot = len(stg_list)
        arr_tot = sum(w["arr"] for w in stg_list)
        pct_share = f"{(cnt_tot / tot_wkl_cnt * 100):.1f}%" if tot_wkl_cnt else "0.0%"
        avg_arr = format_currency(arr_tot / cnt_tot) if cnt_tot else "$0.00"

        pil_c = defaultdict(int)
        for w in stg_list:
            pil_c[w["pillar"]] += 1
        top_pil = max(pil_c.items(), key=lambda x: x[1])[0] if pil_c else "-"

        momentum = "Accelerating" if cnt_s > cnt_a else ("Consistent" if cnt_a > 0 else "Front-Loaded")
        status = "Active Progression" if cnt_tot > 0 else "No Movements"

        rows.append(pad_row([
            stg_label,
            cnt_j, format_currency(arr_j),
            cnt_a, format_currency(arr_a),
            cnt_s, format_currency(arr_s),
            cnt_tot, format_currency(arr_tot),
            pct_share,
            top_pil,
            avg_arr,
            momentum,
            status
        ]))

    layout["t1a_tot_idx"] = len(rows)
    cnt_j_all = sum(1 for w in partner_wkl_transitions if w["month_num"] == 7)
    arr_j_all = sum(w["arr"] for w in partner_wkl_transitions if w["month_num"] == 7)
    cnt_a_all = sum(1 for w in partner_wkl_transitions if w["month_num"] == 8)
    arr_a_all = sum(w["arr"] for w in partner_wkl_transitions if w["month_num"] == 8)
    cnt_s_all = sum(1 for w in partner_wkl_transitions if w["month_num"] == 9)
    arr_s_all = sum(w["arr"] for w in partner_wkl_transitions if w["month_num"] == 9)

    rows.append(pad_row([
        "TOTAL WORKLOAD MOVEMENTS",
        cnt_j_all, format_currency(arr_j_all),
        cnt_a_all, format_currency(arr_a_all),
        cnt_s_all, format_currency(arr_s_all),
        tot_wkl_cnt, format_currency(tot_wkl_arr),
        "100.0%",
        "-",
        format_currency(tot_wkl_arr / tot_wkl_cnt) if tot_wkl_cnt else "$0.00",
        "-",
        "-"
    ]))
    layout["t1a_end"] = len(rows)
    rows.append(pad_row([]))  # Spacer

    # Table 1B: Advanced Workloads Inventory
    layout["t1b_title_idx"] = len(rows)
    rows.append(pad_row(["ADVANCED WORKLOADS INVENTORY (Q3 STAGE MOVEMENTS DETAIL)"]))
    layout["t1b_header_idx"] = len(rows)
    rows.append(pad_row([
        "Customer Account Name",
        "Workload Name",
        "Annual Gross Revenue (ARR USD)",
        "Stage Movement",
        "Transition Month",
        "Transition Date",
        "Previous Progress",
        "New Progress",
        "Current Progress",
        "Workload Owner",
        "Primary Pillar",
        "Opportunity Name",
        "Partner ID",
        "Status"
    ]))

    layout["t1b_data_start"] = len(rows)
    layout["t1b_has_data"] = bool(partner_wkl_transitions)
    if partner_wkl_transitions:
        sorted_wkls = sorted(partner_wkl_transitions, key=lambda w: (w["month_num"], w["date"], -w["arr"]))
        for w in sorted_wkls:
            acc_link = make_hyperlink(f"https://vector.corp.google.com/account/{w['account_id']}", w["account_name"]) if w["account_id"] else w["account_name"]
            wkl_link = make_hyperlink(f"https://vector.corp.google.com/workload/{w['workload_id']}", w["workload_name"])
            opp_link = make_hyperlink(f"https://vector.corp.google.com/opportunity/{w['opp_id']}", w["opp_name"]) if w["opp_id"] else w["opp_name"]

            rows.append(pad_row([
                acc_link,
                wkl_link,
                format_currency(w["arr"]),
                w["transition"],
                w["month_name"],
                w["date"],
                w["prev_val"],
                w["val"],
                w["curr_prog"],
                w["owner"],
                w["pillar"],
                opp_link,
                w["partner_id"],
                "Progressed"
            ]))
    else:
        rows.append(pad_row(["No stage advancements recorded for this partner in Q3 2026 (July - September)"]))
    layout["t1b_end"] = len(rows)
    rows.append(pad_row([]))  # Spacer

    # -------------------------------------------------------------
    # SECTION 2: DRP GROWTH
    # -------------------------------------------------------------
    layout["sec2_title_idx"] = len(rows)
    rows.append(pad_row(["2. DRP GROWTH: PRACTITIONER TIER PROMOTIONS (T4➔T3, T3➔T2, T2➔T1)"]))
    
    layout["t2a_header_idx"] = len(rows)
    rows.append(pad_row([
        "Tier Transition",
        "July Upgrades",
        "August Upgrades",
        "September Upgrades",
        "Q3 Total Upgrades",
        "Unique Profiles",
        "July % Share",
        "August % Share",
        "September % Share",
        "Top Practice Area",
        "Top Product",
        "Growth Velocity",
        "DRP Partner Key",
        "Status"
    ]))

    layout["t2a_data_start"] = len(rows)
    tot_drp_cnt = len(partner_drp_transitions)
    tot_drp_uprofs = len(set(d["profile_id"] for d in partner_drp_transitions))

    for trans_label in ["Tier 4 ➔ Tier 3", "Tier 3 ➔ Tier 2", "Tier 2 ➔ Tier 1"]:
        t_list = [d for d in partner_drp_transitions if d["transition"] == trans_label]
        c_j = sum(1 for d in t_list if d["month_num"] == 7)
        c_a = sum(1 for d in t_list if d["month_num"] == 8)
        c_s = sum(1 for d in t_list if d["month_num"] == 9)
        c_tot = len(t_list)
        uprof = len(set(d["profile_id"] for d in t_list))

        pct_j = f"{(c_j / c_tot * 100):.1f}%" if c_tot else "0.0%"
        pct_a = f"{(c_a / c_tot * 100):.1f}%" if c_tot else "0.0%"
        pct_s = f"{(c_s / c_tot * 100):.1f}%" if c_tot else "0.0%"

        pa_c = defaultdict(int)
        prd_c = defaultdict(int)
        for d in t_list:
            pa_c[d["practice_area"]] += 1
            prd_c[d["product"]] += 1
        top_pa = max(pa_c.items(), key=lambda x: x[1])[0] if pa_c else "-"
        top_prd = max(prd_c.items(), key=lambda x: x[1])[0] if prd_c else "-"

        velocity = "🔥 High" if c_tot >= 10 else ("🚀 Steady" if c_tot >= 3 else "🌱 Emerging")
        status = "Active Progression" if c_tot > 0 else "No Upgrades"

        rows.append(pad_row([
            trans_label,
            c_j, c_a, c_s, c_tot, uprof,
            pct_j, pct_a, pct_s,
            top_pa, top_prd,
            velocity,
            drp_keys[0] if drp_keys else "-",
            status
        ]))

    layout["t2a_tot_idx"] = len(rows)
    all_dj = sum(1 for d in partner_drp_transitions if d["month_num"] == 7)
    all_da = sum(1 for d in partner_drp_transitions if d["month_num"] == 8)
    all_ds = sum(1 for d in partner_drp_transitions if d["month_num"] == 9)

    rows.append(pad_row([
        "TOTAL DRP TIER PROMOTIONS",
        all_dj, all_da, all_ds, tot_drp_cnt, tot_drp_uprofs,
        f"{(all_dj / tot_drp_cnt * 100):.1f}%" if tot_drp_cnt else "0.0%",
        f"{(all_da / tot_drp_cnt * 100):.1f}%" if tot_drp_cnt else "0.0%",
        f"{(all_ds / tot_drp_cnt * 100):.1f}%" if tot_drp_cnt else "0.0%",
        "-", "-", "-", "-", "-"
    ]))
    layout["t2a_end"] = len(rows)
    rows.append(pad_row([]))  # Spacer

    # Table 2B: Practice Area & Product Tier Progression Table
    layout["t2b_title_idx"] = len(rows)
    rows.append(pad_row(["PRACTICE AREA & PRODUCT TIER PROGRESSION TABLE"]))
    layout["t2b_header_idx"] = len(rows)
    rows.append(pad_row([
        "Practice Area",
        "Product",
        "Tier 4 ➔ Tier 3",
        "Tier 3 ➔ Tier 2",
        "Tier 2 ➔ Tier 1",
        "Total Upgrades",
        "July Upgrades",
        "August Upgrades",
        "September Upgrades",
        "Unique Profiles",
        "DRP Partner Key",
        "Growth Velocity Rating",
        "Primary Upgrade Stage",
        "Status"
    ]))

    layout["t2b_data_start"] = len(rows)
    layout["t2b_has_data"] = bool(partner_drp_transitions)
    if partner_drp_transitions:
        drp_prod_groups = defaultdict(list)
        for d in partner_drp_transitions:
            key = (d["practice_area"], d["product"], d["drp_key"])
            drp_prod_groups[key].append(d)

        sorted_prod_keys = sorted(drp_prod_groups.keys(), key=lambda k: (k[0], k[1]))

        tot_p_t43 = tot_p_t32 = tot_p_t21 = tot_p_all = tot_p_j = tot_p_a = tot_p_s = 0
        tot_p_uprofs = set()

        for k in sorted_prod_keys:
            pa, prod, p_key = k
            grp = drp_prod_groups[k]

            c_t43 = sum(1 for d in grp if d["transition"] == "Tier 4 ➔ Tier 3")
            c_t32 = sum(1 for d in grp if d["transition"] == "Tier 3 ➔ Tier 2")
            c_t21 = sum(1 for d in grp if d["transition"] == "Tier 2 ➔ Tier 1")
            c_tot = len(grp)

            c_j = sum(1 for d in grp if d["month_num"] == 7)
            c_a = sum(1 for d in grp if d["month_num"] == 8)
            c_s = sum(1 for d in grp if d["month_num"] == 9)

            c_prof = len(set(d["profile_id"] for d in grp))
            for d in grp:
                tot_p_uprofs.add(d["profile_id"])

            tot_p_t43 += c_t43; tot_p_t32 += c_t32; tot_p_t21 += c_t21; tot_p_all += c_tot
            tot_p_j += c_j; tot_p_a += c_a; tot_p_s += c_s

            rating = "🔥 High Velocity (10+)" if c_tot >= 10 else ("🚀 Steady Growth (3-9)" if c_tot >= 3 else "🌱 Emerging (1-2)")
            max_stg = "Tier 4 ➔ Tier 3"
            if c_t32 > c_t43 and c_t32 >= c_t21:
                max_stg = "Tier 3 ➔ Tier 2"
            elif c_t21 > c_t43 and c_t21 > c_t32:
                max_stg = "Tier 2 ➔ Tier 1"

            rows.append(pad_row([
                pa,
                prod,
                c_t43, c_t32, c_t21,
                c_tot,
                c_j, c_a, c_s,
                c_prof,
                p_key,
                rating,
                max_stg,
                "Active"
            ]))

        layout["t2b_tot_idx"] = len(rows)
        rows.append(pad_row([
            "TOTAL",
            "-",
            tot_p_t43, tot_p_t32, tot_p_t21,
            tot_p_all,
            tot_p_j, tot_p_a, tot_p_s,
            len(tot_p_uprofs),
            "-", "-", "-", "-"
        ]))
    else:
        layout["t2b_tot_idx"] = len(rows)
        rows.append(pad_row(["No DRP tier promotions recorded for this partner in Q3 2026"]))
    layout["t2b_end"] = len(rows)
    rows.append(pad_row([]))  # Spacer

    # Table 2C: Practitioner Profiles Progression Detail Table
    layout["t2c_title_idx"] = len(rows)
    rows.append(pad_row(["PRACTITIONER PROFILES PROGRESSION DETAIL (INDIVIDUAL LEVEL TRANSITIONS)"]))
    layout["t2c_header_idx"] = len(rows)
    rows.append(pad_row([
        "Profile ID",
        "Practice Area",
        "Product",
        "Tier Movement",
        "Transition Month",
        "Transition Date",
        "Previous Score",
        "New Score",
        "Score Delta",
        "Previous Tier",
        "New Tier",
        "DRP Partner Key",
        "Promotion Type",
        "Status"
    ]))

    layout["t2c_data_start"] = len(rows)
    layout["t2c_has_data"] = bool(partner_drp_transitions)
    if partner_drp_transitions:
        sorted_drp = sorted(partner_drp_transitions, key=lambda d: (d["month_num"], d["date"], d["practice_area"]))
        for d in sorted_drp:
            rows.append(pad_row([
                d["profile_id"],
                d["practice_area"],
                d["product"],
                d["transition"],
                d["month_name"],
                d["date"],
                f"{d['prev_score']:.1f}",
                f"{d['score']:.1f}",
                f"+{d['score_delta']:.1f}",
                d["prev_tier"],
                d["new_tier"],
                d["drp_key"],
                "Tier Upgrade",
                "Promoted"
            ]))
    else:
        rows.append(pad_row(["No individual practitioner transitions recorded for this partner in Q3 2026"]))
    layout["t2c_end"] = len(rows)

    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    return len(rows), layout

def apply_growth_tab_formatting(ssid, sid, layout, gsheets_cli=GSHEETS):
    """
    Applies unified Google Sheets styles, borders, alignments, and number formats.
    """
    batch_req = {"requests": []}

    # 1. Column Widths
    widths = {
        0: 220,  # Account Name / Stage Transition / Practice Area / Profile ID
        1: 240,  # Workload Name / July (#) / Product
        2: 140,  # ARR USD / July ($) / T4->T3
        3: 130,  # Stage Movement / Aug (#) / T3->T2
        4: 110,  # Month / Aug ($) / T2->T1
        5: 100,  # Date / Sep (#) / Total Upgrades
        6: 140,  # Prev Progress / Sep ($) / July
        7: 140,  # New Progress / Q3 Total (#) / August
        8: 140,  # Current Progress / Q3 Total ($) / September
        9: 150,  # Workload Owner / Share / Unique Profiles
        10: 160, # Pillar / Top Pillar / DRP Key
        11: 180, # Opportunity / Avg Deal / Rating
        12: 140, # Partner ID / Momentum / Primary Stage
        13: 120  # Status
    }
    for col_idx, w in widths.items():
        batch_req["requests"].append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sid,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1
                },
                "properties": {"pixelSize": w},
                "fields": "pixelSize"
            }
        })

    # 2. Frozen Row 4 & Frozen Column A
    batch_req["requests"].append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sid,
                "gridProperties": {
                    "frozenRowCount": layout.get("freeze_row", 4),
                    "frozenColumnCount": 1
                }
            },
            "fields": "gridProperties(frozenRowCount,frozenColumnCount)"
        }
    })

    # 3. Header Block (Rows 0, 1, 2)
    # Row 0: Main Title (Google Blue)
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": TOTAL_COLS
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.102, "green": 0.459, "blue": 0.910},
                    "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True, "fontSize": 12},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })
    # Row 1: Subtitle (Soft Blue)
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": TOTAL_COLS
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.910, "green": 0.941, "blue": 0.996},
                    "textFormat": {"foregroundColor": {"red": 0.090, "green": 0.306, "blue": 0.651}, "bold": True, "fontSize": 10},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })
    # Row 2: Metadata (Muted Gray italic)
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": TOTAL_COLS
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1, "green": 1, "blue": 1},
                    "textFormat": {"foregroundColor": {"red": 0.439, "green": 0.459, "blue": 0.478}, "italic": True, "fontSize": 9},
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    # Helper function for Section Banners (Dark Navy #174EA6)
    def add_section_banner(row_idx):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.090, "green": 0.306, "blue": 0.651},
                        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True, "fontSize": 11},
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        })

    # Helper function for Table Title Banners (Google Blue #1A73E8)
    def add_table_title(row_idx):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.102, "green": 0.459, "blue": 0.910},
                        "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1}, "bold": True, "fontSize": 10},
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        })

    # Helper function for Table Headers (Soft Blue #D2E3FC)
    def add_table_header(row_idx):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.824, "green": 0.890, "blue": 0.988},
                        "textFormat": {"foregroundColor": {"red": 0.090, "green": 0.306, "blue": 0.651}, "bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        })

    # Helper function for Total rows (Soft Gray/Blue #E8F0FE)
    def add_total_row(row_idx):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.910, "green": 0.941, "blue": 0.996},
                        "textFormat": {"foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}, "bold": True, "fontSize": 10},
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"
            }
        })

    # Apply Section & Table headers
    if "sec1_title_idx" in layout:
        add_section_banner(layout["sec1_title_idx"])
    if "t1a_header_idx" in layout:
        add_table_header(layout["t1a_header_idx"])
    if "t1a_tot_idx" in layout:
        add_total_row(layout["t1a_tot_idx"])

    if "t1b_title_idx" in layout:
        add_table_title(layout["t1b_title_idx"])
    if "t1b_header_idx" in layout:
        add_table_header(layout["t1b_header_idx"])

    if "sec2_title_idx" in layout:
        add_section_banner(layout["sec2_title_idx"])
    if "t2a_header_idx" in layout:
        add_table_header(layout["t2a_header_idx"])
    if "t2a_tot_idx" in layout:
        add_total_row(layout["t2a_tot_idx"])

    if "t2b_title_idx" in layout:
        add_table_title(layout["t2b_title_idx"])
    if "t2b_header_idx" in layout:
        add_table_header(layout["t2b_header_idx"])
    if "t2b_tot_idx" in layout and layout.get("t2b_has_data"):
        add_total_row(layout["t2b_tot_idx"])

    if "t2c_title_idx" in layout:
        add_table_title(layout["t2c_title_idx"])
    if "t2c_header_idx" in layout:
        add_table_header(layout["t2c_header_idx"])

    # Cell alignments for Table 1A data
    if "t1a_data_start" in layout and "t1a_end" in layout:
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": layout["t1a_data_start"],
                    "endRowIndex": layout["t1a_end"],
                    "startColumnIndex": 1,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"
            }
        })

    # Cell alignments for Table 1B data
    if "t1b_data_start" in layout and "t1b_end" in layout and layout.get("t1b_has_data"):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": layout["t1b_data_start"],
                    "endRowIndex": layout["t1b_end"],
                    "startColumnIndex": 2,
                    "endColumnIndex": 9
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"
            }
        })

    # Cell alignments for Table 2A data
    if "t2a_data_start" in layout and "t2a_end" in layout:
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": layout["t2a_data_start"],
                    "endRowIndex": layout["t2a_end"],
                    "startColumnIndex": 1,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"
            }
        })

    # Cell alignments for Table 2B data
    if "t2b_data_start" in layout and "t2b_end" in layout and layout.get("t2b_has_data"):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": layout["t2b_data_start"],
                    "endRowIndex": layout["t2b_end"],
                    "startColumnIndex": 2,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"
            }
        })

    # Cell alignments for Table 2C data
    if "t2c_data_start" in layout and "t2c_end" in layout and layout.get("t2c_has_data"):
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": layout["t2c_data_start"],
                    "endRowIndex": layout["t2c_end"],
                    "startColumnIndex": 3,
                    "endColumnIndex": TOTAL_COLS
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)"
            }
        })

    # Execute formatting batch
    tmp_batch = f"/tmp/growth_batch_{sid}.json"
    with open(tmp_batch, "w") as f:
        json.dump(batch_req, f)

    res = subprocess.run([gsheets_cli, "mutate", "raw-batch", ssid, "-f", tmp_batch], capture_output=True, text=True)
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)

    # 4. Hyperlink copy-paste activation for Table 1B
    if layout.get("t1b_has_data") and "t1b_data_start" in layout and "t1b_end" in layout:
        st_r = layout["t1b_data_start"]
        end_r = layout["t1b_end"]
        copy_req = {
            "requests": [
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": sid,
                            "startRowIndex": st_r,
                            "endRowIndex": end_r,
                            "startColumnIndex": 0,
                            "endColumnIndex": 2
                        },
                        "destination": {
                            "sheetId": sid,
                            "startRowIndex": st_r,
                            "endRowIndex": end_r,
                            "startColumnIndex": 0,
                            "endColumnIndex": 2
                        },
                        "pasteType": "PASTE_NORMAL",
                        "pasteOrientation": "NORMAL"
                    }
                },
                {
                    "copyPaste": {
                        "source": {
                            "sheetId": sid,
                            "startRowIndex": st_r,
                            "endRowIndex": end_r,
                            "startColumnIndex": 11,
                            "endColumnIndex": 12
                        },
                        "destination": {
                            "sheetId": sid,
                            "startRowIndex": st_r,
                            "endRowIndex": end_r,
                            "startColumnIndex": 11,
                            "endColumnIndex": 12
                        },
                        "pasteType": "PASTE_NORMAL",
                        "pasteOrientation": "NORMAL"
                    }
                }
            ]
        }
        tmp_copy = f"/tmp/growth_copy_{sid}.json"
        with open(tmp_copy, "w") as f:
            json.dump(copy_req, f)
        subprocess.run([gsheets_cli, "mutate", "raw-batch", ssid, "-f", tmp_copy], capture_output=True)
        if os.path.exists(tmp_copy):
            os.remove(tmp_copy)

def ensure_sheet_tab(ssid, tab_title, gsheets_cli=GSHEETS):
    res = subprocess.run([gsheets_cli, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            sheets = json.loads(res.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    subprocess.run([gsheets_cli, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    res2 = subprocess.run([gsheets_cli, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res2.returncode == 0 and res2.stdout.strip():
        try:
            sheets = json.loads(res2.stdout)
            for s in sheets:
                if s.get("title") == tab_title:
                    return s.get("id")
        except:
            pass
    return None

def update_partner_growth_tab(cfg, partner_wkl_transitions, partner_drp_transitions, gsheets_cli=GSHEETS):
    """
    Main entry point to build, upload, format, and activate the Growth tab for a partner.
    """
    pname = cfg["partner"]
    ssid = cfg["sheet_id"]
    safe_name = pname.replace(" ", "_").replace("(", "_").replace(")", "_").replace("/", "_").replace("&", "_")
    csv_path = os.path.join("growth_data_latest", f"{safe_name}_growth.csv")

    row_count, layout = build_growth_csv_and_layout(cfg, partner_wkl_transitions, partner_drp_transitions, csv_path)

    # Ensure 'Growth' tab exists
    sid = ensure_sheet_tab(ssid, "Growth", gsheets_cli)
    if sid is None:
        print(f"Warning: Could not get sheetId for Growth tab in {ssid} ({pname})")
        return False

    # Clear old data
    subprocess.run([gsheets_cli, "mutate", "clear", ssid, "'Growth'!A1:Z5000"], capture_output=True)

    # Import CSV
    res_imp = subprocess.run([gsheets_cli, "mutate", "import-csv", ssid, csv_path, "--sheet", "Growth"], capture_output=True, text=True)
    if res_imp.returncode != 0:
        print(f"Error importing CSV to Growth tab for {pname}: {res_imp.stderr}")
        return False

    # Apply formatting and activate hyperlinks
    apply_growth_tab_formatting(ssid, sid, layout, gsheets_cli)
    print(f"✓ Growth tab updated and styled for {pname} ({row_count} rows).")
    return True
