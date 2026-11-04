#!/usr/bin/env python3
"""
sync_fsr_sheets_daily.py
End-to-end daily synchronization orchestrator for the consolidated
"FSR Management Dashboard - Oliver Hartley" (`1JbaDkmltkqu6aaAKRszEwVFRsJxUSCofCWUKtwcjAhs`)
and the Agentic Workload Command Center (Local & Google Apps Script Web App).

Pipeline steps:
1. Pre-Sync Reconciliation (`sync_engine.sync_bidirectional`):
   Reads live non-Vector manual annotations from `FSR Management Dashboard - Oliver Hartley`
   (`All_Workloads_Follow_up` tab: `Cual es el bloqueo?`, `Status Tecnico`,
   `Partner Technical Contact`, `Client Technical Contact`, `Technical win`,
   `Propousal sent to client`) keyed by immutable Salesforce `workload_id`
   (extracted from Column D `=HYPERLINK()` formulas) BEFORE refreshing BigQuery data,
   ensuring zero loss even if a workload is renamed or changes stage in Vector.
2. BigQuery Extraction (`extract_copilot_data.py`):
   Pulls fresh active workloads, Opportunity Partners, Workload Partners,
   Next Steps History, and Partner Technical Contact waterfalls from Concord BQ.
3. Rollup Dashboard Generation & Deployment (`build_oliver_fsr_rollup.py`):
   Merges fresh Vector data with preserved manual annotations, updates incremental
   AI Next Steps summaries (`data/next_steps_ai_summaries.json`), and updates
   `Executive_Summary`, `All_Workloads_Follow_up`, and `Unpartnered_Matchmaker`
   on `FSR Management Dashboard - Oliver Hartley`.
4. Timeline & Date Change Tracking (`date_changes_tab.py`):
   Updates the `Date_Changes` tab on `FSR Management Dashboard - Oliver Hartley`.
5. Post-Sync Enrichment & Drive Cache Sync:
   Re-enriches `data/enriched_portfolio.json` and pushes `data/enriched_portfolio_web.json`
   and `fsr_manual_entries.json` to Google Drive for the shared Apps Script Web App.
"""

import os
import sys
import time
import subprocess

BASE_DIR = "/usr/local/google/home/oliverhartley/jetski-workspace/fsr-wkld-decks"


def main():
    start_ts = time.time()
    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)

    print("=" * 70)
    print("🚀 STARTING DAILY OLIVER HARTLEY FSR MANAGEMENT DASHBOARD SYNC")
    print("=" * 70)

    # Step 1: Pre-sync live manual annotations from FSR Management Dashboard - Oliver Hartley
    print("\n[Step 1/5] Capturing live manual annotations from FSR Management Dashboard - Oliver Hartley...")
    from sync_engine import sync_bidirectional, sync_drive_json_caches
    from copilot_engine import enrich_portfolio_cache
    pre_res = sync_bidirectional()
    print(
        f"  ✓ Pre-sync complete: {pre_res.get('pulled_count', 0)} manual cells pulled from Dashboard, "
        f"{pre_res.get('pushed_count', 0)} pending web edits pushed."
    )

    # Step 2: Refresh BigQuery portfolio cache
    print("\n[Step 2/5] Extracting fresh Concord BigQuery data (extract_copilot_data.py)...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "extract_copilot_data.py")], check=True)

    # Step 3: Build and deploy Oliver Hartley FSR Rollup Dashboard
    print("\n[Step 3/5] Updating FSR Management Dashboard - Oliver Hartley (build_oliver_fsr_rollup.py)...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "build_oliver_fsr_rollup.py")], check=True)

    # Step 4: Update Date_Changes tab on Oliver Hartley FSR Rollup Dashboard
    print("\n[Step 4/5] Updating 'Date_Changes' tab on FSR Management Dashboard - Oliver Hartley (date_changes_tab.py)...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "date_changes_tab.py")], check=True)

    # Step 5: Re-enrich portfolio & sync Drive JSON caches
    print("\n[Step 5/5] Enriching Command Center portfolio and syncing Google Drive JSON caches...")
    enrich_portfolio_cache()
    sync_drive_json_caches()
    # Record fresh post-build baseline state from the updated Rollup Dashboard
    sync_bidirectional()

    elapsed = (time.time() - start_ts) / 60.0
    print("\n" + "=" * 70)
    print(f"✅ DAILY FSR MANAGEMENT DASHBOARD SYNC COMPLETED IN {elapsed:.1f} MINUTES!")
    print("=" * 70)


if __name__ == "__main__":
    main()
