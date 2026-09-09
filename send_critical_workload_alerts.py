#!/usr/bin/env python3
"""
send_critical_workload_alerts.py

Scans partner action trackers for workloads in Critical status (Stages 0-2 or 3, Production Date <= 14 days or overdue).
Generates customized alert notifications:
- Stage 0-2: Check if workload will be in production on target date, ask to update production date ASAP.
- Stage 3: Confirm no technical issues and no partner dependencies.
Can send emails via Gmail CLI and Google Chat DMs via gchat CLI.
Supports simulation mode where all emails/messages are routed to a specified recipient (e.g. oliverhartley@google.com).
"""

import os
import sys
import re
import csv
import json
import argparse
import datetime
import subprocess

GMAIL = "/google/bin/releases/gemini-agents-gmail/gmail"
GCHAT = "/google/bin/releases/gemini-agents-gchat/gchat"

DEFAULT_PARTNER_CSV = "followup_data_latest/MadeinWeb_S_A_followup.csv"
PARTNER_NAME_DEFAULT = "MadeinWeb S/A"
TRACKER_URL_DEFAULT = "https://docs.google.com/spreadsheets/d/1PabQ-umTOYTkMg6n4__kP1VeFRc6SMxz_A0Yft3vrtw/edit"


def extract_hyperlink(cell_str):
    m = re.match(r'=HYPERLINK\("([^"]+)",\s*"([^"]+)"\)', cell_str)
    if m:
        return m.group(2).strip(), m.group(1).strip()
    return cell_str.strip(), ""


