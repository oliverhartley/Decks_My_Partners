#!/usr/bin/env python3
"""
send_aggregated_workload_alerts.py

Scans "Partner Management Dashboard - Oliver Hartley" for qualifying workloads:
- Critical (<= 14 days or overdue in Stages 0-2 & 3)
- High (15-30 days in Stages 0-2 & 3)
- Priority (Marked as Priority in Business Priority column)

Aggregates workloads by Workload Owner Email so each owner receives a single consolidated email.
Supports test mode where aggregated workloads from multiple owners are sent to specified test emails.
Includes stage-specific specifications (Stage 0-2 vs Stage 3), risk badges, and the latest Next Steps history.
"""

import os
import sys
import re
import csv
import json
import argparse
import datetime
import subprocess
import tempfile

GMAIL = "/google/bin/releases/gemini-agents-gmail/gmail"
GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
OLIVER_SSID = "1VkmmtXJopJ57K_XL3jwdqk8LrN6qw0_iGrBbl5deYpI"
OLIVER_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{OLIVER_SSID}/edit"
GLOBAL_LATEST_CSV = "global_dashboard_data/all_workloads_followup_latest.csv"


def extract_hyperlink(cell_str):
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', cell_str)
    if m:
        return m.group(2).strip(), m.group(1).strip()
    return cell_str.strip(), ""


