#!/usr/bin/env python3
"""
server.py
Lightweight HTTP Server and REST API for Partner Velocity Copilot.
Supports:
- Focus toggles (persisted in data/focus_workloads.json)
- User notes & Google Drive attachments (persisted in data/workload_user_data.json)
- Dynamic data injection & BigQuery refresh
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = "/usr/local/google/home/oliverhartley/jetski-workspace/Decks_My_Partners"
WEB_DIR = os.path.join(BASE_DIR, "web")
DATA_FILE = os.path.join(BASE_DIR, "data", "enriched_portfolio.json")
FOCUS_FILE = os.path.join(BASE_DIR, "data", "focus_workloads.json")
USER_DATA_FILE = os.path.join(BASE_DIR, "data", "workload_user_data.json")
GTASKS_BIN = "/google/bin/releases/gemini-agents-gtasks/gtasks"
PORT = 8080


def get_gtasks_lists():
    if not os.path.exists(GTASKS_BIN):
        return []
    try:
        res = subprocess.run([GTASKS_BIN, "list-tasklists", "--json"], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        print(f"Error listing gtasks lists: {e}")
        return []


def create_gtask(tasklist_id, title, notes="", due=""):
    if not os.path.exists(GTASKS_BIN):
        raise RuntimeError("gtasks CLI not found")
    cmd = [GTASKS_BIN, "create-task", tasklist_id, "--title", title, "--json"]
    if notes:
        cmd.extend(["--notes", notes])
    if due:
        cmd.extend(["--due", due])
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


def get_live_tasks_for_list(tasklist_id):
    if not os.path.exists(GTASKS_BIN) or not tasklist_id:
        return []
    try:
        res = subprocess.run([GTASKS_BIN, "list-tasks", tasklist_id, "--show-completed", "--json"], capture_output=True, text=True, check=True)
        if not res.stdout or not res.stdout.strip():
            return []
        data = json.loads(res.stdout)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error listing tasks for list {tasklist_id}: {e}")
        return []


def set_gtask_status(tasklist_id, task_id, completed=True):
    if not os.path.exists(GTASKS_BIN) or not tasklist_id or not task_id:
        return None
    try:
        if completed:
            res = subprocess.run([GTASKS_BIN, "complete-task", tasklist_id, task_id, "--json"], capture_output=True, text=True, check=True)
        else:
            res = subprocess.run([GTASKS_BIN, "update-task", tasklist_id, task_id, "--status", "needsAction", "--json"], capture_output=True, text=True, check=True)
        if res.stdout and res.stdout.strip():
            return json.loads(res.stdout)
        return None
    except Exception as e:
        print(f"Error updating task status: {e}")
        return None


def sync_all_google_tasks():
    user_data = get_user_data()
    try:
        all_lists = get_gtasks_lists()
        if not all_lists or not isinstance(all_lists, list):
            return user_data

        # Map list_id to dict of task_id -> live_task
        live_tasks_by_list = {}
        for l in all_lists:
            lid = l.get('id')
            if not lid:
                continue
            live_tasks = get_live_tasks_for_list(lid)
            if live_tasks and isinstance(live_tasks, list):
                live_tasks_by_list[lid] = {t['id']: t for t in live_tasks if isinstance(t, dict) and 'id' in t}
            else:
                live_tasks_by_list[lid] = {}

        changed = False
        for wid, ud in user_data.items():
            if 'google_tasks' in ud and isinstance(ud['google_tasks'], list):
                for t in ud['google_tasks']:
                    lid = t.get('tasklist_id')
                    tid = t.get('id')
                    if lid in live_tasks_by_list and tid in live_tasks_by_list[lid]:
                        live_t = live_tasks_by_list[lid][tid]
                        new_status = live_t.get('status', 'needsAction')
                        if t.get('status') != new_status:
                            t['status'] = new_status
                            changed = True
                        if live_t.get('title') and t.get('title') != live_t.get('title'):
                            t['title'] = live_t.get('title')
                            changed = True
                        if live_t.get('webViewLink') and t.get('webViewLink') != live_t.get('webViewLink'):
                            t['webViewLink'] = live_t.get('webViewLink')
                            changed = True

        if changed:
            save_user_data(user_data)
    except Exception as e:
        print(f"Error in sync_all_google_tasks: {e}")

    return user_data


def get_focus_ids():
    if os.path.exists(FOCUS_FILE):
        try:
            with open(FOCUS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_focus_ids(focus_set):
    os.makedirs(os.path.dirname(FOCUS_FILE), exist_ok=True)
    with open(FOCUS_FILE, "w") as f:
        json.dump(list(focus_set), f, indent=2)


def get_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_user_data(data):
    os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class CopilotHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        elif self.path == "/api/data":
            if not os.path.exists(DATA_FILE):
                from copilot_engine import enrich_portfolio_cache
                enrich_portfolio_cache()
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    user_data = get_user_data()
                    focus_ids = get_focus_ids()
                    manual_file = os.path.join(BASE_DIR, "fsr_manual_entries.json")
                    manual_entries = {}
                    if os.path.exists(manual_file):
                        try:
                            with open(manual_file, "r", encoding="utf-8") as mf:
                                manual_entries = json.load(mf)
                        except Exception:
                            pass

                    for w in data.get('fsr_workloads', []):
                        wid = w.get('workload_id')
                        wname = w.get('workload_name') or ''
                        w['is_focus'] = wid in focus_ids
                        ud = user_data.get(wid, {})
                        me = manual_entries.get(wid) or manual_entries.get(wname, {})
                        w['user_notes'] = ud.get('notes', '')
                        w['user_notes_updated_at'] = ud.get('notes_updated_at')
                        w['partner_tech_team'] = ud.get('partner_tech_team', '')
                        w['status_tecnico'] = ud.get('status_tecnico') or me.get('status_tecnico') or w.get('status_tecnico', '')
                        w['blocker'] = ud.get('blocker_tecnico') or me.get('blocker') or w.get('blocker', '')
                        w['blocker_tecnico'] = w['blocker']
                        w['partner_technical_email'] = (
                            ud.get('partner_technical_email')
                            or me.get('partner_tech_email')
                            or w.get('partner_technical_email', '')
                        )
                        raw_tw = ud.get('technical_win') if 'technical_win' in ud else (me.get('technical_win') if 'technical_win' in me else w.get('technical_win', False))
                        raw_ps = ud.get('proposal_sent') if 'proposal_sent' in ud else (me.get('proposal_sent') if 'proposal_sent' in me else w.get('proposal_sent', False))
                        w['technical_win'] = bool(raw_tw) if isinstance(raw_tw, bool) else str(raw_tw or '').strip().upper() in ('TRUE', '1', 'YES')
                        w['proposal_sent'] = bool(raw_ps) if isinstance(raw_ps, bool) else str(raw_ps or '').strip().upper() in ('TRUE', '1', 'YES')
                        w['execution_plan'] = ud.get('execution_plan', '')
                        w['attachments'] = ud.get('attachments', [])
                        w['google_tasks'] = ud.get('google_tasks', [])

                    data['workloads'] = data.get('fsr_workloads', [])
                    data['focus_workloads'] = list(focus_ids)
                    if 'generated_at' not in data:
                        data['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode('utf-8'))
                except Exception as e:
                    print(f"Error serving /api/data: {e}")
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Data cache not found"}).encode())
            return

        elif self.path == "/api/tasklists":
            lists = get_gtasks_lists()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(lists).encode('utf-8'))
            return

        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "port": PORT}).encode())
            return

        else:
            file_path = os.path.join(WEB_DIR, self.path.lstrip("/"))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                if file_path.endswith(".html"):
                    self.send_header("Content-Type", "text/html")
                elif file_path.endswith(".js"):
                    self.send_header("Content-Type", "application/javascript")
                elif file_path.endswith(".css"):
                    self.send_header("Content-Type", "text/css")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return

            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        payload = {}
        try:
            payload = json.loads(body.decode('utf-8'))
        except:
            pass

        if self.path == "/api/refresh":
            try:
                print(">>> Refresh requested via API: Running extract_copilot_data.py...")
                subprocess.run([sys.executable, os.path.join(BASE_DIR, "extract_copilot_data.py")], check=True)
                print(">>> Running copilot_engine.py...")
                subprocess.run([sys.executable, os.path.join(BASE_DIR, "copilot_engine.py")], check=True)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Cache refreshed"}).encode())
            except Exception as e:
                print(f"Refresh error: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/toggle-focus":
            wid = payload.get('workload_id')
            if not wid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id"}).encode())
                return

            focus_ids = get_focus_ids()
            if wid in focus_ids:
                focus_ids.remove(wid)
                is_now_focus = False
            else:
                focus_ids.add(wid)
                is_now_focus = True

            save_focus_ids(focus_ids)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "workload_id": wid,
                "is_focus": is_now_focus,
                "total_focus": len(focus_ids)
            }).encode())
            return

        elif self.path == "/api/save-note":
            wid = payload.get('workload_id')
            note_text = payload.get('notes', '')
            if not wid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id"}).encode())
                return

            user_data = get_user_data()
            if wid not in user_data:
                user_data[wid] = {"notes": "", "attachments": []}

            user_data[wid]['notes'] = note_text.strip()
            user_data[wid]['notes_updated_at'] = datetime.now().isoformat()
            save_user_data(user_data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "workload_id": wid,
                "notes": user_data[wid]['notes'],
                "notes_updated_at": user_data[wid]['notes_updated_at']
            }).encode())
            return

        elif self.path == "/api/save-tech-fields":
            wid = payload.get('workload_id')
            if not wid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id"}).encode())
                return

            user_data = get_user_data()
            if wid not in user_data:
                user_data[wid] = {"notes": "", "attachments": []}

            for field in ('partner_tech_team', 'status_tecnico', 'blocker_tecnico', 'execution_plan', 'notes'):
                if field in payload:
                    user_data[wid][field] = payload[field]

            user_data[wid]['updated_at'] = datetime.now().isoformat()
            save_user_data(user_data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "workload_id": wid,
                "data": user_data[wid]
            }).encode())
            return

        elif self.path == "/api/add-attachment":
            wid = payload.get('workload_id')
            title = payload.get('title', '').strip()
            url = payload.get('url', '').strip()

            if not wid or not url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id or url"}).encode())
                return

            if not title:
                title = "Drive Document"
                if "docs.google.com/spreadsheets" in url:
                    title = "Google Sheet"
                elif "docs.google.com/presentation" in url:
                    title = "Google Slide"
                elif "docs.google.com/document" in url:
                    title = "Google Doc"
                elif "drive.google.com" in url:
                    title = "Drive Folder / File"

            user_data = get_user_data()
            if wid not in user_data:
                user_data[wid] = {"notes": "", "attachments": []}

            att_id = f"att_{int(time.time() * 1000)}"
            new_att = {
                "id": att_id,
                "title": title,
                "url": url,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            user_data[wid].setdefault('attachments', []).append(new_att)
            save_user_data(user_data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "workload_id": wid,
                "attachment": new_att,
                "attachments": user_data[wid]['attachments']
            }).encode())
            return

        elif self.path == "/api/delete-attachment":
            wid = payload.get('workload_id')
            att_id = payload.get('attachment_id')

            if not wid or not att_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id or attachment_id"}).encode())
                return

            user_data = get_user_data()
            if wid in user_data and 'attachments' in user_data[wid]:
                user_data[wid]['attachments'] = [a for a in user_data[wid]['attachments'] if a.get('id') != att_id]
                save_user_data(user_data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "workload_id": wid,
                "attachments": user_data.get(wid, {}).get('attachments', [])
            }).encode())
            return

        elif self.path == "/api/create-google-task":
            wid = payload.get('workload_id')
            title = payload.get('title', '').strip()
            notes = payload.get('notes', '').strip()
            due = payload.get('due', '').strip()
            tasklist_id = payload.get('tasklist_id', '').strip()
            tasklist_name = payload.get('tasklist_name', '').strip()

            if not wid or not title:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id or title"}).encode())
                return

            all_lists = get_gtasks_lists()
            if not tasklist_id:
                if tasklist_name:
                    for l in all_lists:
                        if tasklist_name.lower() in l.get('title', '').lower():
                            tasklist_id = l.get('id')
                            break
                if not tasklist_id:
                    for l in all_lists:
                        if "pilon" in l.get('title', '').lower():
                            tasklist_id = l.get('id')
                            break
                if not tasklist_id and all_lists:
                    tasklist_id = all_lists[0].get('id')

            if not tasklist_id:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No Google Task list found"}).encode())
                return

            try:
                task_res = create_gtask(tasklist_id, title, notes=notes, due=due)
                user_data = get_user_data()
                if wid not in user_data:
                    user_data[wid] = {"notes": "", "attachments": []}

                user_data[wid].setdefault('google_tasks', []).append({
                    "id": task_res.get('id'),
                    "title": task_res.get('title'),
                    "notes": task_res.get('notes'),
                    "tasklist_id": tasklist_id,
                    "webViewLink": task_res.get('webViewLink'),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_user_data(user_data)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "task": task_res,
                    "tasks": user_data[wid]['google_tasks']
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/sync-tasks":
            try:
                user_data = sync_all_google_tasks()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Tasks synced with Google Tasks"
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/toggle-task-status":
            wid = payload.get('workload_id')
            tid = payload.get('task_id')
            lid = payload.get('tasklist_id')
            completed = payload.get('completed', True)

            if not wid or not tid or not lid:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing parameters"}).encode())
                return

            try:
                set_gtask_status(lid, tid, completed=completed)
                user_data = get_user_data()
                if wid in user_data and 'google_tasks' in user_data[wid]:
                    for t in user_data[wid]['google_tasks']:
                        if t.get('id') == tid:
                            t['status'] = 'completed' if completed else 'needsAction'
                    save_user_data(user_data)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "task_id": tid,
                    "completed": completed,
                    "tasks": user_data.get(wid, {}).get('google_tasks', [])
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/quick-create-task":
            wid = payload.get('workload_id')
            title = payload.get('title', '').strip()

            if not wid or not title:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing workload_id or title"}).encode())
                return

            w_info = None
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        cached_data = json.load(f)
                    for w in cached_data.get('fsr_workloads', []):
                        if w.get('workload_id') == wid:
                            w_info = w
                            break
                except:
                    pass

            all_lists = get_gtasks_lists()
            tasklist_id = None
            tasklist_name = "My Tasks"

            owner_name = (w_info.get('workload_owner_name') or '').lower() if w_info else ''
            for l in all_lists:
                ltitle = l.get('title', '')
                if owner_name and "pilon" in owner_name and "pilon" in ltitle.lower():
                    tasklist_id = l.get('id')
                    tasklist_name = ltitle
                    break
                elif owner_name and owner_name.split(' ')[0] in ltitle.lower():
                    tasklist_id = l.get('id')
                    tasklist_name = ltitle
                    break

            if not tasklist_id and all_lists:
                tasklist_id = all_lists[0].get('id')
                tasklist_name = all_lists[0].get('title', 'My Tasks')

            notes = ""
            due = ""
            if w_info:
                deal_arr = f"${round(w_info.get('annual_gross_revenue', 0)/1000)}k" if w_info.get('annual_gross_revenue') else "$0"
                notes = f"Customer: {w_info.get('account_name', 'N/A')}\nWorkload: {w_info.get('workload_name')}\nARR: {deal_arr}\nGo-Live: {w_info.get('production_date', 'TBD')}\nVector: {w_info.get('vector_url', '')}"
                if w_info.get('production_date'):
                    due = w_info.get('production_date')[:10] + "T00:00:00Z"

            try:
                task_res = create_gtask(tasklist_id, title, notes=notes, due=due)
                user_data = get_user_data()
                if wid not in user_data:
                    user_data[wid] = {"notes": "", "attachments": []}

                user_data[wid].setdefault('google_tasks', []).append({
                    "id": task_res.get('id'),
                    "title": task_res.get('title'),
                    "notes": task_res.get('notes'),
                    "status": task_res.get('status', 'needsAction'),
                    "tasklist_id": tasklist_id,
                    "tasklist_name": tasklist_name,
                    "webViewLink": task_res.get('webViewLink'),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_user_data(user_data)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "task": task_res,
                    "tasklist_name": tasklist_name,
                    "tasks": user_data[wid]['google_tasks']
                }).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/update-field":
            try:
                from copilot_agent import persist_workload_update
                field_name = payload.get("field")
                field_val = payload.get("value")
                blocker = payload.get("blocker")
                status_tecnico = payload.get("status_tecnico")
                partner_technical_email = payload.get("partner_technical_email")
                technical_win = payload.get("technical_win")
                proposal_sent = payload.get("proposal_sent")
                if field_name == "blocker":
                    blocker = field_val
                elif field_name == "status_tecnico":
                    status_tecnico = field_val
                elif field_name == "partner_technical_email":
                    partner_technical_email = field_val
                elif field_name == "technical_win":
                    technical_win = bool(field_val)
                elif field_name == "proposal_sent":
                    proposal_sent = bool(field_val)

                res = persist_workload_update(
                    workload_id=payload.get("workload_id"),
                    query_name=payload.get("workload_name"),
                    blocker=blocker,
                    status_tecnico=status_tecnico,
                    partner_technical_email=partner_technical_email,
                    technical_win=technical_win,
                    proposal_sent=proposal_sent
                )
                if res.get("status") == "success":
                    res["status"] = "ok"
                self.send_response(200 if res.get("status") == "ok" else 404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/chat":
            try:
                from copilot_agent import run_agent_chat
                res = run_agent_chat(
                    user_message=payload.get("message", ""),
                    selected_workload_id=payload.get("selected_workload_id"),
                    active_filters=payload.get("active_filters") or payload.get("filters")
                )
                updated_w = [
                    a["result"] for a in res.get("tool_actions", [])
                    if a.get("tool") == "update_workload_tracking" and a.get("result", {}).get("status") == "success"
                ]
                res["updated_workloads"] = updated_w
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/draft-nudge":
            try:
                from copilot_agent import load_portfolio, tool_draft_stakeholder_nudge
                pdata = load_portfolio()
                draft = tool_draft_stakeholder_nudge(payload, pdata.get("fsr_workloads", []))
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(draft).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        elif self.path == "/api/sync-sheets":
            try:
                from sync_engine import sync_bidirectional
                fsr_filter = payload.get("fsr")
                sync_res = sync_bidirectional(fsr_filter=fsr_filter)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(sync_res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self.send_response(404)
        self.end_headers()


def run_server():
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(server_address, CopilotHandler)
    print(f"==================================================================")
    print(f"🚀 Partner Velocity Copilot Web Server is LIVE on port {PORT}")
    print(f"📍 Local URL:  http://localhost:{PORT}")
    print(f"==================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