def find_critical_workloads(csv_path, partner_name=PARTNER_NAME_DEFAULT, tracker_url=TRACKER_URL_DEFAULT):
    today = datetime.date.today()
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 6:
        return []

    critical_workloads = []
    # Header is at row index 4 (1-indexed row 5), data starts at row index 5 (1-indexed row 6)
    for row_idx, r in enumerate(rows[5:], start=6):
        if len(r) < 17:
            continue

        cust_cell = r[0]
        tier = r[1]
        wkl_cell = r[2]
        owner_name = r[3].strip()
        arr_val = r[4].strip()
        progress = r[5].strip()
        cap_status = r[6].strip()
        opp_cell = r[7]
        next_steps = r[8].strip() if len(r) > 8 else ""
        er_cell = r[9].strip() if len(r) > 9 else ""
        prod_date_str = r[15].strip() if len(r) > 15 else ""
        owner_email = r[16].strip() if len(r) > 16 else ""

        is_active_stage = progress.startswith("0-2") or progress.startswith("3:")
        if not is_active_stage or not prod_date_str:
            continue

        try:
            prod_date = datetime.datetime.strptime(prod_date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue

        days_diff = (prod_date - today).days
        if days_diff <= 14:
            if days_diff < 0:
                days_status = f"🔴 OVERDUE by {abs(days_diff)} days"
            elif days_diff == 0:
                days_status = "🔴 DUE TODAY"
            else:
                days_status = f"🔴 {days_diff} days remaining"

            cust_name, cust_url = extract_hyperlink(cust_cell)
            wkl_name, wkl_url = extract_hyperlink(wkl_cell)
            opp_name, opp_url = extract_hyperlink(opp_cell)
            er_name, er_url = extract_hyperlink(er_cell)

            stage_type = "stage_0_2" if progress.startswith("0-2") else "stage_3"

            critical_workloads.append({
                "row_number": row_idx,
                "partner_name": partner_name,
                "tracker_url": tracker_url,
                "customer_name": cust_name,
                "customer_url": cust_url,
                "tier": tier,
                "workload_name": wkl_name,
                "workload_url": wkl_url,
                "owner_name": owner_name,
                "owner_email": owner_email,
                "arr": arr_val,
                "progress": progress,
                "stage_type": stage_type,
                "capacity_status": cap_status,
                "next_steps": next_steps,
                "production_date": str(prod_date),
                "days_diff": days_diff,
                "days_status": days_status
            })

    return critical_workloads


def build_email_content(wkl, simulation_recipient=None):
    is_simulation = bool(simulation_recipient)
    actual_owner = f"{wkl['owner_name']} <{wkl['owner_email']}>"

    subject_prefix = "[SIMULATION] " if is_simulation else ""
    subject = f"{subject_prefix}[Action Required 🔴] Critical Workload Alert: {wkl['workload_name']} ({wkl['customer_name']}) - ARR {wkl['arr']}"

    if wkl["stage_type"] == "stage_0_2":
        stage_banner_color = "#e8f0fe"
        stage_border_color = "#1a73e8"
        stage_text_color = "#174ea6"
        stage_title = "Action Required (Stage 0-2: Tech Eval / Solution Dev)"
        stage_action_html = f"""
        <p style="margin: 6px 0 0 0;">
          This workload is scheduled to go live on <strong>{wkl['production_date']}</strong> (<strong>{wkl['days_status']}</strong>).<br>
          👉 <strong>Please check and confirm if this workload will realistically be in production by {wkl['production_date']}.</strong><br>
          If there is any shift or delay, <strong>please update the Production Date in Salesforce / Concord as soon as possible.</strong>
        </p>
        """
        chat_action_text = f"👉 *Action Required*: Please check if this workload will realistically be in production on *{wkl['production_date']}*. If delayed, please update the Production Date in Salesforce as soon as possible."
    else:
        stage_banner_color = "#fef7e0"
        stage_border_color = "#f9ab00"
        stage_text_color = "#b06000"
        stage_title = "Action Required (Stage 3: Proposal / Negotiation)"
        stage_action_html = f"""
        <p style="margin: 6px 0 0 0;">
          With production scheduled for <strong>{wkl['production_date']}</strong> (<strong>{wkl['days_status']}</strong>):<br>
          👉 <strong>Please confirm that there is no technical issue and no blocking dependencies with the partner ({wkl['partner_name']}).</strong>
        </p>
        """
        chat_action_text = f"👉 *Action Required*: Please confirm that there are no unresolved technical issues and no blocking dependencies with partner *{wkl['partner_name']}*."

    simulation_header_html = ""
    if is_simulation:
        simulation_header_html = f"""
        <div style="background-color: #fce8e6; border: 1px dashed #d93025; padding: 10px 14px; border-radius: 4px; margin-bottom: 16px; font-size: 13px;">
          <strong>⚠️ SIMULATION ALERT</strong> — In production, this notification would be sent directly to:<br>
          <strong>{wkl['owner_name']}</strong> (<a href="mailto:{wkl['owner_email']}">{wkl['owner_email']}</a>).
        </div>
        """

    html_body = f"""
    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #202124; line-height: 1.5; max-width: 650px; border: 1px solid #dadce0; border-radius: 8px; padding: 20px;">
      {simulation_header_html}
      <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
        <span style="color: #c5221f; font-size: 16px; font-weight: bold;">🔴 Critical Workload Alert — Target Go-Live Risk</span><br>
        <span style="font-size: 13px; color: #5f6368;">Production Date is within 14 days or overdue while still in Stage 0-2 / 3.</span>
      </div>

      <p>Hi <strong>{wkl['owner_name']}</strong>,</p>

      <p>The workload <strong>{wkl['workload_name']}</strong> with <strong>{wkl['arr']}</strong> ARR in your portfolio is in <strong>Critical Condition</strong>:</p>

      <table style="border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; border: 1px solid #dadce0;">
        <tbody>
          <tr style="background-color: #f8f9fa;">
            <td style="padding: 8px 12px; font-weight: bold; width: 35%; border: 1px solid #dadce0;">Workload Name</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0;">
              <a href="{wkl['workload_url']}" style="color: #1a73e8; text-decoration: none; font-weight: bold;">{wkl['workload_name']} ↗</a>
            </td>
          </tr>
          <tr>
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Customer Account</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0;">
              <a href="{wkl['customer_url']}" style="color: #1a73e8; text-decoration: none;">{wkl['customer_name']} ↗</a> ({wkl['tier']})
            </td>
          </tr>
          <tr style="background-color: #f8f9fa;">
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Partner Organization</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0;"><strong>{wkl['partner_name']}</strong></td>
          </tr>
          <tr>
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Annual Gross Revenue (ARR)</td>
            <td style="padding: 8px 12px; font-weight: bold; color: #137333; border: 1px solid #dadce0;">{wkl['arr']}</td>
          </tr>
          <tr style="background-color: #f8f9fa;">
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Current Stage / Progress</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0;"><strong>{wkl['progress']}</strong></td>
          </tr>
          <tr>
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Target Production Date</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0; color: #c5221f; font-weight: bold;">
              {wkl['production_date']} ({wkl['days_status']})
            </td>
          </tr>
          <tr style="background-color: #f8f9fa;">
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Delivery Capacity Status</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0;">{wkl['capacity_status']}</td>
          </tr>
          <tr>
            <td style="padding: 8px 12px; font-weight: bold; border: 1px solid #dadce0;">Next Steps Registered</td>
            <td style="padding: 8px 12px; border: 1px solid #dadce0; font-style: italic;">{wkl['next_steps'] if wkl['next_steps'] else 'No next steps recorded'}</td>
          </tr>
        </tbody>
      </table>

      <div style="background-color: {stage_banner_color}; border-left: 4px solid {stage_border_color}; padding: 12px 16px; border-radius: 4px; margin: 16px 0;">
        <strong style="color: {stage_text_color}; font-size: 14px;">{stage_title}</strong>
        {stage_action_html}
      </div>

      <p style="font-size: 12px; color: #5f6368; margin-top: 24px; border-top: 1px solid #dadce0; padding-top: 12px;">
        Notification generated by Partner Action Trackers &bull; Partner: <strong>{wkl['partner_name']}</strong> &bull; <a href="{wkl['tracker_url']}" style="color: #1a73e8;">Open Partner Action Tracker Sheet ↗</a>
      </p>
    </div>
    """

    chat_text = f"""🔴 *CRITICAL WORKLOAD ALERT* [Stage {'0-2' if wkl['stage_type'] == 'stage_0_2' else '3'}]
*Workload*: {wkl['workload_name']}
*Customer*: {wkl['customer_name']} ({wkl['tier']})
*Partner*: {wkl['partner_name']}
*ARR*: {wkl['arr']} | *Progress*: {wkl['progress']}
*Target Production Date*: {wkl['production_date']} ({wkl['days_status']})
*Link*: {wkl['workload_url']}

{chat_action_text}"""

    return {
        "subject": subject,
        "html_body": html_body,
        "chat_text": chat_text,
        "recipient": simulation_recipient if is_simulation else wkl["owner_email"],
        "actual_owner": actual_owner
    }


def send_email(recipient, subject, html_body):
    cmd = [
        GMAIL, "mutate", "send",
        "--to", recipient,
        "--subject", subject,
        "--html",
        "--body", html_body
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to send email via Gmail CLI: {res.stderr or res.stdout}")
    return res.stdout.strip()


def send_chat_dm(username, text):
    cmd = [
        GCHAT, "mutate", "send-direct-message",
        "--usernames", username,
        "--text", text
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to send Google Chat DM via gchat CLI: {res.stderr or res.stdout}")
    return res.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Send critical workload alerts to owners or simulation recipient.")
    parser.add_argument("--csv", default=DEFAULT_PARTNER_CSV, help="Path to partner followup CSV")
    parser.add_argument("--partner", default=PARTNER_NAME_DEFAULT, help="Partner organization name")
    parser.add_argument("--tracker-url", default=TRACKER_URL_DEFAULT, help="Partner tracker spreadsheet URL")
    parser.add_argument("--recipient", default="oliverhartley@google.com", help="Email recipient (defaults to Oliver Hartley for simulation)")
    parser.add_argument("--send", action="store_true", help="Actually execute sending via Gmail CLI")
    parser.add_argument("--chat", action="store_true", help="Also send Google Chat DMs for Stage 0-2 workloads")
    parser.add_argument("--chat-user", default="oliverhartley", help="LDAP user to receive chat messages in simulation")

    args = parser.parse_args()

    print(f"Scanning {args.csv} for critical workloads...")
    critical_wkls = find_critical_workloads(args.csv, partner_name=args.partner, tracker_url=args.tracker_url)
    print(f"Found {len(critical_wkls)} workloads in Critical condition (Stage 0-2 or 3 with <= 14 days to go-live).\n")

    if not critical_wkls:
        print("No critical workloads found.")
        return

    for idx, wkl in enumerate(critical_wkls, 1):
        content = build_email_content(wkl, simulation_recipient=args.recipient)
        print(f"[{idx}/{len(critical_wkls)}] {wkl['workload_name']} ({wkl['customer_name']})")
        print(f"  Owner: {wkl['owner_name']} ({wkl['owner_email']})")
        print(f"  ARR: {wkl['arr']} | Stage: {wkl['progress']} ({wkl['stage_type']})")
        print(f"  Prod Date: {wkl['production_date']} ({wkl['days_status']})")
        print(f"  Target Recipient: {content['recipient']}")
        print(f"  Subject: {content['subject']}")

        if args.send:
            print(f"  -> Sending email to {content['recipient']}...")
            try:
                res_mail = send_email(content["recipient"], content["subject"], content["html_body"])
                print(f"     ✓ Email sent! Result: {res_mail}")
            except Exception as e:
                print(f"     ✗ Email failed: {e}")

            if args.chat and wkl["stage_type"] == "stage_0_2":
                print(f"  -> Sending Google Chat DM to {args.chat_user}...")
                try:
                    res_chat = send_chat_dm(args.chat_user, content["chat_text"])
                    print(f"     ✓ Chat DM sent! Result: {res_chat}")
                except Exception as e:
                    print(f"     ✗ Chat DM failed: {e}")
        else:
            print("  (Dry-run mode: Pass --send to execute sending)")
        print()


if __name__ == "__main__":
    main()
