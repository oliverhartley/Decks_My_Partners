#!/usr/bin/env python3
"""
send_workload_digest_alerts.py

Scans the Partner Management Dashboard (Oliver Hartley) for workloads in Critical and High risk,
as well as any Priority workloads. Consolidates workloads by Workload Owner so each owner receives
only ONE aggregated digest email.

Target criteria:
- Stage 0-2 and Stage 3 workloads with Target Date <= 30 days (Critical: <=14d / Overdue, High: 15-30d)
- OR any workload marked with Business Priority == "Priority"
- Emphasizes Stage 0-2 workloads with stage specification, risk level badge, and Next Steps History.

Test mode:
- Aggregates qualifying workloads from:
  patricioperez@google.com
  renanvaladares@google.com
  vpimentel@google.com
- Sends test digest to oliver.hartley@gmail.com and oliver@obiracing.com.
"""

import os
import sys
import re
import csv
import json
import argparse
import datetime
import subprocess

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
GMAIL = "/google/bin/releases/gemini-agents-gmail/gmail"

OLIVER_SSID = "1VkmmtXJopJ57K_XL3jwdqk8LrN6qw0_iGrBbl5deYpI"
DEFAULT_TAB = "All_Workloads_Follow_up"

TEST_OWNERS = [
    "patricioperez@google.com",
    "renanvaladares@google.com",
    "vpimentel@google.com"
]

TEST_RECIPIENTS_TO = "oliver.hartley@gmail.com"
TEST_RECIPIENTS_CC = "oliver@obiracing.com"


def extract_hyperlink(cell_str):
    if not cell_str:
        return "", ""
    cell_str = str(cell_str).strip()
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', cell_str)
    if m:
        return m.group(2).strip(), m.group(1).strip()
    return cell_str, ""


def parse_arr(arr_str):
    if not arr_str:
        return 0.0
    clean = re.sub(r"[^0-9.]", "", str(arr_str))
    try:
        return float(clean)
    except ValueError:
        return 0.0


def fetch_workloads_from_dashboard(ssid=OLIVER_SSID, tab=DEFAULT_TAB):
    cmd = [GSHEETS, "readonly", "read", ssid, f"'{tab}'!A5:V5000", "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Error reading dashboard {ssid}: {res.stderr}")
    data = json.loads(res.stdout)
    if not data or len(data) < 2:
        return [], []
    headers = [str(h).strip() for h in data[0]]
    rows = data[1:]
    return headers, rows


