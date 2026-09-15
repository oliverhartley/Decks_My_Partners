import subprocess
import requests
import json
import time
import os
import csv
from datetime import datetime

GSHEETS = "/google/bin/releases/gemini-agents-gsheets/gsheets"
SCRATCH_DIR = "/usr/local/google/home/oliverhartley/.gemini/jetski/brain/2bfcc778-f455-4d27-b2a0-31818d893ed4/scratch"
os.makedirs(SCRATCH_DIR, exist_ok=True)

def get_oauth_token():
    for _ in range(3):
        try:
            raw = subprocess.check_output([
                'stubby', 'call', 'blade:sso', 'corplogin.CorpLogin.Exchange',
                'target: { scope: GAIA_USER name: "oliverhartley@google.com" } target_credential { type: OAUTH2_TOKEN oauth2_attributes { scope: "https://www.googleapis.com/auth/cloud-platform" } }'
            ], stderr=subprocess.DEVNULL).decode('utf-8')
            return [line for line in raw.split('\n') if 'oauth2_token' in line][0].split('"')[1]
        except Exception:
            time.sleep(1)
    raise RuntimeError("Failed to get oauth token")

token = get_oauth_token()
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

def run_query(query):
    payload = {'query': query, 'useLegacySql': False, 'timeoutMs': 60000}
    resp = requests.post('https://bigquery.googleapis.com/bigquery/v2/projects/concord-prod/queries', headers=headers, json=payload)
    data = resp.json()
    job_id = data.get('jobReference', {}).get('jobId')
    while not data.get('jobComplete', True):
        time.sleep(2)
        resp = requests.get(f"https://bigquery.googleapis.com/bigquery/v2/projects/concord-prod/queries/{job_id}", headers=headers)
        data = resp.json()
    return data

PARTNERS_CONFIG = [
    {
        "partner": "Comercializadora Zenta Group SPA",
        "ssid": "1x7niHKVtF4dVrRjAO9nQF4KmRWuZAZGCysw7qGK2tMw",
        "pids": ['0014M00001h39BLQAY', '0014M00001h38bbQAA', '0014M00001m9woLQAQ', '001Kf000012gqs3IAA', '001Kf00001I81snIAB', '001Kf00001I81tHIAR', '0014M00001yRzvDQAS'],
    },
    {
        "partner": "Tech Pulse SPA (Axmos)",
        "ssid": "1_t_MvhhESxjr-h1MTdMkDkYPu_V0-435ndRdbXdeHTM",
        "pids": ['0014M00002JmizDQAR', '001Kf00001G4DmBIAV', '001Kf0000149iw9IAA'],
    },
    {
        "partner": "Devaid SPA",
        "ssid": "1eKkgjuW--5zo2ad2CPCRZDHEJpZ19EkPHVaEYvU6eOE",
        "pids": ['0014M00001h38aiQAA', '0014M00001m9sVvQAI'],
    },
    {
        "partner": "MadeinWeb S/A",
        "ssid": "1qZKrT1KSwA6GX-UzJs7Wv782RZKSjuuky4xj-iyUMbw",
        "pids": ['0014M00002GGNRCQA5', '001Kf000013hWaOIAU', '0014M00001h336WQAQ'],
    }
]

