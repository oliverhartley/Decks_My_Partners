#!/usr/bin/env python3
"""
copilot_engine.py
Core Intelligence Engine for Workload Acceleration Copilot.

Laser-focused on:
1. Brazil FSR Workloads: Felipe Pilon, Roberta Coelho, Vanessa Moyses + CE Diego Baldini.
2. Next Steps History analysis (detecting stalled deals without momentum).
3. Partner Matchmaker for unpartnered workloads (evaluating all Brazil partners + Oliver's bench).
4. Stage-based categorization (Stage 0-1, Stage 2, Stage 3, Stage 4+).
5. Concept 3: Predictive Capacity & Enablement Sprints.
"""

import json
from datetime import datetime, date

TODAY = date.today()


def parse_date(date_str):
    if not date_str or str(date_str) in ('None', 'null', ''):
        return None
    try:
        return datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
    except:
        return None


def calculate_days_until(target_date):
    if not target_date:
        return None
    return (target_date - TODAY).days


def get_stage_bucket(stage_name):
    s = (stage_name or '').lower()
    if '00' in s or '01' in s or 'qualif' in s or 'refine' in s or 'stage 0' in s or 'stage 1' in s:
        return "STAGE_0_1"
    elif '02' in s or 'tech eval' in s or 'solution dev' in s or 'stage 2' in s or 'scoping' in s:
        return "STAGE_2"
    elif '03' in s or 'proposal' in s or 'negotiat' in s or 'stage 3' in s or 'validation' in s:
        return "STAGE_3"
    elif '04' in s or 'migration' in s or 'implement' in s or 'stage 4' in s or 'won' in s or 'inflight' in s:
        return "STAGE_4_PLUS"
    return "STAGE_2" # default middle


def match_partners_for_workload(workload, candidate_partners):
    """
    Ranks candidate partners (Brazil partners + Oliver's 6) for an unpartnered deal.
    """
    w_prods = [p.lower() for p in workload.get('key_workload_products', []) if p]
    w_pillar = (workload.get('pillar') or '').lower()
    w_play = (workload.get('sales_play') or '').lower()

    scored_candidates = []

    for p in candidate_partners:
        score = 0
        matching_products = []
        matching_tier1 = 0
        matching_tier2 = 0

        # 1. Product & Solution DRP Match
        for b in p.get('drp_bench', []):
            b_prod = (b.get('product') or '').lower()
            b_pillar = (b.get('pillar') or '').lower()
            b_sol = (b.get('solution') or '').lower()
            t1 = b.get('tier1_count', 0)
            t2 = b.get('tier2_count', 0)

            if any(wp in b_prod or b_prod in wp for wp in w_prods) and b_prod != 'all products':
                score += (t1 * 18) + (t2 * 9)
                matching_products.append(b.get('product'))
                matching_tier1 += t1
                matching_tier2 += t2
            elif (w_pillar and w_pillar in b_pillar) or (w_play and w_play in b_sol):
                score += (t1 * 5) + (t2 * 2)

        # 2. Tier Level Bonus
        if p.get('tier_level') == 'Premier':
            score += 10
        elif p.get('tier_level') == 'Select':
            score += 5

        # 3. Vector Support Case Penalty
        p1_p2 = p.get('vector_p1_p2_count', 0)
        if p1_p2 > 3:
            score -= (p1_p2 * 2)

        matching_products = list(set(matching_products))

        if score > 0 or matching_tier1 > 0 or matching_tier2 > 0:
            # Generate explicit selection logic
            reasons = []
            if matching_products:
                prods_str = ", ".join(matching_products[:3])
                reasons.append(f"Architectural match with {matching_tier1} Tier 1 & {matching_tier2} Tier 2 certified practitioners in {prods_str}")
            elif matching_tier1 + matching_tier2 > 0:
                reasons.append(f"Strong cloud delivery bench with {matching_tier1 + matching_tier2} certified architects in {w_pillar or 'Cloud Architecture'}")
            else:
                reasons.append(f"Proven delivery track record across enterprise migrations in Brazil")

            if p.get('tier_level') == 'Premier':
                reasons.append("Premier Google Cloud Partner tier standing in Brazil")
            elif p.get('tier_level') == 'Select':
                reasons.append("Select tier partner with dedicated local technical delivery teams")

            if p1_p2 == 0:
                reasons.append("Clean technical delivery record with 0 critical Vector support escalations in the last 6 months")
            else:
                reasons.append(f"Successfully resolved {p1_p2} technical consults with verified delivery completion")

            logic_summary = ". ".join(reasons) + "."

            scored_candidates.append({
                "partner_name": p['partner_name'],
                "country": p.get('country'),
                "tier_level": p.get('tier_level') or 'Select',
                "score": score,
                "matching_products": matching_products,
                "tier1_bench": matching_tier1,
                "tier2_bench": matching_tier2,
                "vector_p1_p2_cases": p1_p2,
                "selection_logic": logic_summary
            })

    # Sort descending by match score and return exactly top 2
    scored_candidates.sort(key=lambda x: (x['score'], x['tier1_bench']), reverse=True)
    return scored_candidates[:2]