def evaluate_workloads(headers, rows, today=None):
    if today is None:
        today = datetime.date.today()

    col_map = {h: idx for idx, h in enumerate(headers)}
    pe_idx = col_map.get("Partner Engineer (PE)", 0)
    partner_idx = col_map.get("Partner Name", 1)
    account_idx = col_map.get("Customer Account Name", 2)
    tier_idx = col_map.get("Account Tier", 3)
    wkl_idx = col_map.get("Workload Name", 4)
    owner_name_idx = col_map.get("Workload Owner", 5)
    arr_idx = col_map.get("Annual Gross Revenue (ARR USD)", 6)
    progress_idx = col_map.get("Workload Progress", 7)
    cap_idx = col_map.get("Capacity Status (DRP Readiness)", 8)
    opp_idx = col_map.get("Opportunity Name", 9)
    next_steps_idx = col_map.get("Next Steps", 10)
    er_idx = col_map.get("Expert Requests", 11)
    sub_region_idx = col_map.get("Customer Sub Region", 12)
    micro_region_idx = col_map.get("Customer Micro Region", 13)
    pillar_idx = col_map.get("Primary Workload Pillar", 14)
    sales_play_idx = col_map.get("Sales Play", 15)
    sol_idx = col_map.get("Workload Solution", 16)
    prod_date_idx = col_map.get("Production Date", 17)
    owner_email_idx = col_map.get("Workload Owner Email", 18)
    notes_idx = col_map.get("Notes / Tasks", 19)
    last_update_idx = col_map.get("Last Update", 20)
    biz_pri_idx = col_map.get("Business Priority", 21)

    evaluated = []

    for r_idx, r in enumerate(rows, start=6):
        if len(r) <= max(wkl_idx, progress_idx):
            continue

        wkl_raw = r[wkl_idx] if len(r) > wkl_idx else ""
        if not wkl_raw:
            continue

        wkl_name, wkl_url = extract_hyperlink(wkl_raw)
        partner_name, partner_url = extract_hyperlink(r[partner_idx] if len(r) > partner_idx else "")
        account_name, account_url = extract_hyperlink(r[account_idx] if len(r) > account_idx else "")
        opp_name, opp_url = extract_hyperlink(r[opp_idx] if len(r) > opp_idx else "")
        er_raw = r[er_idx] if len(r) > er_idx else ""

        progress = str(r[progress_idx]).strip() if len(r) > progress_idx else ""
        owner_name = str(r[owner_name_idx]).strip() if len(r) > owner_name_idx else ""
        owner_email = str(r[owner_email_idx]).strip().lower() if len(r) > owner_email_idx else ""
        if owner_email and "@" not in owner_email:
            owner_email = f"{owner_email}@google.com"

        arr_str = str(r[arr_idx]).strip() if len(r) > arr_idx else "$0.00"
        arr_val = parse_arr(arr_str)

        prod_date_str = str(r[prod_date_idx]).strip() if len(r) > prod_date_idx else ""
        next_steps = str(r[next_steps_idx]).strip() if len(r) > next_steps_idx else ""
        notes_tasks = str(r[notes_idx]).strip() if len(r) > notes_idx else ""
        last_update = str(r[last_update_idx]).strip() if len(r) > last_update_idx else ""
        biz_priority = str(r[biz_pri_idx]).strip() if len(r) > biz_pri_idx else ""
        is_priority = (biz_priority.lower() == "priority")

        # Parse target date and risk
        target_date = None
        days_diff = None
        risk_level = "NORMAL"
        days_status = "No Target Date"

        if prod_date_str:
            try:
                target_date = datetime.datetime.strptime(prod_date_str[:10], "%Y-%m-%d").date()
                days_diff = (target_date - today).days
                if days_diff < 0:
                    days_status = f"Overdue by {abs(days_diff)}d"
                    risk_level = "CRITICAL"
                elif days_diff <= 14:
                    days_status = f"{days_diff}d remaining"
                    risk_level = "CRITICAL"
                elif 15 <= days_diff <= 30:
                    days_status = f"{days_diff}d remaining"
                    risk_level = "HIGH"
                elif 31 <= days_diff <= 45:
                    days_status = f"{days_diff}d remaining"
                    risk_level = "MEDIUM"
                else:
                    days_status = f"{days_diff}d remaining"
                    risk_level = "NORMAL"
            except ValueError:
                days_status = f"Invalid date: {prod_date_str}"

        is_stage_0_2 = progress.startswith("0-2")
        is_stage_3 = progress.startswith("3:")

        stage_category = "other"
        if is_stage_0_2:
            stage_category = "stage_0_2"
        elif is_stage_3:
            stage_category = "stage_3"

        # Qualification rule:
        # 1) (Stage 0-2 or Stage 3) AND (risk_level in [CRITICAL, HIGH])
        # OR
        # 2) is_priority (any Priority workload)
        qualifies_stage_risk = (is_stage_0_2 or is_stage_3) and (risk_level in ["CRITICAL", "HIGH"])
        qualifies = qualifies_stage_risk or is_priority

        item = {
            "row_number": r_idx,
            "workload_name": wkl_name,
            "workload_url": wkl_url,
            "partner_name": partner_name,
            "partner_url": partner_url,
            "account_name": account_name,
            "account_url": account_url,
            "tier": str(r[tier_idx]).strip() if len(r) > tier_idx else "",
            "opportunity_name": opp_name,
            "opportunity_url": opp_url,
            "owner_name": owner_name,
            "owner_email": owner_email,
            "arr_str": arr_str,
            "arr_val": arr_val,
            "progress": progress,
            "stage_category": stage_category,
            "is_stage_0_2": is_stage_0_2,
            "is_stage_3": is_stage_3,
            "is_priority": is_priority,
            "target_date_str": str(target_date) if target_date else prod_date_str,
            "days_diff": days_diff,
            "days_status": days_status,
            "risk_level": risk_level,
            "next_steps": next_steps,
            "notes_tasks": notes_tasks,
            "last_update": last_update,
            "qualifies": qualifies,
            "qualifies_stage_risk": qualifies_stage_risk
        }
        evaluated.append(item)

    return evaluated