def get_existing_sheets(ssid):
    res = subprocess.run([GSHEETS, "readonly", "list-sheets", ssid, "--json"], capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        try:
            return json.loads(res.stdout)
        except Exception:
            pass
    return []

def ensure_tab(ssid, tab_title):
    sheets = get_existing_sheets(ssid)
    for s in sheets:
        if s.get("title") == tab_title:
            return s.get("id")
    res = subprocess.run([GSHEETS, "mutate", "add-sheet", ssid, "--title", tab_title], capture_output=True, text=True)
    sheets = get_existing_sheets(ssid)
    for s in sheets:
        if s.get("title") == tab_title:
            return s.get("id")
    return None

def format_open_cases_tab(ssid, sid, num_rows, p1_cnt, p2_cnt, p3_cnt, p4_cnt):
    num_cols = 12
    batch_req = {"requests": []}

    # 1. Base format: Roboto 10, vertical align middle, wrap CLIP
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 0,
                "endRowIndex": num_rows,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "fontFamily": "Roboto",
                        "fontSize": 10,
                        "foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}
                    },
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "CLIP"
                }
            },
            "fields": "userEnteredFormat(textFormat(fontFamily,fontSize,foregroundColor),verticalAlignment,wrapStrategy)"
        }
    })

    # 2. Row 0: Top Title Banner
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.082, "green": 0.341, "blue": 0.690}, # #1557B0
                    "textFormat": {
                        "fontFamily": "Google Sans",
                        "fontSize": 12,
                        "bold": True,
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                    },
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    # 3. Row 1: Subtitle Banner
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 1,
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.910, "green": 0.941, "blue": 0.996}, # #E8F0FE
                    "textFormat": {
                        "fontFamily": "Roboto",
                        "fontSize": 9,
                        "italic": True,
                        "foregroundColor": {"red": 0.090, "green": 0.306, "blue": 0.651}
                    },
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    # 4. Row 2: KPI / Legend Banner
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 2,
                "endRowIndex": 3,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.973, "green": 0.976, "blue": 0.980}, # #F8F9FA
                    "textFormat": {
                        "fontFamily": "Google Sans",
                        "fontSize": 10,
                        "bold": True,
                        "foregroundColor": {"red": 0.125, "green": 0.129, "blue": 0.141}
                    },
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    # 5. Row 3: Table Column Headers
    batch_req["requests"].append({
        "repeatCell": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 3,
                "endRowIndex": 4,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.082, "green": 0.341, "blue": 0.690},
                    "textFormat": {
                        "fontFamily": "Google Sans",
                        "fontSize": 10,
                        "bold": True,
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)"
        }
    })

    # 6. Data Rows
    data_start = 4
    data_end = num_rows

    for r in range(data_start, data_end):
        is_even = (r % 2 == 0)
        bg = {"red": 1.0, "green": 1.0, "blue": 1.0} if is_even else {"red": 0.973, "green": 0.976, "blue": 0.980}
        batch_req["requests"].append({
            "repeatCell": {
                "range": {
                    "sheetId": sid,
                    "startRowIndex": r,
                    "endRowIndex": r + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": bg
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        })

    # Specific Column Alignments
    # Col A (0): Case Number -> Center, Bold, Link Blue
    batch_req["requests"].append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 0, "endColumnIndex": 1},
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                    "textFormat": {
                        "foregroundColor": {"red": 0.067, "green": 0.333, "blue": 0.8}, # #1155cc
                        "bold": True,
                        "underline": True
                    }
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment,textFormat)"
        }
    })

    # Col B (1): Priority -> Center, Bold
    batch_req["requests"].append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 1, "endColumnIndex": 2},
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment,textFormat)"
        }
    })

    # Col E (4): Product Line -> Center
    batch_req["requests"].append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 4, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat.horizontalAlignment"
        }
    })

    # Col H (7): Created Date -> Center
    batch_req["requests"].append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 7, "endColumnIndex": 8},
            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat.horizontalAlignment"
        }
    })

    # Col I (8): Days Open -> Center, Bold
    batch_req["requests"].append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 8, "endColumnIndex": 9},
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                    "textFormat": {"bold": True},
                    "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                }
            },
            "fields": "userEnteredFormat(horizontalAlignment,textFormat,numberFormat)"
        }
    })

    # Col J (9): Support Level -> Center
    batch_req["requests"].append({
        "repeatCell": {
            "range": {"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 9, "endColumnIndex": 10},
            "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
            "fields": "userEnteredFormat.horizontalAlignment"
        }
    })

    # Grid borders
    batch_req["requests"].append({
        "updateBorders": {
            "range": {
                "sheetId": sid,
                "startRowIndex": 3,
                "endRowIndex": data_end,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols
            },
            "top": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "left": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "right": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0.9, "green": 0.9, "blue": 0.9}},
            "innerVertical": {"style": "SOLID", "width": 1, "color": {"red": 0.9, "green": 0.9, "blue": 0.9}}
        }
    })

    # Conditional Formatting for Priority (Col B)
    # Clear existing conditional formats on this sheet first
    batch_req["requests"].append({
        "clearBasicFilter": {"sheetId": sid}
    })

    # P1: Soft Red
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 1, "endColumnIndex": 2}],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "P1"}]},
                    "format": {
                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902}, # #FCE8E6
                        "textFormat": {"foregroundColor": {"red": 0.773, "green": 0.133, "blue": 0.122}, "bold": True} # #C5221F
                    }
                }
            },
            "index": 0
        }
    })

    # P2: Soft Orange
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 1, "endColumnIndex": 2}],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "P2"}]},
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.878, "blue": 0.698}, # #FFE0B2
                        "textFormat": {"foregroundColor": {"red": 0.690, "green": 0.376, "blue": 0.0}, "bold": True} # #B06000
                    }
                }
            },
            "index": 1
        }
    })

    # P3: Soft Yellow
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 1, "endColumnIndex": 2}],
                "booleanRule": {
                    "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "P3"}]},
                    "format": {
                        "backgroundColor": {"red": 1.0, "green": 0.976, "blue": 0.859}, # #FFF9DB
                        "textFormat": {"foregroundColor": {"red": 0.620, "green": 0.467, "blue": 0.0}, "bold": True}
                    }
                }
            },
            "index": 2
        }
    })

    # Days Open > 30 days: highlight in Col I
    batch_req["requests"].append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{"sheetId": sid, "startRowIndex": data_start, "endRowIndex": data_end, "startColumnIndex": 8, "endColumnIndex": 9}],
                "booleanRule": {
                    "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "30"}]},
                    "format": {
                        "backgroundColor": {"red": 0.988, "green": 0.910, "blue": 0.902},
                        "textFormat": {"foregroundColor": {"red": 0.773, "green": 0.133, "blue": 0.122}, "bold": True}
                    }
                }
            },
            "index": 3
        }
    })

    # Freeze Top 4 rows
    batch_req["requests"].append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sid,
                "gridProperties": {
                    "frozenRowCount": 4
                }
            },
            "fields": "gridProperties.frozenRowCount"
        }
    })

    # Set explicit column dimensions
    col_widths = [140, 90, 200, 240, 140, 200, 420, 120, 110, 130, 160, 240]
    for ci, w in enumerate(col_widths):
        batch_req["requests"].append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sid,
                    "dimension": "COLUMNS",
                    "startIndex": ci,
                    "endIndex": ci + 1
                },
                "properties": {
                    "pixelSize": w
                },
                "fields": "pixelSize"
            }
        })

    # Self-copy paste to activate hyperlinks on Col A
    if data_end > data_start:
        batch_req["requests"].append({
            "copyPaste": {
                "source": {
                    "sheetId": sid,
                    "startRowIndex": data_start,
                    "endRowIndex": data_end,
                    "startColumnIndex": 0,
                    "endColumnIndex": 1
                },
                "destination": {
                    "sheetId": sid,
                    "startRowIndex": data_start,
                    "endRowIndex": data_end,
                    "startColumnIndex": 0,
                    "endColumnIndex": 1
                },
                "pasteType": "PASTE_NORMAL"
            }
        })

    tmp_batch = f"/tmp/batch_open_cases_{sid}_{int(time.time()*1000)}.json"
    with open(tmp_batch, "w") as f:
        json.dump(batch_req, f)
    
    success = False
    for attempt in range(5):
        res_b = subprocess.run([GSHEETS, "mutate", "raw-batch", ssid, "-f", tmp_batch], capture_output=True, text=True)
        if res_b.returncode == 0:
            success = True
            break
        elif "429" in res_b.stderr or "Quota exceeded" in res_b.stderr or "RATE_LIMIT_EXCEEDED" in res_b.stderr:
            wait_time = (attempt + 1) * 6
            print(f"    Rate limit hit on raw-batch. Retrying in {wait_time}s (attempt {attempt+1}/5)...")
            time.sleep(wait_time)
        else:
            print(f"    Batch formatting error: {res_b.stderr}")
            break

    if not success:
        print(f"    Failed to format sheet {sid} after retries.")
    if os.path.exists(tmp_batch):
        os.remove(tmp_batch)