def diagnose_workload(w, partner_bench_map, all_match_candidates):
    bottlenecks = []
    actions = []
    prod_date = parse_date(w.get('production_date'))
    days_to_prod = calculate_days_until(prod_date)
    stage = w.get('stage_name') or w.get('workload_progress') or ''
    stage_bucket = get_stage_bucket(stage)
    is_partnered = w.get('is_partnered', False)
    w_prods = w.get('key_workload_products', [])
    p1_p2_cases = w.get('vector_p1_p2_count', 0)
    matched_partners = []

    # 1. Next Steps History Analysis
    ns_history = w.get('next_steps_history', [])
    last_ns_date_str = w.get('last_next_step_date')
    days_since_ns = None
    if last_ns_date_str:
        last_ns_date = parse_date(last_ns_date_str)
        if last_ns_date:
            days_since_ns = (TODAY - last_ns_date).days

    if days_since_ns is not None and days_since_ns > 35:
        bottlenecks.append({
            "code": "STALLED_NEXT_STEP",
            "severity": "HIGH",
            "title": f"Next Step Unchanged for {days_since_ns} Days",
            "description": f"Last logged update was on {last_ns_date_str}: \"{ns_history[0]['text'][:80]}...\". Deal may be stalling."
        })
    elif not ns_history and stage_bucket in ('STAGE_2', 'STAGE_3'):
        bottlenecks.append({
            "code": "NO_NEXT_STEPS",
            "severity": "MEDIUM",
            "title": "No Next Steps Documented",
            "description": "Workload lacks a documented action plan in Salesforce/Vector."
        })

    # 2. Unpartnered Deal Matchmaking
    if not is_partnered:
        bottlenecks.append({
            "code": "UNPARTNERED",
            "severity": "HIGH",
            "title": "Deal Has No Delivery Partner Attached",
            "description": f"Workload is in {stage} with no attached partner. Customer requires delivery capacity."
        })
        matched_partners = match_partners_for_workload(w, all_match_candidates)
        if matched_partners:
            top_p = matched_partners[0]
            actions.append({
                "type": "PARTNER_ATTACHMENT",
                "title": f"Introduce {top_p['partner_name']} to FSR & Diego Baldini",
                "detail": f"{top_p['partner_name']} offers {top_p['tier1_bench']} Tier 1 certified practitioners for required architecture.",
                "draft_recipient": f"{w.get('workload_owner_name')}, Diego Baldini",
                "draft_subject": f"Partner Recommendation: {w.get('account_name')} ({w.get('workload_name')})"
            })
    else:
        # 3. Partner Capacity Check
        p_name = w.get('partner_name') or ''
        p_bench = partner_bench_map.get(p_name, [])
        if w_prods:
            matched_bench = 0
            for wp in w_prods:
                wp_low = wp.lower()
                for b in p_bench:
                    if wp_low in (b.get('product') or '').lower():
                        matched_bench += b.get('total', 0)
            if matched_bench == 0:
                bottlenecks.append({
                    "code": "CAPACITY_GAP",
                    "severity": "HIGH",
                    "title": f"{p_name} Has 0 Scored DRP for Deal Products",
                    "description": f"Workload requires {', '.join(w_prods)}, but {p_name} has 0 DRP Tier 1/2 bench recorded."
                })
                actions.append({
                    "type": "ENABLEMENT_DRP",
                    "title": f"Fast-Track DRP Validation for {p_name}",
                    "detail": f"Check LMS certifications or pair with specialist partner.",
                    "draft_recipient": f"{p_name} Delivery Lead, Diego Baldini",
                    "draft_subject": f"Delivery Capacity Readiness: {w.get('workload_name')}"
                })

    # 4. Milestone Collision
    if days_to_prod is not None:
        if days_to_prod < 0:
            bottlenecks.append({
                "code": "OVERDUE_MILESTONE",
                "severity": "CRITICAL",
                "title": f"Target Production Date Overdue by {abs(days_to_prod)} Days",
                "description": f"Target date was {w.get('production_date')}, but stage remains {stage}."
            })
            actions.append({
                "type": "MILESTONE_RESET",
                "title": "Timeline Alignment with Diego Baldini",
                "detail": "Coordinate with FSR and CE Diego Baldini to reset the go-live milestone in Vector.",
                "draft_recipient": f"{w.get('workload_owner_name')}, Diego Baldini",
                "draft_subject": f"Timeline Alignment: {w.get('account_name')} ({w.get('workload_name')})"
            })
        elif days_to_prod <= 30 and stage_bucket in ('STAGE_0_1', 'STAGE_2', 'STAGE_3'):
            bottlenecks.append({
                "code": "IMMINENT_COLLISION",
                "severity": "HIGH",
                "title": f"Go-Live in {days_to_prod} Days in Early Stage ({stage})",
                "description": "High risk of delivery compression."
            })

    # 5. Vector Technical Cases
    if p1_p2_cases > 0:
        bottlenecks.append({
            "code": "VECTOR_CRITICAL_CASES",
            "severity": "HIGH",
            "title": f"{p1_p2_cases} Critical Support Cases (P1/P2) in Last 6M",
            "description": "Customer has recent severe support escalations. Architectural caution advised."
        })

    # Overall Priority Badge
    if any(b['severity'] == 'CRITICAL' for b in bottlenecks):
        overall_status = "CRITICAL"
    elif any(b['severity'] == 'HIGH' for b in bottlenecks):
        overall_status = "HIGH_RISK"
    elif not is_partnered:
        overall_status = "MATCH_NEEDED"
    elif any(b['severity'] == 'MEDIUM' for b in bottlenecks):
        overall_status = "MEDIUM_RISK"
    else:
        overall_status = "ON_TRACK"

    return {
        "status": overall_status,
        "stage_bucket": stage_bucket,
        "days_to_prod": days_to_prod,
        "days_since_next_step": days_since_ns,
        "bottlenecks": bottlenecks,
        "recommended_actions": actions,
        "matched_partners": matched_partners
    }