def load_url_mappings(global_csv_path=GLOBAL_LATEST_CSV):
    url_map = {}
    if not os.path.exists(global_csv_path):
        return url_map

    with open(global_csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    for r in rows[5:]:
        if len(r) < 5:
            continue
        p_name, p_url = extract_hyperlink(r[1])
        c_name, c_url = extract_hyperlink(r[2])
        w_name, w_url = extract_hyperlink(r[4])
        o_name, o_url = extract_hyperlink(r[9]) if len(r) > 9 else ("", "")
        er_name, er_url = extract_hyperlink(r[11]) if len(r) > 11 else ("", "")

        key = (p_name.strip().lower(), c_name.strip().lower(), w_name.strip().lower())
        url_map[key] = {
            "w_url": w_url,
            "c_url": c_url,
            "p_url": p_url,
            "o_url": o_url,
            "er_url": er_url
        }
    return url_map


def export_oliver_dashboard(output_csv="/tmp/oliver_followup.csv", refresh=False):
    if not refresh and os.path.exists(output_csv):
        return output_csv

    cmd = [
        GSHEETS, "readonly", "export",
        OLIVER_SSID, output_csv,
        "--sheet", "All_Workloads_Follow_up"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to export Oliver Hartley dashboard: {res.stderr or res.stdout}")
    return output_csv


def fetch_and_evaluate_workloads(csv_path="/tmp/oliver_followup.csv", target_date=None):
    if target_date is None:
        today = datetime.date.today()
    else:
        today = target_date

    url_map = load_url_mappings()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if len(rows) < 6:
        return []

    headers = [h.strip() for h in rows[4]]
    col_map = {h: idx for idx, h in enumerate(headers)}

    pe_idx = col_map.get("Partner Engineer (PE)", 0)
    partner_idx = col_map.get("Partner Name", 1)
    cust_idx = col_map.get("Customer Account Name", 2)
    tier_idx = col_map.get("Account Tier", 3)
    wkl_idx = col_map.get("Workload Name", 4)
    owner_idx = col_map.get("Workload Owner", 5)
    arr_idx = col_map.get("Annual Gross Revenue (ARR USD)", 6)
    progress_idx = col_map.get("Workload Progress", 7)
    cap_idx = col_map.get("Capacity Status (DRP Readiness)", 8)
    opp_idx = col_map.get("Opportunity Name", 9)
    next_steps_idx = col_map.get("Next Steps", 10)
    er_idx = col_map.get("Expert Requests", 11)
    prod_date_idx = col_map.get("Production Date", 17)
    owner_email_idx = col_map.get("Workload Owner Email", 18)
    notes_idx = col_map.get("Notes / Tasks", 19)
    last_update_idx = col_map.get("Last Update", 20)
    priority_idx = col_map.get("Business Priority", 21)

    evaluated_workloads = []

    for row_num, r in enumerate(rows[5:], start=6):
        if len(r) <= max(prod_date_idx, owner_email_idx):
            continue

        owner_email = r[owner_email_idx].strip().lower()
        if not owner_email:
            continue

        wkl_name = r[wkl_idx].strip()
        cust_name = r[cust_idx].strip()
        partner_name = r[partner_idx].strip()
        owner_name = r[owner_idx].strip()
        progress = r[progress_idx].strip()
        arr_val = r[arr_idx].strip()
        cap_status = r[cap_idx].strip() if len(r) > cap_idx else ""
        opp_name = r[opp_idx].strip() if len(r) > opp_idx else ""
        next_steps = r[next_steps_idx].strip() if len(r) > next_steps_idx else ""
        er_val = r[er_idx].strip() if len(r) > er_idx else ""
        prod_date_str = r[prod_date_idx].strip() if len(r) > prod_date_idx else ""
        notes = r[notes_idx].strip() if len(r) > notes_idx else ""
        last_update = r[last_update_idx].strip() if len(r) > last_update_idx else ""
        priority_val = r[priority_idx].strip() if len(r) > priority_idx else ""
        is_priority = bool(priority_val)

        # Stage classification
        is_stage_0_2 = progress.startswith("0-2")
        is_stage_3 = progress.startswith("3:")
        is_active_pipeline = is_stage_0_2 or is_stage_3

        # Parse target date
        prod_date = None
        days_diff = None
        days_status = "Date Unspecified"
        risk_level = "Normal"

        if prod_date_str:
            try:
                prod_date = datetime.datetime.strptime(prod_date_str[:10], "%Y-%m-%d").date()
                days_diff = (prod_date - today).days
                if days_diff < 0:
                    days_status = f"🔴 OVERDUE by {abs(days_diff)} days"
                elif days_diff == 0:
                    days_status = "🔴 DUE TODAY"
                else:
                    days_status = f"{days_diff} days remaining"

                if is_active_pipeline:
                    if days_diff <= 14:
                        risk_level = "Critical"
                    elif days_diff <= 30:
                        risk_level = "High"
                    elif days_diff <= 45:
                        risk_level = "Medium"
                    else:
                        risk_level = "Normal"
                else:
                    risk_level = "Normal"
            except ValueError:
                days_status = f"Invalid Date ({prod_date_str})"
                risk_level = "Normal"

        # Check qualification: Critical OR High in active pipeline, OR marked as Priority
        is_critical = risk_level == "Critical"
        is_high = risk_level == "High"
        qualifies = is_critical or is_high or is_priority

        if not qualifies:
            continue

        # Lookup URLs
        key = (partner_name.lower(), cust_name.lower(), wkl_name.lower())
        urls = url_map.get(key, {})
        if not urls:
            for k, u in url_map.items():
                if k[2] == wkl_name.lower():
                    urls = u
                    break

        wkl_url = urls.get("w_url", "")
        cust_url = urls.get("c_url", "")
        partner_url = urls.get("p_url", "")
        opp_url = urls.get("o_url", "")
        er_url = urls.get("er_url", "")

        stage_type = "stage_0_2" if is_stage_0_2 else ("stage_3" if is_stage_3 else "other")

        evaluated_workloads.append({
            "row_number": row_num,
            "partner_engineer": r[pe_idx].strip(),
            "partner_name": partner_name,
            "partner_url": partner_url,
            "customer_name": cust_name,
            "customer_url": cust_url,
            "tier": r[tier_idx].strip(),
            "workload_name": wkl_name,
            "workload_url": wkl_url,
            "owner_name": owner_name,
            "owner_email": owner_email,
            "arr": arr_val,
            "progress": progress,
            "stage_type": stage_type,
            "production_date": str(prod_date) if prod_date else prod_date_str,
            "days_diff": days_diff,
            "days_status": days_status,
            "risk_level": risk_level,
            "is_priority": is_priority,
            "priority_val": priority_val,
            "capacity_status": cap_status,
            "opportunity_name": opp_name,
            "opportunity_url": opp_url,
            "expert_requests": er_val,
            "expert_requests_url": er_url,
            "next_steps": next_steps,
            "notes": notes,
            "last_update": last_update
        })

    return evaluated_workloads


def get_risk_components(risk_level, is_priority=False):
    if risk_level == "Critical":
        dot = "🔴"
        badge = '<span style="background-color: #fce8e6; color: #c5221f; border: 1px solid #ea4335; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">CRITICAL</span>'
    elif risk_level == "High":
        dot = "🔴"
        badge = '<span style="background-color: #fde8e8; color: #b06000; border: 1px solid #f9ab00; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">🌸 HIGH</span>'
    elif risk_level == "Medium":
        dot = "🟡"
        badge = '<span style="background-color: #fef7e0; color: #b06000; border: 1px solid #f9ab00; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">MEDIUM</span>'
    else:
        dot = "⚪"
        badge = '<span style="background-color: #f1f3f4; color: #5f6368; border: 1px solid #dadce0; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">NORMAL</span>'

    prio_badge = ""
    if is_priority:
        prio_badge = '<span style="background-color: #e8f0fe; color: #1a73e8; border: 1px solid #1a73e8; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase; margin-right: 8px; vertical-align: middle;">⭐ PRIORITY</span>'

    return dot, badge, prio_badge


def build_workload_card_html(wkl):
    is_0_2 = wkl["stage_type"] == "stage_0_2"
    is_3 = wkl["stage_type"] == "stage_3"

    if is_0_2:
        action_title = "Action Required (Stage 0-2: Tech Eval / Solution Dev)"
        action_desc = f"""This workload is scheduled to go live on <strong>{wkl['production_date']}</strong> (<strong>{wkl['days_status']}</strong>).<br>
👉 <strong>Please check and confirm if this workload will realistically be in production by {wkl['production_date']}.</strong><br>
If there is any shift or delay, <strong>please update the Production Date in Salesforce / Concord as soon as possible.</strong>"""
        banner_bg = "#e8f0fe"
        banner_border = "#1a73e8"
        banner_color = "#174ea6"
    elif is_3:
        action_title = "Action Required (Stage 3: Proposal / Negotiation)"
        action_desc = f"""With production scheduled for <strong>{wkl['production_date']}</strong> (<strong>{wkl['days_status']}</strong>):<br>
👉 <strong>Please confirm that there is no technical issue and no blocking dependencies with partner ({wkl['partner_name']}).</strong>"""
        banner_bg = "#fef7e0"
        banner_border = "#f9ab00"
        banner_color = "#b06000"
    else:
        action_title = f"Priority Workload Attention ({wkl['progress']})"
        action_desc = f"👉 <strong>Priority Workload Review:</strong> Target Production Date is <strong>{wkl['production_date']}</strong>. Please ensure key milestones are progressing as planned."
        banner_bg = "#f1f3f4"
        banner_border = "#5f6368"
        banner_color = "#3c4043"

    w_link = f'<a href="{wkl["workload_url"]}" style="color: #1a73e8; text-decoration: none; font-weight: bold;">{wkl["workload_name"]} ↗</a>' if wkl["workload_url"] else f'<strong>{wkl["workload_name"]}</strong>'
    c_link = f'<a href="{wkl["customer_url"]}" style="color: #1a73e8; text-decoration: none;">{wkl["customer_name"]} ↗</a>' if wkl["customer_url"] else wkl["customer_name"]
    p_link = f'<a href="{wkl["partner_url"]}" style="color: #1a73e8; text-decoration: none;">{wkl["partner_name"]} ↗</a>' if wkl["partner_url"] else wkl["partner_name"]

    dot_icon, risk_badge_html, prio_badge_html = get_risk_components(wkl["risk_level"], wkl["is_priority"])

    next_step_content = wkl["next_steps"] if wkl["next_steps"] else "<em>No Next Steps registered in Concord</em>"
    notes_content = f"<br><strong>Notes / Tasks:</strong> {wkl['notes']}" if wkl["notes"] else ""
    last_update_content = f"<br><strong>Last Update:</strong> {wkl['last_update']}" if wkl["last_update"] else ""

    card_html = f"""
    <div style="background: #ffffff; border: 1px solid #dadce0; border-radius: 8px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 1px 3px rgba(60,64,67,0.08);">
      <div style="background-color: #f8f9fa; border-bottom: 1px solid #dadce0; padding: 12px 16px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="text-align: left; vertical-align: middle;">
              <span style="font-size: 13px; vertical-align: middle; margin-right: 6px;">{dot_icon}</span>
              <span style="vertical-align: middle; margin-right: 8px;">{risk_badge_html}</span>
              {prio_badge_html}
              <span style="font-size: 15px; font-weight: bold; color: #202124; vertical-align: middle;">{w_link}</span>
              <span style="font-size: 12px; color: #5f6368; margin-left: 6px; vertical-align: middle;">({c_link} &bull; {wkl['tier']})</span>
            </td>
          </tr>
        </table>
      </div>

      <div style="padding: 16px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 14px;">
          <tbody>
            <tr>
              <td style="padding: 6px 0; color: #5f6368; width: 25%;"><strong>Partner:</strong></td>
              <td style="padding: 6px 0; color: #202124; width: 35%;"><strong>{p_link}</strong></td>
              <td style="padding: 6px 0; color: #5f6368; width: 20%;"><strong>ARR (USD):</strong></td>
              <td style="padding: 6px 0; color: #137333; font-weight: bold; width: 20%;">{wkl['arr']}</td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #5f6368;"><strong>Stage / Progress:</strong></td>
              <td style="padding: 6px 0; color: #202124;"><strong>{wkl['progress']}</strong></td>
              <td style="padding: 6px 0; color: #5f6368;"><strong>Production Date:</strong></td>
              <td style="padding: 6px 0; color: {'#c5221f' if wkl['risk_level'] == 'Critical' else ('#b06000' if wkl['risk_level'] == 'High' else '#202124')}; font-weight: bold;">
                {wkl['production_date']} ({wkl['days_status']})
              </td>
            </tr>
            <tr>
              <td style="padding: 6px 0; color: #5f6368;"><strong>Capacity Status:</strong></td>
              <td style="padding: 6px 0; color: #202124;">{wkl['capacity_status']}</td>
              <td style="padding: 6px 0; color: #5f6368;"><strong>Opportunity:</strong></td>
              <td style="padding: 6px 0; color: #202124;">{wkl['opportunity_name'] if wkl['opportunity_name'] else '-'}</td>
            </tr>
          </tbody>
        </table>

        <!-- Stage Action Banner -->
        <div style="background-color: {banner_bg}; border-left: 4px solid {banner_border}; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px; font-size: 13px; line-height: 1.5;">
          <strong style="color: {banner_color};">{action_title}</strong><br>
          {action_desc}
        </div>

        <!-- Next Steps History -->
        <div style="background-color: #f8f9fa; border: 1px solid #e8eaed; border-radius: 4px; padding: 10px 14px; font-size: 12px; color: #3c4043; line-height: 1.5;">
          <strong style="color: #202124;">📋 Next Steps History & Tracking:</strong><br>
          {next_step_content}
          {notes_content}
          {last_update_content}
        </div>
      </div>
    </div>
    """
    return card_html


def build_owner_email(owner_email, owner_wkls, simulation_recipients=None):
    today_str = datetime.date.today().strftime("%d %b %Y")
    is_test = bool(simulation_recipients)
    owner_name = owner_wkls[0]["owner_name"] if owner_wkls else owner_email.split("@")[0].title()

    total_wkls = len(owner_wkls)
    crit_count = sum(1 for w in owner_wkls if w["risk_level"] == "Critical")
    high_count = sum(1 for w in owner_wkls if w["risk_level"] == "High")
    prio_count = sum(1 for w in owner_wkls if w["is_priority"])

    tot_arr = 0.0
    for w in owner_wkls:
        try:
            tot_arr += float(w["arr"].replace("$", "").replace(",", "").strip())
        except:
            pass

    test_banner_html = ""
    if is_test:
        if len(simulation_recipients) > 1:
            rec_str = f"To: {simulation_recipients[0]} &bull; CC: {', '.join(simulation_recipients[1:])}"
        elif simulation_recipients:
            rec_str = f"To: {simulation_recipients[0]}"
        else:
            rec_str = "None"
        test_banner_html = f"""
        <div style="background-color: #fce8e6; border: 1px dashed #d93025; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; color: #c5221f;">
          <strong>⚠️ SIMULATION ALERT &bull; IN-FLIGHT TEST</strong><br>
          In production, this automated notification is delivered directly to: <strong>{owner_name} &lt;{owner_email}&gt;</strong>.<br>
          Test Delivery Target: <strong>{rec_str}</strong>
        </div>
        """

    crit_part = f"{crit_count} Critical 🔴, " if crit_count > 0 else ""
    high_part = f"{high_count} High 🌸" if high_count > 0 else ""
    breakdown_str = f"({crit_part}{high_part})".replace(", )", ")") if (crit_count or high_count) else ""

    subject = f"{'[TEST for ' + owner_name + '] ' if is_test else ''}[Action Required] Workload Pipeline Alert: {total_wkls} Workload(s) Requiring Attention {breakdown_str}".strip()

    cards_html = "".join([build_workload_card_html(w) for w in owner_wkls])

    html_body = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #202124; line-height: 1.5; max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #dadce0; border-radius: 8px;">
      {test_banner_html}

      <div style="background-color: #ffffff; border-bottom: 2px solid #ea4335; padding-bottom: 14px; margin-bottom: 20px;">
        <h2 style="color: #c5221f; margin: 0 0 6px 0; font-size: 20px;">
          🔴 Workload Action Alerts & Pipeline Status
        </h2>
        <span style="font-size: 13px; color: #5f6368;">
          Assigned to: <strong>{owner_name}</strong> (&lt;{owner_email}&gt;) &bull; Date: <strong>{today_str}</strong>
        </span>
      </div>

      <p style="margin-bottom: 20px;">
        Hi <strong>{owner_name}</strong>,<br>
        The following <strong>{total_wkls} workloads</strong> in your portfolio currently require immediate confirmation or follow-up due to approaching target production dates or business priority status.
      </p>

      <!-- KPI Summary Cards -->
      <table style="width: 100%; border-collapse: separate; border-spacing: 10px 0; margin-bottom: 24px;">
        <tbody>
          <tr>
            <td style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #5f6368; text-transform: uppercase; font-weight: bold;">Total Attention</span><br>
              <span style="font-size: 22px; font-weight: bold; color: #202124;">{total_wkls}</span>
            </td>
            <td style="background-color: #fce8e6; border: 1px solid #ea4335; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #c5221f; text-transform: uppercase; font-weight: bold;">🔴 Critical (≤14d)</span><br>
              <span style="font-size: 22px; font-weight: bold; color: #c5221f;">{crit_count}</span>
            </td>
            <td style="background-color: #fef7e0; border: 1px solid #f9ab00; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #b06000; text-transform: uppercase; font-weight: bold;">🌸 High (15-30d)</span><br>
              <span style="font-size: 22px; font-weight: bold; color: #b06000;">{high_count}</span>
            </td>
            <td style="background-color: #e6f4ea; border: 1px solid #34a853; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #137333; text-transform: uppercase; font-weight: bold;">Total ARR (USD)</span><br>
              <span style="font-size: 20px; font-weight: bold; color: #137333;">${tot_arr:,.2f}</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Detailed Workload Cards -->
      {cards_html}

      <!-- Footer -->
      <div style="margin-top: 30px; border-top: 1px solid #dadce0; padding-top: 16px; font-size: 12px; color: #5f6368; text-align: center;">
        Automated Partner Workload Intelligence &bull; Partner Engineer: <strong>Oliver Hartley</strong><br>
        <a href="{OLIVER_SHEET_URL}" style="color: #1a73e8; text-decoration: none;">Open Partner Management Dashboard - Oliver Hartley ↗</a>
      </div>
    </div>
    """

    return {
        "owner_email": owner_email,
        "owner_name": owner_name,
        "subject": subject,
        "html_body": html_body,
        "total_wkls": total_wkls
    }


def build_consolidated_email(workloads, target_owners, simulation_recipients=None):
    today_str = datetime.date.today().strftime("%d %b %Y")
    is_test = bool(simulation_recipients)

    by_owner = {}
    for w in workloads:
        e = w["owner_email"]
        by_owner.setdefault(e, []).append(w)

    total_wkls = len(workloads)
    crit_count = sum(1 for w in workloads if w["risk_level"] == "Critical")
    high_count = sum(1 for w in workloads if w["risk_level"] == "High")
    prio_count = sum(1 for w in workloads if w["is_priority"])

    tot_arr = 0.0
    for w in workloads:
        try:
            tot_arr += float(w["arr"].replace("$", "").replace(",", "").strip())
        except:
            pass

    test_banner_html = ""
    if is_test:
        if len(simulation_recipients) > 1:
            rec_str = f"To: {simulation_recipients[0]} &bull; CC: {', '.join(simulation_recipients[1:])}"
        elif simulation_recipients:
            rec_str = f"To: {simulation_recipients[0]}"
        else:
            rec_str = "None"
        owner_label = by_owner[target_owners[0]][0]['owner_name'] if len(target_owners) == 1 and target_owners[0] in by_owner else f"{len(target_owners)} owners"
        test_banner_html = f"""
        <div style="background-color: #fce8e6; border: 1px dashed #d93025; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; color: #c5221f;">
          <strong>⚠️ TEST & SIMULATION EXECUTION</strong><br>
          This email aggregates all qualifying workloads for: <strong>{owner_label}</strong> (<em>{', '.join(target_owners)}</em>).<br>
          In production automation, each owner receives only their own personalized aggregated email.<br>
          Target Test Recipients: <strong>{rec_str}</strong>
        </div>
        """

    crit_part = f"{crit_count} Critical 🔴, " if crit_count > 0 else ""
    high_part = f"{high_count} High 🌸" if high_count > 0 else ""
    breakdown_str = f"({crit_part}{high_part})".replace(", )", ")") if (crit_count or high_count) else ""

    single_owner_tag = f" - {by_owner[target_owners[0]][0]['owner_name']}" if len(target_owners) == 1 and target_owners[0] in by_owner else ""
    subject = f"{'[TEST' + single_owner_tag + '] ' if is_test else ''}[Action Required] Aggregated Workload Alerts: {total_wkls} Workloads {breakdown_str}".strip()

    owner_sections_html = []
    for owner_email in target_owners:
        owner_wkls = by_owner.get(owner_email, [])
        if not owner_wkls:
            owner_name = owner_email.split("@")[0].title()
            owner_sections_html.append(f"""
            <div style="margin-top: 30px; border-top: 2px solid #e8eaed; padding-top: 20px;">
              <h3 style="color: #202124; margin-bottom: 8px;">👤 {owner_name} &bull; <a href="mailto:{owner_email}" style="color: #1a73e8; font-weight: normal; font-size: 14px;">{owner_email}</a></h3>
              <p style="font-size: 13px; color: #5f6368; font-style: italic;">No Critical, High, or Priority workloads currently requiring action.</p>
            </div>
            """)
            continue

        owner_name = owner_wkls[0]["owner_name"]
        o_crit = sum(1 for w in owner_wkls if w["risk_level"] == "Critical")
        o_high = sum(1 for w in owner_wkls if w["risk_level"] == "High")
        o_prio = sum(1 for w in owner_wkls if w["is_priority"])

        cards_html = "".join([build_workload_card_html(w) for w in owner_wkls])

        owner_section = f"""
        <div style="margin-top: 30px; border-top: 2px solid #1a73e8; padding-top: 20px;">
          <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
            <tr>
              <td style="text-align: left; vertical-align: baseline;">
                <h3 style="color: #202124; margin: 0; font-size: 18px;">
                  👤 {owner_name} <span style="font-size: 13px; color: #5f6368; font-weight: normal;">(&lt;{owner_email}&gt;)</span>
                </h3>
              </td>
              <td style="text-align: right; vertical-align: baseline;">
                <span style="font-size: 13px; color: #5f6368;">
                  <strong>{len(owner_wkls)}</strong> workloads ({o_crit} Critical, {o_high} High, {o_prio} Priority)
                </span>
              </td>
            </tr>
          </table>
          {cards_html}
        </div>
        """
        owner_sections_html.append(owner_section)

    all_owners_html = "".join(owner_sections_html)

    summary_rows = []
    for idx, e in enumerate(target_owners):
        w_list = by_owner.get(e, [])
        name = w_list[0]['owner_name'] if w_list else e
        c_num = sum(1 for w in w_list if w['risk_level'] == 'Critical')
        h_num = sum(1 for w in w_list if w['risk_level'] == 'High')
        p_num = sum(1 for w in w_list if w['is_priority'])
        bg = '#ffffff' if idx % 2 == 0 else '#f8f9fa'
        row_str = f"""<tr style="background-color: {bg};">
          <td style="padding: 8px 12px; border: 1px solid #dadce0;"><strong>{name}</strong> (&lt;{e}&gt;)</td>
          <td style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0; font-weight: bold; color: #c5221f;">{c_num}</td>
          <td style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0; font-weight: bold; color: #b06000;">{h_num}</td>
          <td style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0; font-weight: bold; color: #1a73e8;">{p_num}</td>
          <td style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0; font-weight: bold;">{len(w_list)}</td>
        </tr>"""
        summary_rows.append(row_str)

    html_body = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #202124; line-height: 1.5; max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #dadce0; border-radius: 8px;">
      {test_banner_html}

      <div style="background-color: #ffffff; border-bottom: 2px solid #ea4335; padding-bottom: 14px; margin-bottom: 20px;">
        <h2 style="color: #c5221f; margin: 0 0 6px 0; font-size: 20px;">
          🔴 Active Pipeline Alerts & Business Priorities
        </h2>
        <span style="font-size: 13px; color: #5f6368;">
          Evaluated from <strong>Partner Management Dashboard - Oliver Hartley</strong> &bull; Date: <strong>{today_str}</strong>
        </span>
      </div>

      <!-- KPI Summary Cards -->
      <table style="width: 100%; border-collapse: separate; border-spacing: 10px 0; margin-bottom: 24px;">
        <tbody>
          <tr>
            <td style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #5f6368; text-transform: uppercase; font-weight: bold;">Total Workloads</span><br>
              <span style="font-size: 22px; font-weight: bold; color: #202124;">{total_wkls}</span>
            </td>
            <td style="background-color: #fce8e6; border: 1px solid #ea4335; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #c5221f; text-transform: uppercase; font-weight: bold;">🔴 Critical (≤14d)</span><br>
              <span style="font-size: 22px; font-weight: bold; color: #c5221f;">{crit_count}</span>
            </td>
            <td style="background-color: #fef7e0; border: 1px solid #f9ab00; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #b06000; text-transform: uppercase; font-weight: bold;">🌸 High (15-30d)</span><br>
              <span style="font-size: 22px; font-weight: bold; color: #b06000;">{high_count}</span>
            </td>
            <td style="background-color: #e6f4ea; border: 1px solid #34a853; border-radius: 6px; padding: 12px; text-align: center; width: 25%;">
              <span style="font-size: 11px; color: #137333; text-transform: uppercase; font-weight: bold;">Total ARR (USD)</span><br>
              <span style="font-size: 20px; font-weight: bold; color: #137333;">${tot_arr:,.2f}</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Executive Overview Summary -->
      <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 24px; border: 1px solid #dadce0;">
        <thead>
          <tr style="background-color: #1a73e8; color: #ffffff;">
            <th style="padding: 8px 12px; text-align: left; border: 1px solid #dadce0;">Workload Owner</th>
            <th style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0;">Critical 🔴</th>
            <th style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0;">High 🌸</th>
            <th style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0;">Priority ⭐</th>
            <th style="padding: 8px 12px; text-align: center; border: 1px solid #dadce0;">Total Action Workloads</th>
          </tr>
        </thead>
        <tbody>
          {''.join(summary_rows)}
        </tbody>
      </table>

      <!-- Detailed Sections by Owner -->
      {all_owners_html}

      <!-- Footer -->
      <div style="margin-top: 30px; border-top: 1px solid #dadce0; padding-top: 16px; font-size: 12px; color: #5f6368; text-align: center;">
        Automated Partner Workload Intelligence &bull; Partner Engineer: <strong>Oliver Hartley</strong><br>
        <a href="{OLIVER_SHEET_URL}" style="color: #1a73e8; text-decoration: none;">Open Partner Management Dashboard - Oliver Hartley ↗</a>
      </div>
    </div>
    """

    return {
        "subject": subject,
        "html_body": html_body,
        "total_wkls": total_wkls,
        "by_owner": by_owner
    }


def send_email_via_cli(recipients, subject, html_body, cc=None):
    if isinstance(recipients, list):
        to_addr = recipients[0]
        cc_addrs = [c for c in recipients[1:]]
    else:
        to_addr = recipients
        cc_addrs = []

    if cc:
        if isinstance(cc, list):
            cc_addrs.extend(cc)
        else:
            cc_addrs.extend([c.strip() for c in cc.split(",") if c.strip()])

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_body)
        temp_html_path = f.name

    try:
        cmd = [
            GMAIL, "mutate", "send",
            "--to", to_addr,
            "--subject", subject,
            "--html",
            "--body-file", temp_html_path,
            "--ignore-sharing-checks"
        ]
        for c in cc_addrs:
            cmd.extend(["--cc", c])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Gmail CLI error: {res.stderr or res.stdout}")
        return res.stdout.strip()
    finally:
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)


