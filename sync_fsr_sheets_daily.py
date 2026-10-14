#!/usr/bin/env python3
"""
sync_fsr_sheets_daily.py
End-to-end daily synchronization orchestrator for all 8 Brazil FSR Action Trackers
and the Agentic Workload Command Center (Local & Google Apps Script Web App).

Pipeline steps:
1. Pre-Sync Reconciliation (`sync_engine.sync_bidirectional`):
   Reads live non-Vector manual annotations across all 8 FSR Google Sheets
   (`Cual es el bloqueo?`, `Status Tecnico`, `Partner Technical Owner Email`,
   `Technical win`, `Propousal sent to client`) keyed by immutable Salesforce
   `workload_id` (extracted from Column C `=HYPERLINK()` formulas) BEFORE
   refreshing BigQuery data, ensuring zero loss even if a workload is renamed
   or changes stage in Vector.
2. BigQuery Extraction (`extract_copilot_data.py`):
   Pulls fresh active workloads, Opportunity Partners, Workload Partners,
   Next Steps History, and Partner Technical Owner Email waterfalls from Concord BQ.
3. Deck Generation & Deployment (`create_fsr_decks.py`):
   Merges fresh Vector data with preserved manual annotations, updates incremental
   AI Next Steps summaries (`data/next_steps_ai_summaries.json`), and updates
   `Follow_up`, `Executive_Summary`, and `Unpartnered_Matchmaker` across all 8 sheets.
4. Post-Sync Enrichment & Drive Cache Sync:
   Re-enriches `data/enriched_portfolio.json` and pushes `data/enriched_portfolio_web.json`
   and `fsr_manual_entries.json` to Google Drive for the shared Apps Script Web App.
"""

import os
import sys
import time
import subprocess

BASE_DIR = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners"


def main():
    start_ts = time.time()
    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)

    print("=" * 70)
    print("🚀 STARTING DAILY BRAZIL FSR ACTION TRACKERS & COMMAND CENTER SYNC")
    print("=" * 70)

    # Step 1: Pre-sync live manual annotations from all 8 Google Sheets
    print("\n[Step 1/3] Capturing live manual annotations from all 8 FSR Google Sheets...")
    from sync_engine import sync_bidirectional
    pre_res = sync_bidirectional()
    print(
        f"  ✓ Pre-sync complete: {pre_res.get('pulled_count', 0)} manual cells pulled from Sheets, "
        f"{pre_res.get('pushed_count', 0)} pending web edits pushed."
    )

    # Step 2: Refresh BigQuery portfolio cache
    print("\n[Step 2/3] Extracting fresh Concord BigQuery data (extract_copilot_data.py)...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "extract_copilot_data.py")], check=True)

    # Step 3: Build and deploy all 8 FSR Action Trackers + update Drive caches
    print("\n[Step 3/3] Updating all 8 Brazil FSR Google Sheets & Command Center caches (create_fsr_decks.py)...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "create_fsr_decks.py")], check=True)

    elapsed = (time.time() - start_ts) / 60.0
    print("\n" + "=" * 70)
    print(f"✅ DAILY FSR SYNC COMPLETED SUCCESSFULLY IN {elapsed:.1f} MINUTES!")
    print("=" * 70)


if __name__ == "__main__":
    main()
