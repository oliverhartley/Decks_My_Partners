#!/usr/bin/env python3
"""
copilot_agent.py
Agentic LLM Copilot & Structured Tool-Calling Engine for the Brazil FSR & Partner Workload Command Center.
"""

import os
import json
import subprocess
from datetime import datetime
from copilot_engine import enrich_portfolio_cache, match_partners_for_workload

BASE_DIR = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners"
ENRICHED_FILE = os.path.join(BASE_DIR, "data", "enriched_portfolio.json")
MANUAL_FILE = os.path.join(BASE_DIR, "fsr_manual_entries.json")
USER_DATA_FILE = os.path.join(BASE_DIR, "data", "workload_user_data.json")
GENERATE_BIN = "/google/bin/releases/gemini-agents-generate/generate"

NOTEBOOKLM_MAP = {
    "vanessa moyses": "9b8a0427-7f9c-4fe8-8264-81808b665d2b",
    "vmmoyses": "9b8a0427-7f9c-4fe8-8264-81808b665d2b",
    "roberta coelho": "6cf8be7c-e5a4-49bf-992e-92b183275a9f",
    "robertacoelho": "6cf8be7c-e5a4-49bf-992e-92b183275a9f",
    "felipe pilon": "9b246927-d973-45b2-a73d-c0feceb84dc1",
    "fpilon": "9b246927-d973-45b2-a73d-c0feceb84dc1",
}


def load_portfolio():
    if not os.path.exists(ENRICHED_FILE):
        return enrich_portfolio_cache()
    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def persist_workload_update(
    workload_id=None,
    query_name=None,
    blocker=None,
    status_tecnico=None,
    partner_technical_email=None,
    technical_win=None,
    proposal_sent=None
):
    data = load_portfolio()
    workloads = data.get("fsr_workloads", [])
    target = None

    for w in workloads:
        if workload_id and w.get("workload_id") == workload_id:
            target = w
            break
    if not target and query_name:
        q = query_name.lower().strip()
        for w in workloads:
            if q in (w.get("workload_name") or "").lower() or q in (w.get("account_name") or "").lower():
                target = w
                break

    if not target:
        return {"status": "error", "message": f"Workload '{workload_id or query_name}' not found."}

    wid = target["workload_id"]
    wname = target["workload_name"]
    now_iso = datetime.now().isoformat()

    # 1. Update fsr_manual_entries.json (used by create_fsr_decks.py)
    manual_entries = {}
    if os.path.exists(MANUAL_FILE):
        try:
            with open(MANUAL_FILE, "r", encoding="utf-8") as f:
                manual_entries = json.load(f)
        except Exception:
            manual_entries = {}

    entry = dict(manual_entries.get(wid) or manual_entries.get(wname, {}))
    pending_web = dict(entry.get("pending_web_edits", {}))
    if blocker is not None:
        entry["blocker"] = blocker
        pending_web["blocker"] = blocker
    if status_tecnico is not None:
        entry["status_tecnico"] = status_tecnico
        pending_web["status_tecnico"] = status_tecnico
    if partner_technical_email is not None:
        entry["partner_tech_email"] = partner_technical_email
        pending_web["partner_tech_email"] = partner_technical_email
    if technical_win is not None:
        entry["technical_win"] = bool(technical_win)
        pending_web["technical_win"] = bool(technical_win)
    if proposal_sent is not None:
        entry["proposal_sent"] = bool(proposal_sent)
        pending_web["proposal_sent"] = bool(proposal_sent)
    entry["pending_web_edits"] = pending_web
    entry["updated_at"] = now_iso
    manual_entries[wid] = entry
    manual_entries[wname] = entry

    with open(MANUAL_FILE, "w", encoding="utf-8") as f:
        json.dump(manual_entries, f, indent=2, ensure_ascii=False)

    # 2. Update data/workload_user_data.json
    user_data = {}
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except Exception:
            user_data = {}

    ud = user_data.get(wid, {"notes": "", "attachments": []})
    if blocker is not None:
        ud["blocker_tecnico"] = blocker
    if status_tecnico is not None:
        ud["status_tecnico"] = status_tecnico
    if partner_technical_email is not None:
        ud["partner_technical_email"] = partner_technical_email
    if technical_win is not None:
        ud["technical_win"] = bool(technical_win)
    if proposal_sent is not None:
        ud["proposal_sent"] = bool(proposal_sent)
    ud["updated_at"] = now_iso
    user_data[wid] = ud

    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

    # 3. Re-enrich portfolio cache so /api/data reflects the fresh touch immediately
    enrich_portfolio_cache()

    # 4. Trigger non-blocking immediate write-through to the FSR's Google Sheet
    try:
        import threading
        from sync_engine import push_single_workload_to_sheet_async
        fsr_user = target.get("workload_owner_username") or target.get("fsr_ldap")
        threading.Thread(
            target=push_single_workload_to_sheet_async,
            args=(fsr_user, wname),
            daemon=True
        ).start()
    except Exception as e:
        print(f"Warning spawning sheet write-through thread: {e}")

    return {
        "status": "success",
        "workload_id": wid,
        "workload_name": wname,
        "account_name": target.get("account_name"),
        "blocker": entry.get("blocker", ""),
        "status_tecnico": entry.get("status_tecnico", ""),
        "partner_technical_email": entry.get("partner_tech_email") or target.get("partner_technical_email") or "",
        "technical_win": bool(entry.get("technical_win", False)),
        "proposal_sent": bool(entry.get("proposal_sent", False)),
        "updated_at": now_iso
    }