def build_workload_card_html(w):
    is_s02 = w["is_stage_0_2"]
    is_s3 = w["is_stage_3"]

    # Stage Badge
    if is_s02:
        stage_badge = """<span style="background-color: #E8F0FE; color: #1967D2; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #C2E7FF;">Stage 0-2: Technical Evaluation / Solution Development</span>"""
    elif is_s3:
        stage_badge = """<span style="background-color: #FEF7E0; color: #B06000; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #FEEFC3;">Stage 3: Proposal / Negotiation</span>"""
    else:
        stage_badge = f"""<span style="background-color: #F1F3F4; color: #3C4043; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{w['progress']}</span>"""

    # Risk Badge
    if w["risk_level"] == "CRITICAL":
        risk_badge = f"""<span style="background-color: #FCE8E6; color: #C5221F; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #FAD2CF;">🔴 CRITICAL ({w['days_status']})</span>"""
    elif w["risk_level"] == "HIGH":
        risk_badge = f"""<span style="background-color: #FFEFE6; color: #D9381E; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #FFD8C7;">🌸 HIGH ({w['days_status']})</span>"""
    elif w["risk_level"] == "MEDIUM":
        risk_badge = f"""<span style="background-color: #FEF7E0; color: #7C4A00; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #FEEFC3;">🟡 MEDIUM ({w['days_status']})</span>"""
    else:
        risk_badge = f"""<span style="background-color: #F1F3F4; color: #5F6368; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">⚪ NORMAL ({w['days_status']})</span>"""

    priority_badge = ""
    if w["is_priority"]:
        priority_badge = """<span style="background-color: #F3E8FD; color: #7627BB; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; border: 1px solid #D7AEFB; margin-left: 6px;">⭐ PRIORITY</span>"""

    # Action callout
    if is_s02:
        action_box = f"""
        <div style="background-color: #F8F9FA; border-left: 4px solid #1A73E8; padding: 10px 14px; margin-top: 10px; border-radius: 0 4px 4px 0;">
          <div style="font-weight: bold; font-size: 12px; color: #1A73E8; margin-bottom: 4px;">🎯 STAGE 0-2 ACTION REQUIRED:</div>
          <div style="font-size: 12px; color: #3C4043; line-height: 1.4;">
            This workload is scheduled to go live on <strong>{w['target_date_str']}</strong> (<strong>{w['days_status']}</strong>).<br>
            👉 <strong>Please check and confirm if this workload will realistically be in production by {w['target_date_str']}.</strong><br>
            If delayed or shifting, please update the <strong>Target Production Date</strong> in Salesforce / Concord ASAP.
          </div>
        </div>
        """
    elif is_s3:
        action_box = f"""
        <div style="background-color: #F8F9FA; border-left: 4px solid #FBBC04; padding: 10px 14px; margin-top: 10px; border-radius: 0 4px 4px 0;">
          <div style="font-weight: bold; font-size: 12px; color: #B06000; margin-bottom: 4px;">🤝 STAGE 3 ACTION REQUIRED:</div>
          <div style="font-size: 12px; color: #3C4043; line-height: 1.4;">
            Target production date is <strong>{w['target_date_str']}</strong> (<strong>{w['days_status']}</strong>).<br>
            👉 <strong>Please confirm there are no unresolved technical blockers or partner dependencies with {w['partner_name']}.</strong>
          </div>
        </div>
        """
    else:
        action_box = f"""
        <div style="background-color: #F8F9FA; border-left: 4px solid #9AA0A6; padding: 8px 12px; margin-top: 10px; border-radius: 0 4px 4px 0;">
          <div style="font-size: 12px; color: #3C4043;">
            Target production date: <strong>{w['target_date_str']}</strong> ({w['days_status']}).
          </div>
        </div>
        """

    # Next Steps History Highlight
    ns_text = w["next_steps"].strip() if w["next_steps"] else "<em>No next steps history logged yet in Salesforce.</em>"
    ns_box = f"""
    <div style="margin-top: 10px; padding: 10px 12px; background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px;">
      <div style="font-size: 11px; font-weight: bold; color: #5F6368; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
        📝 Latest Next Steps History:
      </div>
      <div style="font-size: 12px; color: #202124; line-height: 1.45; font-style: italic;">
        "{ns_text}"
      </div>
    </div>
    """

    wkl_link = f"""<a href="{w['workload_url']}" style="color: #1A73E8; text-decoration: underline; font-weight: bold;">{w['workload_name']}</a>""" if w['workload_url'] else f"""<strong>{w['workload_name']}</strong>"""
    acc_link = f"""<a href="{w['account_url']}" style="color: #1A73E8; text-decoration: none;">{w['account_name']}</a>""" if w['account_url'] else w['account_name']
    opp_link = f"""<a href="{w['opportunity_url']}" style="color: #1A73E8; text-decoration: none;">{w['opportunity_name']}</a>""" if w['opportunity_url'] else w['opportunity_name']
    partner_link = f"""<a href="{w['partner_url']}" style="color: #1A73E8; text-decoration: none;">{w['partner_name']}</a>""" if w['partner_url'] else w['partner_name']

    card_border = "#FAD2CF" if w["risk_level"] == "CRITICAL" else ("#FFD8C7" if w["risk_level"] == "HIGH" else "#DADCE0")

    html = f"""
    <div style="border: 1px solid {card_border}; border-radius: 6px; padding: 14px 16px; margin-bottom: 14px; background-color: #FFFFFF; box-shadow: 0 1px 2px rgba(60,64,67,0.08);">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
        <div style="font-size: 15px; line-height: 1.3;">
          {wkl_link}
        </div>
      </div>
      <div style="margin-bottom: 10px;">
        {stage_badge}
        {risk_badge}
        {priority_badge}
      </div>
      <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 6px;">
        <tr>
          <td style="padding: 3px 0; color: #5F6368; width: 140px;">Customer Account:</td>
          <td style="padding: 3px 0; color: #202124; font-weight: 500;">{acc_link}</td>
          <td style="padding: 3px 0; color: #5F6368; width: 130px;">Partner:</td>
          <td style="padding: 3px 0; color: #202124; font-weight: 500;">{partner_link}</td>
        </tr>
        <tr>
          <td style="padding: 3px 0; color: #5F6368;">Annual Revenue (ARR):</td>
          <td style="padding: 3px 0; color: #188038; font-weight: bold; font-size: 13px;">{w['arr_str']}</td>
          <td style="padding: 3px 0; color: #5F6368;">Target Date:</td>
          <td style="padding: 3px 0; color: #202124; font-weight: 600;">{w['target_date_str']} ({w['days_status']})</td>
        </tr>
        <tr>
          <td style="padding: 3px 0; color: #5F6368;">Opportunity:</td>
          <td style="padding: 3px 0; color: #202124;" colspan="3">{opp_link}</td>
        </tr>
      </table>
      {ns_box}
      {action_box}
    </div>
    """
    return html