def main():
    parser = argparse.ArgumentParser(description="Send aggregated workload alerts from Oliver Hartley dashboard.")
    parser.add_argument("--csv", default="/tmp/oliver_followup.csv", help="Path to exported Oliver Hartley followup CSV")
    parser.add_argument("--refresh", action="store_true", help="Force re-export of Oliver Hartley dashboard sheet")
    parser.add_argument("--owners", default="patricioperez@google.com,renanvaladares@google.com,vpimentel@google.com", help="Comma-separated owner emails")
    parser.add_argument("--recipients", default=None, help="Comma-separated recipient emails (first is To, others are CC)")
    parser.add_argument("--to", default=None, help="Primary recipient email (To:)")
    parser.add_argument("--cc", default=None, help="CC recipient email(s), comma-separated")
    parser.add_argument("--preview-file", default="/tmp/email_preview.html", help="Path to save HTML preview file")
    parser.add_argument("--mode", choices=["consolidated", "per-owner", "all"], default="consolidated", help="Send mode: consolidated (single email for all owners) or per-owner (separate email per owner) or all")
    parser.add_argument("--send", action="store_true", help="Actually execute sending via Gmail CLI")

    args = parser.parse_args()

    target_owners = [o.strip().lower() for o in args.owners.split(",") if o.strip()]

    recipients = []
    if args.to:
        recipients.append(args.to.strip())
        if args.cc:
            recipients.extend([c.strip() for c in args.cc.split(",") if c.strip()])
    elif args.recipients:
        recipients = [r.strip() for r in args.recipients.split(",") if r.strip()]
    else:
        recipients = ["oliver.hartley@gmail.com", "oliver@obiracing.com"]

    print("=================================================================")
    print("Aggregated Workload Alert Engine (Oliver Hartley Dashboard)")
    print("=================================================================")
    print(f"Target Owners ({len(target_owners)}): {', '.join(target_owners)}")
    print(f"Test Recipients ({len(recipients)}): {', '.join(recipients)}")
    print(f"Mode: {args.mode}")

    # Ensure export exists
    export_oliver_dashboard(output_csv=args.csv, refresh=args.refresh)

    # Evaluate workloads
    all_wkls = fetch_and_evaluate_workloads(csv_path=args.csv)
    print(f"Total qualifying workloads in dashboard: {len(all_wkls)}")

    # Filter for target owners
    filtered_wkls = [w for w in all_wkls if w["owner_email"] in target_owners]
    print(f"Total qualifying workloads for selected owners: {len(filtered_wkls)}\n")

    for owner_email in target_owners:
        ow = [w for w in filtered_wkls if w["owner_email"] == owner_email]
        print(f"👤 {owner_email}: {len(ow)} workloads")
        for w in ow:
            prio_tag = " [⭐ Priority]" if w["is_priority"] else ""
            print(f"   • [{w['risk_level']}] {w['workload_name']} ({w['customer_name']}) - ARR {w['arr']} - Prod: {w['production_date']} ({w['days_status']}){prio_tag}")
            if w['next_steps']:
                print(f"     Next Steps: {w['next_steps'][:70]}...")
            if w['notes']:
                print(f"     Notes / Tasks: {w['notes']}")
        print()

    # Consolidated email
    if args.mode in ["consolidated", "all"]:
        consolidated = build_consolidated_email(filtered_wkls, target_owners, simulation_recipients=recipients)
        with open(args.preview_file, "w", encoding="utf-8") as f:
            f.write(consolidated["html_body"])
        print(f"✓ Consolidated HTML preview generated at: {args.preview_file}")
        print(f"Consolidated Subject: {consolidated['subject']}")

        if args.send:
            print(f"\n-> Sending consolidated email to {recipients[0]}" + (f" (cc: {recipients[1]})" if len(recipients) > 1 else "") + "...")
            try:
                res = send_email_via_cli(recipients, consolidated["subject"], consolidated["html_body"])
                print(f"✓ Consolidated email sent! Result: {res}")
            except Exception as e:
                print(f"✗ Failed to send consolidated email: {e}")

    # Per-owner emails
    if args.mode in ["per-owner", "all"]:
        by_owner = {}
        for w in filtered_wkls:
            by_owner.setdefault(w["owner_email"], []).append(w)

        for owner_email in target_owners:
            ow_list = by_owner.get(owner_email, [])
            if not ow_list:
                continue
            owner_email_data = build_owner_email(owner_email, ow_list, simulation_recipients=recipients)
            preview_owner_file = f"/tmp/email_preview_{owner_email.split('@')[0]}.html"
            with open(preview_owner_file, "w", encoding="utf-8") as f:
                f.write(owner_email_data["html_body"])
            print(f"✓ Per-owner HTML preview for {owner_email}: {preview_owner_file}")
            print(f"  Subject: {owner_email_data['subject']}")

            if args.send:
                print(f"  -> Sending per-owner email for {owner_email} to {recipients[0]}" + (f" (cc: {recipients[1]})" if len(recipients) > 1 else "") + "...")
                try:
                    res = send_email_via_cli(recipients, owner_email_data["subject"], owner_email_data["html_body"])
                    print(f"     ✓ Sent! Result: {res}")
                except Exception as e:
                    print(f"     ✗ Failed: {e}")

    if not args.send:
        print("\n(Dry-run mode: Pass --send to execute sending via Gmail CLI)")


if __name__ == "__main__":
    main()