def tool_query_workloads(params, workloads):
    fsr = (params.get("fsr") or "").lower().strip()
    pe = (params.get("pe") or "").lower().strip()
    blocker = (params.get("blocker") or "").lower().strip()
    min_days_inactive = int(params.get("min_days_inactive") or 0)
    unpartnered_only = bool(params.get("unpartnered_only", False))
    partner_q = (params.get("partner") or "").lower().strip()
    search_q = (params.get("search") or "").lower().strip()
    min_arr = float(params.get("min_arr") or 0.0)
    limit = int(params.get("limit") or 12)

    matched = []
    for w in workloads:
        if fsr and fsr not in (w.get("workload_owner_name") or "").lower() and fsr not in (w.get("workload_owner_username") or "").lower():
            continue
        if pe and pe not in (w.get("pe_owner") or "").lower():
            continue
        if blocker:
            wb = (w.get("blocker") or "").lower()
            if blocker == "none" and wb != "":
                continue
            elif blocker != "none" and blocker not in wb:
                continue
        days_inact = (w.get("activity_telemetry") or {}).get("days_inactive", 0)
        if min_days_inactive and days_inact < min_days_inactive:
            continue
        if unpartnered_only and w.get("is_partnered"):
            continue
        if partner_q:
            wp = (w.get("partner_name") or "").lower()
            op = (w.get("opportunity_partner_name") or "").lower()
            if partner_q not in wp and partner_q not in op:
                continue
        if search_q:
            blob = f"{w.get('account_name','')} {w.get('workload_name','')} {w.get('opportunity_name','')} {w.get('status_tecnico','')} {w.get('ai_summary_next_steps','')}".lower()
            if search_q not in blob:
                continue
        if float(w.get("annual_gross_revenue") or 0.0) < min_arr:
            continue
        matched.append(w)

    matched.sort(key=lambda x: -float(x.get("annual_gross_revenue") or 0.0))
    total_arr = sum(float(x.get("annual_gross_revenue") or 0.0) for x in matched)

    items = []
    for w in matched[:limit]:
        tel = w.get("activity_telemetry") or {}
        items.append({
            "workload_id": w.get("workload_id"),
            "account_name": w.get("account_name"),
            "opportunity_name": w.get("opportunity_name") or "—",
            "workload_name": w.get("workload_name"),
            "fsr": w.get("workload_owner_name"),
            "arr_usd": round(float(w.get("annual_gross_revenue") or 0.0), 2),
            "stage": w.get("workload_progress_short"),
            "days_inactive": tel.get("days_inactive"),
            "inactivity_tier": tel.get("inactivity_tier"),
            "blocker": w.get("blocker") or "—",
            "status_tecnico": w.get("status_tecnico") or "—",
            "ai_summary_next_steps": w.get("ai_summary_next_steps") or "—",
            "opportunity_partner": w.get("opportunity_partner_name") or "—",
            "workload_partner": w.get("partner_name") or "Unpartnered (No WL Partner)",
            "unpartnered_substatus": w.get("unpartnered_substatus") or ("WL_PARTNERED" if w.get("is_partnered") else ("OPP_PARTNER_ONLY" if w.get("opportunity_partner_name") else "NO_PARTNER_AT_ALL")),
            "partner_technical_email": w.get("partner_technical_email") or "—",
            "primary_ce_email": w.get("primary_ce_email") or "—"
        })

    return {
        "total_matching_workloads": len(matched),
        "total_matching_arr_usd": round(total_arr, 2),
        "top_workloads": items
    }