def build_digest_html(owner_workloads_map, is_test=False):
    today_str = datetime.date.today().strftime("%B %d, %Y")
    total_wkls = sum(len(wkls) for wkls in owner_workloads_map.values())
    total_arr = sum(sum(w["arr_val"] for w in wkls) for wkls in owner_workloads_map.values())
    total_critical = sum(sum(1 for w in wkls if w["risk_level"] == "CRITICAL") for wkls in owner_workloads_map.values())
    total_high = sum(sum(1 for w in wkls if w["risk_level"] == "HIGH") for wkls in owner_workloads_map.values())
    total_priority = sum(sum(1 for w in wkls if w["is_priority"]) for wkls in owner_workloads_map.values())

    test_banner = ""
    if is_test:
        test_banner = f"""
        <div style="background-color: #E8F0FE; border: 1px solid #1A73E8; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px;">
          <div style="font-weight: bold; color: #1967D2; font-size: 14px; margin-bottom: 4px;">🧪 AUTOMATION TEST DISPATCH</div>
          <div style="font-size: 12px; color: #3C4043; line-height: 1.4;">
            This test digest aggregates workloads from <strong>Patricio Perez</strong>, <strong>Renan Valadares</strong>, and <strong>Victor Pimentel</strong>.<br>
            In production, each owner will receive their personalized digest containing only their assigned workloads.<br>
            Source Dashboard: <a href="https://docs.google.com/spreadsheets/d/{OLIVER_SSID}/edit#gid=0" style="color: #1A73E8; font-weight: bold;">Partner Management Dashboard - Oliver Hartley</a>.
          </div>
        </div>
        """

    sections_html = ""
    for owner_email, wkls in owner_workloads_map.items():
        owner_name = wkls[0]["owner_name"] or owner_email
        owner_arr = sum(w["arr_val"] for w in wkls)
        owner_crit = sum(1 for w in wkls if w["risk_level"] == "CRITICAL")
        owner_high = sum(1 for w in wkls if w["risk_level"] == "HIGH")
        owner_prio = sum(1 for w in wkls if w["is_priority"])

        cards_html = "".join([build_workload_card_html(w) for w in wkls])

        section = f"""
        <div style="margin-bottom: 30px; border: 1px solid #E0E0E0; border-radius: 8px; padding: 18px 20px; background-color: #FAFAFA;">
          <div style="border-bottom: 2px solid #1A73E8; padding-bottom: 10px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: baseline;">
            <div>
              <span style="font-size: 17px; font-weight: bold; color: #202124;">👤 {owner_name}</span>
              <span style="font-size: 13px; color: #5F6368; margin-left: 8px;">({owner_email})</span>
            </div>
            <div style="font-size: 13px; font-weight: bold; color: #188038;">
              ${owner_arr:,.2f} ARR &nbsp;|&nbsp; {len(wkls)} Workloads
            </div>
          </div>
          <div style="font-size: 12px; color: #5F6368; margin-bottom: 14px;">
            Summary: <strong>{owner_crit}</strong> Critical (≤14d), <strong>{owner_high}</strong> High (15-30d), <strong>{owner_prio}</strong> Priority
          </div>
          {cards_html}
        </div>
        """
        sections_html += section

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Critical & High Workload Action Digest</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F8F9FA; margin: 0; padding: 24px; color: #202124;">
      <div style="max-width: 820px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; border: 1px solid #DADCE0; padding: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
        
        {test_banner}

        <!-- Header -->
        <div style="border-bottom: 1px solid #E8EAED; padding-bottom: 16px; margin-bottom: 20px;">
          <div style="font-size: 22px; font-weight: bold; color: #1A73E8; margin-bottom: 4px;">
            ⚡ Partner Workload Action & Risk Digest
          </div>
          <div style="font-size: 13px; color: #5F6368;">
            Pipeline Health & Target Go-Live Risk Follow-up &nbsp;•&nbsp; <strong>{today_str}</strong>
          </div>
        </div>

        <!-- KPI Metrics Grid -->
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          <tr>
            <td style="width: 20%; padding: 12px; background-color: #F8F9FA; border-radius: 6px; text-align: center; border: 1px solid #E8EAED;">
              <div style="font-size: 11px; color: #5F6368; font-weight: bold; text-transform: uppercase;">Total Monitored</div>
              <div style="font-size: 20px; font-weight: bold; color: #202124; margin-top: 4px;">{total_wkls}</div>
            </td>
            <td style="width: 2%;"></td>
            <td style="width: 26%; padding: 12px; background-color: #F8F9FA; border-radius: 6px; text-align: center; border: 1px solid #E8EAED;">
              <div style="font-size: 11px; color: #5F6368; font-weight: bold; text-transform: uppercase;">Total ARR</div>
              <div style="font-size: 20px; font-weight: bold; color: #188038; margin-top: 4px;">${total_arr:,.2f}</div>
            </td>
            <td style="width: 2%;"></td>
            <td style="width: 24%; padding: 12px; background-color: #FCE8E6; border-radius: 6px; text-align: center; border: 1px solid #FAD2CF;">
              <div style="font-size: 11px; color: #C5221F; font-weight: bold; text-transform: uppercase;">🔴 Critical (≤14d)</div>
              <div style="font-size: 20px; font-weight: bold; color: #C5221F; margin-top: 4px;">{total_critical}</div>
            </td>
            <td style="width: 2%;"></td>
            <td style="width: 24%; padding: 12px; background-color: #FFEFE6; border-radius: 6px; text-align: center; border: 1px solid #FFD8C7;">
              <div style="font-size: 11px; color: #D9381E; font-weight: bold; text-transform: uppercase;">🌸 High (15-30d)</div>
              <div style="font-size: 20px; font-weight: bold; color: #D9381E; margin-top: 4px;">{total_high}</div>
            </td>
          </tr>
        </table>

        <!-- Alert Criteria Guide -->
        <div style="background-color: #F8F9FA; border: 1px solid #E8EAED; border-radius: 6px; padding: 12px 16px; margin-bottom: 24px; font-size: 12px; color: #5F6368; line-height: 1.5;">
          <strong>📋 Evaluation Criteria:</strong><br>
          • <strong>Stage 0-2 (Tech Eval / Solution Dev)</strong>: Critical (≤14d / Overdue) or High (15-30d) vs Target Date.<br>
          • <strong>Stage 3 (Proposal / Negotiation)</strong>: Critical (≤14d / Overdue) or High (15-30d) vs Target Date.<br>
          • <strong>Priority Workloads (⭐)</strong>: Included regardless of days remaining to ensure active executive tracking.
        </div>

        <!-- Owner Workload Sections -->
        {sections_html}

        <!-- Footer -->
        <div style="border-top: 1px solid #E8EAED; padding-top: 16px; margin-top: 24px; font-size: 11px; color: #70757A; line-height: 1.5; text-align: center;">
          Partner Management Follow-up Automation &nbsp;•&nbsp;
          <a href="https://docs.google.com/spreadsheets/d/{OLIVER_SSID}/edit#gid=0" style="color: #1A73E8; text-decoration: none;">Open Partner Management Dashboard (Oliver Hartley) ↗</a><br>
          Generated automatically from Salesforce & Concord data.
        </div>
      </div>
    </body>
    </html>
    """
    return full_html


def main():
    parser = argparse.ArgumentParser(description="Send Workload Digest Action Alerts")
    parser.add_argument("--dashboard-id", default=OLIVER_SSID, help="Spreadsheet ID of the dashboard")
    parser.add_argument("--tab", default=DEFAULT_TAB, help="Tab name in dashboard")
    parser.add_argument("--test", action="store_true", default=True, help="Run test mode for Patricio, Renan, and Victor")
    parser.add_argument("--send", action="store_true", help="Send actual emails via Gmail CLI (dry-run if not specified)")
    parser.add_argument("--to", default=TEST_RECIPIENTS_TO, help="Recipient email address")
    parser.add_argument("--cc", default=TEST_RECIPIENTS_CC, help="CC email address")
    parser.add_argument("--output-html", default="workload_digest_preview.html", help="Path to save HTML preview")
    args = parser.parse_args()

    print(f"\n>>> Fetching workloads from dashboard {args.dashboard_id} ({args.tab})...")
    headers, rows = fetch_workloads_from_dashboard(args.dashboard_id, args.tab)
    print(f"Loaded {len(rows)} total workloads from dashboard.")

    today = datetime.date.today()
    evaluated = evaluate_workloads(headers, rows, today=today)

    if args.test:
        target_owners_set = set(TEST_OWNERS)
        qualifying = [w for w in evaluated if w["qualifies"] and w["owner_email"] in target_owners_set]
    else:
        qualifying = [w for w in evaluated if w["qualifies"]]

    print(f"\nFound {len(qualifying)} qualifying workloads for evaluation.")

    # Group by owner
    owner_map = {}
    for w in qualifying:
        email = w["owner_email"]
        if email not in owner_map:
            owner_map[email] = []
        owner_map[email].append(w)

    print("\nBreakdown by Owner:")
    for email, wkls in owner_map.items():
        arr_sum = sum(w["arr_val"] for w in wkls)
        print(f"  - {email}: {len(wkls)} workloads (${arr_sum:,.2f} ARR)")
        for w in wkls:
            prio_tag = " [PRIORITY]" if w["is_priority"] else ""
            print(f"      • {w['workload_name']} | {w['progress']} | {w['risk_level']} ({w['days_status']}){prio_tag} | ARR {w['arr_str']}")

    html_content = build_digest_html(owner_map, is_test=args.test)
    with open(args.output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n✓ Generated HTML digest report: {args.output_html}")

    if args.send:
        print(f"\n>>> Sending test email via Gmail CLI...")
        print(f"  To: {args.to}")
        print(f"  CC: {args.cc}")
        subject = f"[TEST DIGEST] Partner Management Action Alerts: Critical & High Priority Workloads ({today.strftime('%b %d')})"
        cmd = [
            GMAIL, "--target_user", "oliverhartley",
            "--ignore-sharing-checks",
            "mutate", "send",
            "--to", args.to,
            "--cc", args.cc,
            "--subject", subject,
            "--html",
            "--body-file", args.output_html
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("✓ Email dispatched successfully via Gmail CLI!")
            print(res.stdout)
        else:
            print(f"❌ Error sending email: {res.stderr}")
            sys.exit(1)
    else:
        print("\n[Dry-run mode] Email was NOT sent. Pass --send to dispatch.")


if __name__ == "__main__":
    main()