def process_partner(cfg):
    partner_name = cfg["partner"]
    ssid = cfg["ssid"]
    print(f"\n==================================================================")
    print(f"Processing: {partner_name} (SSID: {ssid})")
    print(f"==================================================================")

    pids_str = str(cfg['pids'])
    q_c = f"""
    SELECT DISTINCT sfdc_account_id
    FROM `concord-prod.service_cloudbi.workloads`
    WHERE workload_details.partner_id IN UNNEST({pids_str})
      AND sfdc_account_id IS NOT NULL
      AND sfdc_account_id NOT IN UNNEST({pids_str})
    """
    res_c = run_query(q_c)
    cids = [r['f'][0]['v'] for r in res_c.get('rows', [])]
    all_ids = cfg['pids'] + cids
    all_ids_str = str(all_ids)
    print(f"  Identified {len(cids)} client accounts in workloads.")

    q_cases = f"""
    SELECT
      case_number,
      priority,
      case_status,
      COALESCE(customer.name, 'N/A') as customer_name,
      COALESCE(product_line, 'Other') as product_line,
      COALESCE(product, 'Unknown') as product,
      COALESCE(case_subject, 'Sin Asunto') as case_subject,
      CAST(DATE(created.timestamp) AS STRING) as created_date,
      DATE_DIFF(CURRENT_DATE(), DATE(created.timestamp), DAY) as days_open,
      COALESCE(service_level_info.unified_service_level, 'Basic') as support_level,
      COALESCE(case_owner.ldap, 'Unassigned') as owner_ldap,
      COALESCE(customer.submitter_email, 'N/A') as submitter_email
    FROM `concord-prod.service_customerexperience_support.case_detail`
    WHERE (timeliness.is_closed IS FALSE OR timeliness.is_closed IS NULL)
      AND case_status != 'Closed'
      AND (
        customer.vector.sales.account_id IN UNNEST({all_ids_str})
        OR customer.vector.reporting.account_id IN UNNEST({all_ids_str})
      )
    ORDER BY
      CASE priority
        WHEN 'P1' THEN 1
        WHEN 'P2' THEN 2
        WHEN 'P3' THEN 3
        WHEN 'P4' THEN 4
        ELSE 5
      END ASC,
      days_open DESC
    """
    res_cases = run_query(q_cases)
    case_rows = res_cases.get('rows', [])
    tot_cases = len(case_rows)

    p1_cnt = 0
    p2_cnt = 0
    p3_cnt = 0
    p4_cnt = 0
    gt_15_cnt = 0

    for r in case_rows:
        p = r['f'][1]['v']
        days = int(r['f'][8]['v']) if r['f'][8]['v'] is not None else 0
        if p == 'P1': p1_cnt += 1
        elif p == 'P2': p2_cnt += 1
        elif p == 'P3': p3_cnt += 1
        elif p == 'P4': p4_cnt += 1
        if days > 15: gt_15_cnt += 1

    print(f"  Found {tot_cases} open cases (P1: {p1_cnt}, P2: {p2_cnt}, P3: {p3_cnt}, P4: {p4_cnt}, >15d: {gt_15_cnt}).")

    target_tab = "Casos_de_Soporte_Abierto"
    sid = ensure_tab(ssid, target_tab)
    subprocess.run([GSHEETS, "mutate", "clear", ssid, f"'{target_tab}'!A1:Z2000"], capture_output=True)
    subprocess.run([GSHEETS, "mutate", "delete-rows", ssid, "--range", f"'{target_tab}'!2:2000"], capture_output=True)

    today_str = datetime.now().strftime("%d - %b %Y")
    t_rows = []
    # Row 0: Title
    t_rows.append([f"MONITOREO DE CASOS DE SOPORTE ABIERTOS (OPEN CASES) - {partner_name.upper()}", "", "", "", "", "", "", "", "", "", "", ""])
    # Row 1: Subtitle
    t_rows.append([f"Partner: {partner_name} | Total Casos Abiertos: {tot_cases} | Fuente: Concord (case_detail) | PE: Oliver Hartley | Fecha: {today_str}", "", "", "", "", "", "", "", "", "", "", ""])
    # Row 2: KPI / Legend
    t_rows.append([f"🔴 P1 Urgente: {p1_cnt}   |   🟠 P2 Alta: {p2_cnt}   |   🟡 P3 Media: {p3_cnt}   |   ⚪ P4 Baja: {p4_cnt}   |   ⏱️ Casos >15 días abierto: {gt_15_cnt}", "", "", "", "", "", "", "", "", "", "", ""])
    # Row 3: Headers
    t_rows.append([
        "Número de Caso",
        "Prioridad",
        "Estado del Caso",
        "Cuenta / Cliente",
        "Línea de Producto",
        "Producto",
        "Asunto / Resumen del Caso",
        "Fecha Apertura",
        "Días Abierto",
        "Nivel de Soporte",
        "TSE Owner (Google)",
        "Solicitante (Email)"
    ])

    if tot_cases == 0:
        t_rows.append(["No hay casos de soporte abiertos actualmente para las cuentas de este partner.", "", "", "", "", "", "", "", "", "", "", ""])
    else:
        for r in case_rows:
            c_num = r['f'][0]['v']
            prio = r['f'][1]['v']
            status = r['f'][2]['v']
            c_name = r['f'][3]['v']
            pline = r['f'][4]['v']
            prod = r['f'][5]['v']
            subj = r['f'][6]['v']
            c_date = r['f'][7]['v']
            days = int(r['f'][8]['v']) if r['f'][8]['v'] is not None else 0
            s_level = r['f'][9]['v']
            owner = r['f'][10]['v']
            submitter = r['f'][11]['v']

            link_formula = f'=HYPERLINK("https://cases.corp.google.com/case/{c_num}", "#{c_num}")'
            t_rows.append([
                link_formula,
                prio,
                status,
                c_name,
                pline,
                prod,
                subj,
                c_date,
                days,
                s_level,
                owner,
                submitter
            ])

    safe_name = partner_name.replace(" ", "_").replace("(", "_").replace(")", "_").replace("/", "_")
    csv_path = os.path.join(SCRATCH_DIR, f"{safe_name}_casos_soporte_abierto.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(t_rows)

    subprocess.run([GSHEETS, "mutate", "import-csv", ssid, csv_path, "--sheet", target_tab], capture_output=True)
    format_open_cases_tab(ssid, sid, len(t_rows), p1_cnt, p2_cnt, p3_cnt, p4_cnt)
    print(f"  Created & formatted '{target_tab}' with {len(t_rows)} rows successfully.")

if __name__ == "__main__":
    for i, cfg in enumerate(PARTNERS_CONFIG):
        if i > 0:
            time.sleep(4)
        process_partner(cfg)
    print("\nAll 4 partner spreadsheets successfully updated with 'Casos_de_Soporte_Abierto'!")