def tool_draft_stakeholder_nudge(params, workloads):
    wid = params.get("workload_id")
    q = (params.get("workload_name") or params.get("search") or "").lower().strip()
    target = None
    for w in workloads:
        if wid and w.get("workload_id") == wid:
            target = w
            break
    if not target and q:
        for w in workloads:
            if q in (w.get("workload_name") or "").lower() or q in (w.get("account_name") or "").lower():
                target = w
                break
    if not target and workloads:
        target = workloads[0]

    if not target:
        return {"error": "Workload not found"}

    tel = target.get("activity_telemetry") or {}
    days_inact = tel.get("days_inactive", 0)
    recipients = [
        e for e in [
            target.get("partner_technical_email"),
            target.get("primary_ce_email"),
            target.get("workload_owner_email")
        ] if e
    ]
    partner_label = target.get("partner_name") or target.get("opportunity_partner_name") or "Partner Team"
    subject = f"[Action Required] Status Técnico & Próximos Passos: {target.get('account_name')} — {target.get('workload_name')}"
    body = (
        f"Olá time ({target.get('workload_owner_name')}, {target.get('supporting_ce')} & {partner_label}),\n\n"
        f"Estamos revisando o workload '{target.get('workload_name')}' da conta {target.get('account_name')} "
        f"(ARR: ${float(target.get('annual_gross_revenue') or 0):,.2f} | Stage: {target.get('workload_progress_short')}).\n"
        f"Notamos que a última atualização registrada foi há {days_inact} dias.\n"
        f"• Resumo atual: {target.get('ai_summary_next_steps') or 'Sem atualização recente no Vector'}\n"
        f"• Bloqueio: {target.get('blocker') or 'A confirmar'} | Status Técnico: {target.get('status_tecnico') or 'Pendente'}\n\n"
        f"Poderiam confirmar se há algum bloqueio técnico ou comercial e atualizar a data de Go-Live ({target.get('production_date') or 'TBD'})?\n\n"
        f"Link Vector: {target.get('vector_url')}"
    )
    return {
        "workload_id": target.get("workload_id"),
        "account_name": target.get("account_name"),
        "workload_name": target.get("workload_name"),
        "to": recipients,
        "subject": subject,
        "body": body,
        "requires_user_approval": True
    }