def compute_predictive_capacity_matrix(cache_data):
    fsr_wkls = cache_data.get('fsr_workloads', [])

    product_demand = {}
    for w in fsr_wkls:
        prods = w.get('key_workload_products') or []
        rev = w.get('annual_gross_revenue', 0.0)
        owner = w.get('workload_owner_name') or 'Other'
        pillar = w.get('pillar') or 'General'

        for p in prods:
            if not p:
                continue
            if p not in product_demand:
                product_demand[p] = {
                    "product": p,
                    "pillar": pillar,
                    "total_workloads": 0,
                    "total_pipeline_value": 0.0,
                    "unpartnered_workloads": 0,
                    "unpartnered_value": 0.0,
                    "by_fsr": {}
                }
            product_demand[p]["total_workloads"] += 1
            product_demand[p]["total_pipeline_value"] += rev
            if not w.get('is_partnered'):
                product_demand[p]["unpartnered_workloads"] += 1
                product_demand[p]["unpartnered_value"] += rev
            product_demand[p]["by_fsr"][owner] = product_demand[p]["by_fsr"].get(owner, 0) + 1

    partner_supply = {}
    candidate_partners = cache_data.get('candidate_partners', [])
    for p in candidate_partners:
        pname = p['partner_name']
        for b in p.get('drp_bench', []):
            prod = b.get('product')
            if not prod or prod == 'All Products':
                continue
            if prod not in partner_supply:
                partner_supply[prod] = {
                    "tier1_total": 0,
                    "tier2_total": 0,
                    "partners_with_bench": []
                }
            t1 = b.get('tier1_count', 0)
            t2 = b.get('tier2_count', 0)
            partner_supply[prod]["tier1_total"] += t1
            partner_supply[prod]["tier2_total"] += t2
            if t1 > 0 or t2 > 0:
                partner_supply[prod]["partners_with_bench"].append({
                    "partner": pname,
                    "t1": t1,
                    "t2": t2
                })

    gap_matrix = []
    for prod, d in product_demand.items():
        supply = partner_supply.get(prod, {"tier1_total": 0, "tier2_total": 0, "partners_with_bench": []})
        t1 = supply["tier1_total"]
        t2 = supply["tier2_total"]
        bench_count = len(supply["partners_with_bench"])

        gap_severity = "HEALTHY"
        if bench_count == 0 and d["total_workloads"] >= 2:
            gap_severity = "CRITICAL_DEFICIT"
        elif bench_count <= 2 and d["total_pipeline_value"] > 500000:
            gap_severity = "HIGH_EXPOSURE"
        elif t1 == 0 and d["total_workloads"] >= 3:
            gap_severity = "TIER1_GAP"

        gap_matrix.append({
            "product": prod,
            "pillar": d["pillar"],
            "workloads_count": d["total_workloads"],
            "pipeline_revenue": d["total_pipeline_value"],
            "unpartnered_count": d["unpartnered_workloads"],
            "unpartnered_revenue": d["unpartnered_value"],
            "tier1_certified_bench": t1,
            "tier2_certified_bench": t2,
            "qualified_partner_count": bench_count,
            "qualified_partners": [x['partner'] for x in supply["partners_with_bench"][:3]],
            "gap_severity": gap_severity
        })

    gap_matrix.sort(key=lambda x: (x['unpartnered_revenue'], x['pipeline_revenue']), reverse=True)

    enablement_sprints = []
    for item in gap_matrix:
        if item['gap_severity'] in ('CRITICAL_DEFICIT', 'HIGH_EXPOSURE', 'TIER1_GAP'):
            enablement_sprints.append({
                "product": item['product'],
                "pillar": item['pillar'],
                "unlocked_revenue": item['pipeline_revenue'],
                "impact_statement": f"Enabling 2 partner engineers on {item['product']} will unlock ${round(item['pipeline_revenue']/1000, 1)}k across {item['workloads_count']} upcoming FSR deals.",
                "target_partners": ["MadeinWeb S/A", "IPNET", "SantoDigital", "Tech Pulse SPA"]
            })

    return {
        "demand_matrix": gap_matrix,
        "recommended_enablement_sprints": enablement_sprints[:5]
    }


