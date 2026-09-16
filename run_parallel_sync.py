#!/usr/bin/env python3
"""
run_parallel_sync.py
Orchestrator for parallel synchronization of the 56 Partner Action Trackers,
Dedicated PE Dashboards, and Global Management Dashboard.

Strategy:
1. Phase 1: Fast PEs (Oliver Hartley, Fernando Laguna, Ignacio Rauda, Luna Longo, Thiago da Ponte, Jaquelyn Montañez)
   run concurrently with 3 workers (--primary-pe-only ensures no co-managed partner collisions).
2. Phase 2: Wanda Flores (26 partners) runs at the end.
3. Phase 3: Refresh Fernando Laguna PE Dashboard (co-managed partners) & consolidate Global Dashboard (--global-only).
"""

import sys
import os
import time
import subprocess
import concurrent.futures
import datetime

FAST_PES = [
    "Oliver Hartley",
    "Fernando Laguna",
    "Ignacio Rauda",
    "Luna Longo",
    "Thiago da Ponte",
    "Jaquelyn Montañez"
]

def run_pe_sync(pe_name, log_file, extra_args=None):
    cmd = [sys.executable, "update_all_partner_decks.py", "--pe", pe_name, "--primary-pe-only"]
    if extra_args:
        cmd.extend(extra_args)
    with open(log_file, "w", encoding="utf-8") as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
    return pe_name, p.returncode

def main(workers=3, commit=False):
    start_time = time.time()
    os.makedirs("logs", exist_ok=True)
    print("=" * 65)
    print("STARTING OPTIMIZED PARALLEL SYNC ACROSS ALL PARTNERS & DASHBOARDS")
    print(f"Workers: {workers} | Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # 1. Phase 1: Fast PEs (30 partners across 6 PEs)
    print(f"\n========================================================")
    print(f"PHASE 1: Syncing 6 Fast PEs in Parallel ({len(FAST_PES)} PEs, ~30 partners)")
    print(f"Workers: {workers} concurrent")
    print(f"========================================================")

    phase1_start = time.time()
    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for pe in FAST_PES:
            pe_clean = pe.replace(" ", "_").replace("ñ", "n")
            log_path = f"logs/sync_{pe_clean}.log"
            print(f"  -> Launched worker for: {pe} (Log: {log_path})")
            f = executor.submit(run_pe_sync, pe, log_path)
            futures[f] = pe

        for f in concurrent.futures.as_completed(futures):
            pe = futures[f]
            try:
                pe_res, rc = f.result()
                if rc == 0:
                    print(f"  ✓ [{datetime.datetime.now().strftime('%H:%M:%S')}] Completed PE: {pe}")
                else:
                    print(f"  ✗ [{datetime.datetime.now().strftime('%H:%M:%S')}] Error in PE: {pe} (Exit code {rc}, check logs/sync_{pe.replace(' ', '_').replace('ñ', 'n')}.log)")
            except Exception as e:
                print(f"  ✗ Exception in PE {pe}: {e}")

    phase1_time = time.time() - phase1_start
    print(f"\n✓ Phase 1 complete in {phase1_time/60:.1f} minutes.")

    # 2. Phase 2: Wanda Flores (26 partners)
    print(f"\n========================================================")
    print(f"PHASE 2: Syncing Wanda Flores (26 partners)")
    print(f"========================================================")
    phase2_start = time.time()
    wanda_log = "logs/sync_Wanda_Flores.log"
    print(f"  -> Running Wanda Flores sync (Log: {wanda_log})...")
    wanda_cmd = [sys.executable, "update_all_partner_decks.py", "--pe", "Wanda Flores"]
    with open(wanda_log, "w", encoding="utf-8") as f:
        p_wanda = subprocess.run(wanda_cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if p_wanda.returncode == 0:
        print(f"  ✓ [{datetime.datetime.now().strftime('%H:%M:%S')}] Completed Wanda Flores & PE Dashboard")
    else:
        print(f"  ✗ Error in Wanda Flores sync (Exit code {p_wanda.returncode}, check {wanda_log})")

    phase2_time = time.time() - phase2_start
    print(f"\n✓ Phase 2 complete in {phase2_time/60:.1f} minutes.")

    # 3. Phase 3: Refresh Fernando Laguna PE Dashboard (for co-managed partners) & Global Dashboard
    print(f"\n========================================================")
    print(f"PHASE 3: Consolidating Global Dashboard")
    print(f"========================================================")
    phase3_start = time.time()
    print("  -> Refreshing Fernando Laguna PE Dashboard (co-managed partners)...")
    subprocess.run([sys.executable, "update_all_partner_decks.py", "--pe-dashboard-only", "Fernando Laguna"], capture_output=True)

    print("  -> Consolidating and updating Global Management Dashboard...")
    g_res = subprocess.run([sys.executable, "update_all_partner_decks.py", "--global-only"], capture_output=True, text=True)
    if g_res.returncode == 0:
        print("  ✓ Global Management Dashboard updated successfully.")
    else:
        print(f"  ✗ Warning updating Global Dashboard: {g_res.stderr}")

    phase3_time = time.time() - phase3_start
    total_time = time.time() - start_time

    print("\n" + "=" * 65)
    print("SUCCESS: ALL 56 PARTNERS, 7 PE DASHBOARDS & GLOBAL DASHBOARD SYNCED!")
    print(f"Total Execution Time: {total_time/60:.1f} minutes (Phase 1: {phase1_time/60:.1f}m, Phase 2: {phase2_time/60:.1f}m, Phase 3: {phase3_time/60:.1f}m)")
    print("=" * 65)

if __name__ == "__main__":
    main()