def run_agent_chat(user_message, selected_workload_id=None, active_filters=None):
    data = load_portfolio()
    workloads = data.get("fsr_workloads", [])
    candidates = data.get("candidate_partners", [])

    # Compute high-level portfolio digest for grounding
    total_arr = sum(float(w.get("annual_gross_revenue") or 0.0) for w in workloads)
    stalled_30 = [w for w in workloads if (w.get("activity_telemetry") or {}).get("inactivity_tier") == "STALLED_30D"]
    cooling_14 = [w for w in workloads if (w.get("activity_telemetry") or {}).get("inactivity_tier") == "COOLING_14D"]
    tech_blocked = [w for w in workloads if (w.get("blocker") or "").lower() == "tecnico"]
    com_blocked = [w for w in workloads if (w.get("blocker") or "").lower() == "comercial"]

    selected_w = None
    if selected_workload_id:
        for w in workloads:
            if w.get("workload_id") == selected_workload_id:
                selected_w = w
                break

    tool_actions = []
    draft_previews = []
    context_results = {}

    msg_low = (user_message or "").lower()

    # Check if user is asking to update a workload's blocker, status tecnico, or partner email
    router_prompt = f"""You are an AI router for the Brazil FSR Workload Command Center.
Analyze the user message and return ONLY a single valid JSON object with "intent" and "params".
Possible intents:
1. "UPDATE_WORKLOAD": User wants to set/update blocker ("Comercial" or "Tecnico"), status_tecnico, or partner_technical_email on a workload.
   params: {{"workload_name": "...", "blocker": "Tecnico|Comercial|null", "status_tecnico": "...|null", "partner_technical_email": "...|null"}}
2. "DRAFT_NUDGE": User wants to draft an email/message/ping/nudge to the partner technical owner, CE, or FSR.
   params: {{"workload_name": "..."}}
3. "MATCH_PARTNER": User asks for partner recommendations/matchmaking for an unpartnered workload.
   params: {{"workload_name": "...", "fsr": "..."}}
4. "QUERY_PORTFOLIO": User asks a question about workloads, stalled deals, technical blockers, FSRs, or partners.
   params: {{"fsr": "", "pe": "", "blocker": "", "min_days_inactive": 0, "unpartnered_only": false, "partner": "", "search": "", "min_arr": 0}}

Selected workload context: {selected_w.get('workload_name') if selected_w else 'None'}
Active UI filters: {json.dumps(active_filters or {})}
User message: {user_message}
JSON:"""

    routed = {"intent": "QUERY_PORTFOLIO", "params": {}}
    if os.path.exists(GENERATE_BIN):
        try:
            res = subprocess.run([GENERATE_BIN, "text", router_prompt], capture_output=True, text=True, timeout=12)
            if res.returncode == 0 and res.stdout.strip():
                raw = res.stdout.strip()
                start_idx = raw.find("{")
                end_idx = raw.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    routed = json.loads(raw[start_idx:end_idx + 1])
        except Exception:
            pass

    intent = routed.get("intent", "QUERY_PORTFOLIO")
    params = routed.get("params") or {}

    # Deterministic heuristics backup for fast responsiveness
    if any(k in msg_low for k in ["stalled", "dormant", "nothing", "inactive", "no activity", "parado", "sem atualização", "no touch"]):
        if not params.get("min_days_inactive"):
            params["min_days_inactive"] = 14
    if "tecnico" in msg_low or "técnico" in msg_low or "technical blocker" in msg_low:
        if intent == "QUERY_PORTFOLIO" and not params.get("blocker"):
            params["blocker"] = "tecnico"
    for fsr_key in ["pilon", "roberta", "coelho", "vanessa", "moyses", "daniela", "benevides", "prudencio", "sarah", "tobias", "anagama", "ana", "gama", "renan", "valadares"]:
        if fsr_key in msg_low and not params.get("fsr"):
            params["fsr"] = fsr_key

    if intent == "UPDATE_WORKLOAD":
        upd_res = persist_workload_update(
            workload_id=selected_workload_id if not params.get("workload_name") else None,
            query_name=params.get("workload_name"),
            blocker=params.get("blocker"),
            status_tecnico=params.get("status_tecnico"),
            partner_technical_email=params.get("partner_technical_email")
        )
        tool_actions.append({"tool": "update_workload_tracking", "result": upd_res})
        context_results["update_result"] = upd_res

    elif intent == "DRAFT_NUDGE":
        draft = tool_draft_stakeholder_nudge(
            {"workload_id": selected_workload_id, "workload_name": params.get("workload_name")},
            workloads
        )
        draft_previews.append(draft)
        tool_actions.append({"tool": "draft_stakeholder_nudge", "result": {"workload": draft.get("workload_name"), "to": draft.get("to")}})
        context_results["draft"] = draft

    elif intent == "MATCH_PARTNER":
        q_res = tool_query_workloads({"fsr": params.get("fsr"), "search": params.get("workload_name"), "unpartnered_only": True, "limit": 5}, workloads)
        matches_out = []
        for item in q_res.get("top_workloads", []):
            w_obj = next((x for x in workloads if x.get("workload_id") == item["workload_id"]), None)
            if w_obj:
                top2 = match_partners_for_workload(w_obj, candidates)
                matches_out.append({
                    "workload_name": w_obj.get("workload_name"),
                    "account_name": w_obj.get("account_name"),
                    "arr_usd": w_obj.get("annual_gross_revenue"),
                    "recommended_partners": top2
                })
        tool_actions.append({"tool": "match_brazil_partners", "result": {"count": len(matches_out)}})
        context_results["partner_matches"] = matches_out

    # Always include top relevant workloads for grounding
    q_data = tool_query_workloads(params, workloads)
    context_results["query_results"] = q_data

    # Synthesize final answer with Gemini
    synth_prompt = f"""You are the Agentic Workload Copilot for Oliver Hartley & Luna Longo's Brazil FSR Portfolio (513 active workloads, ${total_arr:,.0f} ARR).
Portfolio Snapshot:
- Stalled >=30d (No touch): {len(stalled_30)} workloads
- Cooling 14-29d: {len(cooling_14)} workloads
- Active Technical Blockers (Tecnico): {len(tech_blocked)} workloads
- Active Commercial Blockers (Comercial): {len(com_blocked)} workloads

Selected Workload: {json.dumps({k: selected_w.get(k) for k in ('workload_name','account_name','annual_gross_revenue','workload_progress_short','blocker','status_tecnico','ai_summary_next_steps','partner_name','opportunity_partner_name','partner_technical_email','activity_telemetry')} if selected_w else None, ensure_ascii=False)}

Tool Execution & Query Context:
{json.dumps(context_results, ensure_ascii=False)}

User Question / Command:
{user_message}

Instructions:
- Be concise, executive, and actionable (use bullet points and bold key numbers/names).
- Cite specific Customer Account Names, Workload Names, ARR ($), Days Inactive, and Partner Technical Owner Emails when available.
- If a workload was updated or a draft was created, confirm it clearly.
"""

    reply_text = ""
    if os.path.exists(GENERATE_BIN):
        try:
            res = subprocess.run([GENERATE_BIN, "text", synth_prompt], capture_output=True, text=True, timeout=18)
            if res.returncode == 0 and res.stdout.strip():
                reply_text = res.stdout.strip()
        except Exception:
            pass

    if not reply_text:
        top_w = q_data.get("top_workloads", [])[:5]
        lines = [
            f"**Portfolio Match**: **{q_data.get('total_matching_workloads', 0)} workloads** (${q_data.get('total_matching_arr_usd', 0):,.2f} ARR).",
        ]
        for item in top_w:
            lines.append(
                f"- **{item['account_name']} — {item['workload_name']}** (${item['arr_usd']:,.0f} | Stage `{item['stage']}` | "
                f"`{item['days_inactive']}d inactive` | Bloqueo: `{item['blocker']}` | Partner Email: `{item['partner_technical_email']}`)"
            )
        reply_text = "\n".join(lines)

    return {
        "reply": reply_text,
        "tool_actions": tool_actions,
        "draft_previews": draft_previews,
        "matching_summary": {
            "count": q_data.get("total_matching_workloads", 0),
            "arr_usd": q_data.get("total_matching_arr_usd", 0)
        }
    }