def enrich_portfolio_cache():
    import os
    base_dir = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners"
    cache_path = os.path.join(base_dir, "data", "portfolio_cache.json")
    ai_summaries_path = os.path.join(base_dir, "data", "next_steps_ai_summaries.json")
    manual_entries_path = os.path.join(base_dir, "fsr_manual_entries.json")
    user_data_path = os.path.join(base_dir, "data", "workload_user_data.json")

    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)

    ai_summaries = {}
    if os.path.exists(ai_summaries_path):
        try:
            with open(ai_summaries_path, "r", encoding="utf-8") as f:
                ai_summaries = json.load(f)
        except Exception:
            pass

    manual_entries = {}
    if os.path.exists(manual_entries_path):
        try:
            with open(manual_entries_path, "r", encoding="utf-8") as f:
                manual_entries = json.load(f)
        except Exception:
            pass

    user_data = {}
    if os.path.exists(user_data_path):
        try:
            with open(user_data_path, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except Exception:
            pass

    candidate_partners = cache.get('candidate_partners', [])
    partner_bench_map = {p['partner_name']: p.get('drp_bench', []) for p in candidate_partners}

    oliver_users = {'fpilon', 'robertacoelho', 'vmmoyses', 'anagama'}
    oliver_names = {'felipe pilon', 'roberta coelho', 'vanessa moyses', 'ana luiza gama', 'ana gama'}

    for w in cache.get('fsr_workloads', []):
        wid = w.get('workload_id') or ''
        wname = w.get('workload_name') or ''
        owner_user = (w.get('workload_owner_username') or '').lower().strip()
        owner_name = (w.get('workload_owner_name') or '').lower().strip()

        if owner_user in oliver_users or owner_name in oliver_names:
            w['pe_owner'] = "Oliver Hartley"
            w['supporting_ce'] = "Diego Baldini"
            default_ce_email = "diegobaldini@google.com"
        else:
            w['pe_owner'] = "Luna Longo"
            w['supporting_ce'] = "Victor Hugo Ferreira"
            default_ce_email = "vhferreira@google.com"

        w['workload_owner_email'] = f"{owner_user}@google.com" if owner_user and "@" not in owner_user else (owner_user or "")
        ce_user = (w.get('primary_ce_username') or '').strip()
        w['primary_ce_email'] = (f"{ce_user}@google.com" if "@" not in ce_user else ce_user) if ce_user else default_ce_email

        progress = w.get('workload_progress') or ''
        w['workload_progress_short'] = progress.split(':')[0].strip() if ':' in progress else progress.strip()

        impl_dt = parse_date(w.get('begin_migration_date'))
        prod_dt = parse_date(w.get('production_date'))
        w['days_until_implementation'] = calculate_days_until(impl_dt)
        w['days_until_production'] = calculate_days_until(prod_dt)

        m_entry = manual_entries.get(wid) or manual_entries.get(wname, {})
        ud = user_data.get(wid, {})

        w['blocker'] = ud.get('blocker_tecnico') or m_entry.get('blocker') or ''
        w['status_tecnico'] = ud.get('status_tecnico') or m_entry.get('status_tecnico') or ''
        w['partner_technical_email'] = (
            ud.get('partner_technical_email')
            or m_entry.get('partner_tech_email')
            or w.get('partner_technical_email')
            or ''
        )
        raw_tw = ud.get('technical_win') if 'technical_win' in ud else m_entry.get('technical_win')
        raw_ps = ud.get('proposal_sent') if 'proposal_sent' in ud else m_entry.get('proposal_sent')
        w['technical_win'] = bool(raw_tw) if isinstance(raw_tw, bool) else str(raw_tw or '').strip().upper() in ('TRUE', '1', 'YES')
        w['proposal_sent'] = bool(raw_ps) if isinstance(raw_ps, bool) else str(raw_ps or '').strip().upper() in ('TRUE', '1', 'YES')

        ai_entry = ai_summaries.get(wid, {})
        ai_text = ai_entry.get('summary') or ''
        if not ai_text:
            ns_hist = w.get('next_steps_history') or []
            if ns_hist:
                ai_text = f"[{ns_hist[0].get('date', '')}] {ns_hist[0].get('text', '')[:140]}"
            elif w.get('next_steps'):
                ai_text = str(w.get('next_steps'))[:140]
        w['ai_summary_next_steps'] = ai_text

        w['diagnosis'] = diagnose_workload(w, partner_bench_map, candidate_partners)
        w['stage_bucket'] = w['diagnosis']['stage_bucket']

        # Compute Activity & Staleness Telemetry
        vec_ns_date = w.get('last_next_step_date') or ''
        man_upd_date = (ud.get('updated_at') or m_entry.get('updated_at') or '')[:10]
        candidates_dates = [d for d in (vec_ns_date, man_upd_date) if parse_date(d) is not None]
        if candidates_dates:
            eff_date_str = max(candidates_dates)
        else:
            eff_date_str = (w.get('workload_last_modified_date') or w.get('sfdc_created_date') or '')[:10]

        eff_dt = parse_date(eff_date_str)
        days_inactive = (TODAY - eff_dt).days if eff_dt else 60
        if days_inactive < 0:
            days_inactive = 0

        if days_inactive >= 30 or (not vec_ns_date and not man_upd_date and w['stage_bucket'] in ('STAGE_2', 'STAGE_3')):
            inactivity_tier = "STALLED_30D"
        elif days_inactive >= 14:
            inactivity_tier = "COOLING_14D"
        else:
            inactivity_tier = "ACTIVE"

        w['activity_telemetry'] = {
            "last_vector_next_step_date": vec_ns_date or None,
            "last_manual_update_date": man_upd_date or None,
            "effective_last_touch_date": eff_date_str or None,
            "last_activity_date": eff_date_str or None,
            "days_inactive": days_inactive,
            "inactivity_tier": inactivity_tier,
            "is_stalled": inactivity_tier in ("STALLED_30D", "COOLING_14D")
        }

        # Normalized fields for frontend Action Grid, Unpartnered Control & Executive Overview
        w['arr'] = float(w.get('annual_gross_revenue') or 0.0)
        w['pdm_owner'] = w['pe_owner']
        w['fsr_ldap'] = owner_user
        w['fsr_name'] = w.get('workload_owner_name') or owner_user
        w['stage'] = w.get('workload_progress') or ''
        w['implementation_date'] = w.get('begin_migration_date') or ''
        w['opportunity_partner'] = (w.get('opportunity_partner_name') or '').strip()
        w['workload_partner'] = (w.get('partner_name') or '').strip()

        has_wl_partner = bool(w.get('is_partnered') and w['workload_partner'])
        has_opp_partner = bool(w['opportunity_partner'])
        w['has_workload_partner'] = has_wl_partner
        w['has_opportunity_partner'] = has_opp_partner
        w['partner_status'] = 'PARTNERED' if has_wl_partner else 'UNPARTNERED'
        if has_wl_partner:
            w['unpartnered_substatus'] = 'WL_PARTNERED'
        elif has_opp_partner:
            w['unpartnered_substatus'] = 'OPP_PARTNER_ONLY'
        else:
            w['unpartnered_substatus'] = 'NO_PARTNER_AT_ALL'

        aid = w.get('sfdc_account_id') or ''
        opp_id = w.get('opportunity_id') or ''
        opp_pid = w.get('opportunity_partner_id') or ''
        pid = w.get('partner_id') or ''
        w['account_url'] = w.get('acc_url') or (f"https://vector.lightning.force.com/lightning/r/Account/{aid}/view" if aid else "")
        w['opportunity_url'] = w.get('opp_url') or (f"https://vector.lightning.force.com/lightning/r/Opportunity/{opp_id}/view" if opp_id else "")
        w['workload_url'] = w.get('vector_url') or (f"https://vector.lightning.force.com/lightning/r/Workload__c/{wid}/view" if wid else "")
        w['opportunity_partner_url'] = f"https://vector.lightning.force.com/lightning/r/Account/{opp_pid}/view" if opp_pid else ""
        w['workload_partner_url'] = f"https://vector.lightning.force.com/lightning/r/Account/{pid}/view" if pid else ""

        w['partner_recommendations'] = [
            {
                "partner": mp.get("partner_name"),
                "tier": mp.get("tier_level") or "Select",
                "score": mp.get("score"),
                "tier1_bench": mp.get("tier1_bench", 0),
                "tier2_bench": mp.get("tier2_bench", 0),
                "reason": mp.get("selection_logic") or ""
            }
            for mp in (w['diagnosis'].get('matched_partners') or [])
        ]

    predictive_data = compute_predictive_capacity_matrix(cache)
    cache['predictive_capacity'] = predictive_data
    cache['workloads'] = cache.get('fsr_workloads', [])
    cache['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    out_file = os.path.join(base_dir, "data", "enriched_portfolio.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"✅ Enriched portfolio saved to {out_file} ({len(cache.get('fsr_workloads', []))} workloads)")
    return cache


if __name__ == "__main__":
    enrich_portfolio_cache()
