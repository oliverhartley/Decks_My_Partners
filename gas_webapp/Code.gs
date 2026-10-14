/**
 * Code.gs
 * Google Apps Script Backend for the Agentic Workload Command Center
 * Shared between Oliver Hartley (oliverhartley@google.com) & Luna Longo (lunalongo@google.com)
 *
 * Powers:
 * - doGet(e): Serves the full Agentic Workload Command Center UI
 * - apiGetData(): Loads enriched 6-FSR portfolio (513 workloads) + latest manual overrides from Drive
 * - apiUpdateField(payload): Persists inline edits to Drive JSON caches AND writes through directly to the FSR's Google Sheet
 * - apiSyncSheets(payload): Full bidirectional reconciliation across all 6 Brazil FSR Google Sheets
 * - apiDraftNudge(payload): Context-aware Portuguese stakeholder follow-up email drafter
 * - apiChat(payload): Portfolio Copilot query, partner matchmaker & inline field updater
 */

const PORTFOLIO_DRIVE_FILE_ID = '1cm_QlMMNbnqv0zeyD3HfmRO1xGZxvYBX';
const MANUAL_ENTRIES_DRIVE_FILE_ID = '1CnhVKamb5IWUQ6uFxnNDHFSBaM4unvOG';

const FSR_SHEET_CONFIGS = [
  { username: 'fpilon', name: 'Felipe Pilon', pdm: 'Oliver Hartley', ssid: '1gS9JWRb-aReMKOiJzhlKEu0TFTb4fF8fNROcTKWf7jU' },
  { username: 'robertacoelho', name: 'Roberta Coelho', pdm: 'Oliver Hartley', ssid: '1wBiY2bqGo-NJaVeET6g8GRKfOTMDkQaSUhbD5xPfb5M' },
  { username: 'vmmoyses', name: 'Vanessa Moyses', pdm: 'Oliver Hartley', ssid: '1UXbDWQNf1_wvm6_WHtKX2QIWXzRgib_xMpMGfnu5nKg' },
  { username: 'dbenevides', name: 'Daniela Benevides', pdm: 'Luna Longo', ssid: '1PlnciU1NuNuo7SL0Jxb-X3HWksLzRXpYOVFk8UqmdAI' },
  { username: 'dprudencio', name: 'Daniel Prudencio', pdm: 'Luna Longo', ssid: '1qOUzmqu0vrZ7a19oSDR8KZTuDAfbdkJLiCDMoql9iqM' },
  { username: 'tobiassarah', name: 'Sarah Tobias', pdm: 'Luna Longo', ssid: '1eB2g5osFTKxH0i9B7AoddQO-MJ_qnewu3nwIozquTIs' },
  { username: 'anagama', name: 'Ana Luiza Gama', pdm: 'Oliver Hartley', ssid: '1VMLeUmBjnucCwW98Z4ElVdusQSOhQgIrWrKlQOGeZdA' },
  { username: 'renanvaladares', name: 'Renan Valadares', pdm: 'Luna Longo', ssid: '1YmVIhMxpaQpCV4DHP-cN3g4AFt5d2jCDHpQZaeF_soU' }
];

const FIELD_SPECS = [
  { key: 'blocker', webKey: 'blocker', colIdx: 10, header: 'Cual es el bloqueo?', isBool: false },
  { key: 'status_tecnico', webKey: 'status_tecnico', colIdx: 11, header: 'Status Tecnico', isBool: false },
  { key: 'partner_tech_email', webKey: 'partner_technical_email', colIdx: 17, header: 'Partner Technical Owner Email', isBool: false },
  { key: 'technical_win', webKey: 'technical_win', colIdx: 18, header: 'Technical win', isBool: true },
  { key: 'proposal_sent', webKey: 'proposal_sent', colIdx: 19, header: 'Propousal sent to client', isBool: true }
];

/**
 * Entry point for Google Apps Script Web App
 * Injects initial portfolio JSON directly into the HTML payload for 0ms instant rendering
 */
function doGet(e) {
  let html = HtmlService.createHtmlOutputFromFile('index').getContent();
  try {
    const initialPayload = buildPortfolioPayload_();
    const safeJson = JSON.stringify(initialPayload).replace(/<\/script/gi, '<\\/script');
    const bootstrapScript = '<script>window.__INITIAL_PORTFOLIO_DATA__ = ' + safeJson + ';</script>\n</head>';
    html = html.replace('</head>', bootstrapScript);
  } catch (err) {
    console.error('Error injecting initial portfolio payload in doGet: ' + err);
  }
  return HtmlService.createHtmlOutput(html)
    .setTitle('Agentic Workload Command Center · Brazil Partner Ecosystem')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0');
}

/**
 * Helper: Safely read JSON file from Google Drive
 */
function readDriveJson_(fileId, defaultVal) {
  try {
    const file = DriveApp.getFileById(fileId);
    const content = file.getBlob().getDataAsString('UTF-8');
    return JSON.parse(content);
  } catch (err) {
    console.error('Error reading Drive JSON ' + fileId + ': ' + err);
    return defaultVal;
  }
}

/**
 * Helper: Safely overwrite JSON file on Google Drive (compact serialization)
 */
function writeDriveJson_(fileId, dataObj) {
  try {
    const file = DriveApp.getFileById(fileId);
    file.setContent(JSON.stringify(dataObj));
    return true;
  } catch (err) {
    console.error('Error writing Drive JSON ' + fileId + ': ' + err);
    return false;
  }
}

/**
 * Helper: Normalize boolean or string values
 */
function normVal_(val, isBool) {
  if (isBool) {
    if (typeof val === 'boolean') return val;
    const s = String(val || '').trim().toUpperCase();
    return s === 'TRUE' || s === '1' || s === 'YES';
  }
  return String(val === null || val === undefined ? '' : val).trim();
}

/**
 * Helper: Extract plain text label from =HYPERLINK("url", "label")
 */
function extractHyperlinkLabel_(formulaOrVal) {
  if (!formulaOrVal) return '';
  const s = String(formulaOrVal).trim();
  const m = s.match(/^=HYPERLINK\("[^"]*",\s*"(.*)"\)$/i);
  if (m) {
    return m[1].replace(/""/g, '"').trim();
  }
  return s;
}

function extractWorkloadIdFromFormula_(formulaOrVal) {
  if (!formulaOrVal) return '';
  const s = String(formulaOrVal).trim();
  const m = s.match(/\/Workload__c\/([a-zA-Z0-9]+)\/view/i);
  return m ? m[1].trim() : '';
}

/**
 * Internal helper: Builds the merged & slimmed portfolio payload object
 */
function buildPortfolioPayload_() {
  const data = readDriveJson_(PORTFOLIO_DRIVE_FILE_ID, { fsr_workloads: [] });
  const manualEntries = readDriveJson_(MANUAL_ENTRIES_DRIVE_FILE_ID, {});
  let activeEmail = '';
  try {
    activeEmail = Session.getActiveUser().getEmail() || '';
  } catch (e) {}

  const workloads = data.fsr_workloads || data.workloads || [];
  for (let i = 0; i < workloads.length; i++) {
    const w = workloads[i];
    const wid = w.workload_id || '';
    const wname = w.workload_name || '';
    const me = (wid && manualEntries[wid]) ? manualEntries[wid] : (manualEntries[wname] || {});

    if (me.blocker !== undefined) {
      w.blocker = me.blocker;
      w.blocker_tecnico = me.blocker;
    }
    if (me.status_tecnico !== undefined) {
      w.status_tecnico = me.status_tecnico;
    }
    if (me.partner_tech_email !== undefined && me.partner_tech_email !== '') {
      w.partner_technical_email = me.partner_tech_email;
    }
    if (me.technical_win !== undefined) {
      w.technical_win = normVal_(me.technical_win, true);
    } else {
      w.technical_win = normVal_(w.technical_win, true);
    }
    if (me.proposal_sent !== undefined) {
      w.proposal_sent = normVal_(me.proposal_sent, true);
    } else {
      w.proposal_sent = normVal_(w.proposal_sent, true);
    }

    // Ensure bulky legacy fields are stripped if present
    delete w.next_steps_history;
    delete w.vector_recent_cases;
    delete w.diagnosis;
    delete w.opportunity_partners;
  }

  const genAt = data.generated_at || Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyy-MM-dd HH:mm');
  return {
    generated_at: genAt,
    current_user_email: activeEmail,
    workloads: workloads
  };
}

/**
 * GET /api/data equivalent for Apps Script
 * Returns compact JSON string to avoid google.script.run object size cap
 */
function apiGetData() {
  return JSON.stringify(buildPortfolioPayload_());
}

/**
 * Writes a single workload's updated fields directly to its FSR Google Sheet
 */
function writeSingleWorkloadToSheet_(fsrUsername, workloadId, workloadName, updatedFields) {
  const cfg = FSR_SHEET_CONFIGS.find(c => c.username === fsrUsername);
  if (!cfg || (!workloadId && !workloadName)) return false;

  try {
    const ss = SpreadsheetApp.openById(cfg.ssid);
    const sheet = ss.getSheetByName('Follow_up');
    if (!sheet) return false;

    const lastRow = Math.min(sheet.getLastRow(), 300);
    if (lastRow < 6) return false;

    const headerRow = sheet.getRange(5, 1, 1, 20).getValues()[0].map(h => String(h || '').trim());
    const colMap = {};
    headerRow.forEach((h, idx) => { colMap[h] = idx; });

    const numDataRows = lastRow - 5;
    const colCValues = sheet.getRange(6, 3, numDataRows, 1).getValues();
    const colCFormulas = sheet.getRange(6, 3, numDataRows, 1).getFormulas();

    let targetSheetRow = -1; // 1-based row number
    for (let r = 0; r < numDataRows; r++) {
      const fStr = colCFormulas[r][0] || '';
      const rowWid = extractWorkloadIdFromFormula_(fStr);
      if (workloadId && rowWid && rowWid === String(workloadId)) {
        targetSheetRow = 6 + r;
        break;
      }
      const label = extractHyperlinkLabel_(fStr || colCValues[r][0]);
      if (!rowWid && label === workloadName) {
        targetSheetRow = 6 + r;
        break;
      }
    }

    if (targetSheetRow === -1) return false;

    FIELD_SPECS.forEach(spec => {
      if (updatedFields[spec.key] !== undefined) {
        let cIdx = colMap[spec.header] !== undefined ? colMap[spec.header] : spec.colIdx;
        if (spec.key === 'proposal_sent' && colMap[spec.header] === undefined && colMap['Proposal sent to client'] !== undefined) {
          cIdx = colMap['Proposal sent to client'];
        }
        const cell = sheet.getRange(targetSheetRow, cIdx + 1);
        const val = normVal_(updatedFields[spec.key], spec.isBool);
        cell.setValue(val);
      }
    });
    SpreadsheetApp.flush();
    return true;
  } catch (err) {
    console.error('Error writing single workload to sheet (' + fsrUsername + '): ' + err);
    return false;
  }
}

/**
 * POST /api/update-field equivalent for Apps Script
 */
function apiUpdateField(payload) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    const workloadId = payload.workload_id;
    const queryName = payload.workload_name;
    const fieldName = payload.field;
    const fieldVal = payload.value;

    let blocker = payload.blocker;
    let statusTecnico = payload.status_tecnico;
    let partnerTechEmail = payload.partner_technical_email;
    let technicalWin = payload.technical_win;
    let proposalSent = payload.proposal_sent;

    if (fieldName === 'blocker') blocker = fieldVal;
    else if (fieldName === 'status_tecnico') statusTecnico = fieldVal;
    else if (fieldName === 'partner_technical_email') partnerTechEmail = fieldVal;
    else if (fieldName === 'technical_win') technicalWin = normVal_(fieldVal, true);
    else if (fieldName === 'proposal_sent') proposalSent = normVal_(fieldVal, true);

    const data = readDriveJson_(PORTFOLIO_DRIVE_FILE_ID, { fsr_workloads: [] });
    const workloads = data.fsr_workloads || data.workloads || [];
    let target = null;

    for (let i = 0; i < workloads.length; i++) {
      if (workloadId && String(workloads[i].workload_id) === String(workloadId)) {
        target = workloads[i];
        break;
      }
    }
    if (!target && queryName) {
      const q = String(queryName).toLowerCase().trim();
      for (let i = 0; i < workloads.length; i++) {
        const wn = String(workloads[i].workload_name || '').toLowerCase();
        const an = String(workloads[i].account_name || '').toLowerCase();
        if (wn.indexOf(q) !== -1 || an.indexOf(q) !== -1) {
          target = workloads[i];
          break;
        }
      }
    }

    if (!target) {
      return { status: 'error', message: 'Workload not found' };
    }

    const wid = target.workload_id || '';
    const wname = target.workload_name;
    const fsrUser = target.workload_owner_username || target.fsr_ldap;
    const nowIso = new Date().toISOString();

    const manualEntries = readDriveJson_(MANUAL_ENTRIES_DRIVE_FILE_ID, {});
    const entry = Object.assign({}, manualEntries[wid] || manualEntries[wname] || {});
    const updatedForSheet = {};

    if (blocker !== undefined && blocker !== null) {
      entry.blocker = String(blocker).trim();
      target.blocker = entry.blocker;
      target.blocker_tecnico = entry.blocker;
      updatedForSheet.blocker = entry.blocker;
    }
    if (statusTecnico !== undefined && statusTecnico !== null) {
      entry.status_tecnico = String(statusTecnico).trim();
      target.status_tecnico = entry.status_tecnico;
      updatedForSheet.status_tecnico = entry.status_tecnico;
    }
    if (partnerTechEmail !== undefined && partnerTechEmail !== null) {
      entry.partner_tech_email = String(partnerTechEmail).trim();
      target.partner_technical_email = entry.partner_tech_email;
      updatedForSheet.partner_tech_email = entry.partner_tech_email;
    }
    if (technicalWin !== undefined && technicalWin !== null) {
      entry.technical_win = normVal_(technicalWin, true);
      target.technical_win = entry.technical_win;
      updatedForSheet.technical_win = entry.technical_win;
    }
    if (proposalSent !== undefined && proposalSent !== null) {
      entry.proposal_sent = normVal_(proposalSent, true);
      target.proposal_sent = entry.proposal_sent;
      updatedForSheet.proposal_sent = entry.proposal_sent;
    }

    entry.updated_at = nowIso;
    if (wid) manualEntries[wid] = entry;
    manualEntries[wname] = entry;

    // 1. Write directly to the FSR's Google Sheet
    const wroteSheet = writeSingleWorkloadToSheet_(fsrUser, wid, wname, updatedForSheet);
    if (!wroteSheet) {
      entry.pending_web_edits = Object.assign(entry.pending_web_edits || {}, updatedForSheet);
    }

    // 2. Persist both Drive JSON files so both Web Apps & Cloudtop stay in sync
    writeDriveJson_(MANUAL_ENTRIES_DRIVE_FILE_ID, manualEntries);
    writeDriveJson_(PORTFOLIO_DRIVE_FILE_ID, data);

    return {
      status: 'ok',
      workload_id: target.workload_id,
      workload_name: wname,
      account_name: target.account_name,
      blocker: target.blocker || '',
      status_tecnico: target.status_tecnico || '',
      partner_technical_email: target.partner_technical_email || '',
      technical_win: Boolean(target.technical_win),
      proposal_sent: Boolean(target.proposal_sent),
      updated_at: nowIso
    };
  } finally {
    lock.releaseLock();
  }
}

/**
 * POST /api/sync-sheets & /api/refresh equivalent for Apps Script
 * Performs bidirectional reconciliation across all 6 FSR Google Sheets and updates Drive JSON cache
 */
function apiSyncSheets(payload) {
  const lock = LockService.getScriptLock();
  lock.waitLock(25000);
  try {
    const data = readDriveJson_(PORTFOLIO_DRIVE_FILE_ID, { fsr_workloads: [] });
    const workloads = data.fsr_workloads || data.workloads || [];
    const manualEntries = readDriveJson_(MANUAL_ENTRIES_DRIVE_FILE_ID, {});

    const wById = {};
    const wByName = {};
    const wNameCounts = {};
    workloads.forEach(w => {
      if (w.workload_id) wById[String(w.workload_id).trim()] = w;
      if (w.workload_name) {
        const wn = w.workload_name.trim();
        wByName[wn] = w;
        wNameCounts[wn] = (wNameCounts[wn] || 0) + 1;
      }
    });

    let pulledCount = 0;
    let pushedCount = 0;
    const nowIso = new Date().toISOString();

    FSR_SHEET_CONFIGS.forEach(cfg => {
      try {
        const ss = SpreadsheetApp.openById(cfg.ssid);
        const sheet = ss.getSheetByName('Follow_up');
        if (!sheet) return;

        const lastRow = Math.min(sheet.getLastRow(), 300);
        if (lastRow < 6) return;

        const numRows = lastRow - 4; // Row 5 (header) through lastRow
        const values = sheet.getRange(5, 1, numRows, 20).getValues();
        const formulas = sheet.getRange(5, 3, numRows, 1).getFormulas();

        const headers = values[0].map(h => String(h || '').trim());
        const colMap = {};
        headers.forEach((h, idx) => { colMap[h] = idx; });

        for (let r = 1; r < numRows; r++) {
          const rowVals = values[r];
          const fStr = formulas[r][0] || '';
          const wid = extractWorkloadIdFromFormula_(fStr);
          const wname = extractHyperlinkLabel_(fStr || rowVals[2]);
          if (!wname && !wid) continue;

          const isUniqueWname = (wNameCounts[wname] || 0) <= 1;
          const primaryKey = wid || wname;
          const mEntry = Object.assign({}, manualEntries[primaryKey] || (isUniqueWname ? manualEntries[wname] : {}) || {});
          const pendingWeb = mEntry.pending_web_edits || {};
          const wObj = (wid && wById[wid]) ? wById[wid] : (isUniqueWname ? wByName[wname] : null);
          let rowChangedLocal = false;

          FIELD_SPECS.forEach(spec => {
            let cIdx = colMap[spec.header] !== undefined ? colMap[spec.header] : spec.colIdx;
            if (spec.key === 'proposal_sent' && colMap[spec.header] === undefined && colMap['Proposal sent to client'] !== undefined) {
              cIdx = colMap['Proposal sent to client'];
            }

            const sheetVal = normVal_(rowVals[cIdx], spec.isBool);
            const hasLocal = mEntry[spec.key] !== undefined;
            const localVal = hasLocal
              ? normVal_(mEntry[spec.key], spec.isBool)
              : (wObj ? normVal_(wObj[spec.webKey], spec.isBool) : (spec.isBool ? false : ''));

            if (pendingWeb[spec.key] !== undefined && sheetVal !== localVal) {
              // Pending Web edit -> push to Sheet
              sheet.getRange(5 + r, cIdx + 1).setValue(localVal);
              delete pendingWeb[spec.key];
              pushedCount++;
              rowChangedLocal = true;
            } else if (sheetVal !== localVal) {
              // Sheet was edited -> pull into Web state
              mEntry[spec.key] = sheetVal;
              if (wObj) {
                wObj[spec.webKey] = sheetVal;
                if (spec.key === 'blocker') wObj.blocker_tecnico = sheetVal;
              }
              pulledCount++;
              rowChangedLocal = true;
            } else if (pendingWeb[spec.key] !== undefined) {
              delete pendingWeb[spec.key];
              rowChangedLocal = true;
            }
          });

          if (rowChangedLocal) {
            if (Object.keys(pendingWeb).length > 0) {
              mEntry.pending_web_edits = pendingWeb;
            } else {
              delete mEntry.pending_web_edits;
            }
            mEntry.updated_at = nowIso;
            manualEntries[primaryKey] = mEntry;
            if (isUniqueWname && wname) manualEntries[wname] = mEntry;
          }
        }
      } catch (sheetErr) {
        console.error('Error syncing sheet ' + cfg.name + ': ' + sheetErr);
      }
    });

    SpreadsheetApp.flush();
    data.generated_at = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyy-MM-dd HH:mm');
    writeDriveJson_(MANUAL_ENTRIES_DRIVE_FILE_ID, manualEntries);
    writeDriveJson_(PORTFOLIO_DRIVE_FILE_ID, data);

    return {
      status: 'ok',
      synced_at: data.generated_at,
      pulled_count: pulledCount,
      pushed_count: pushedCount
    };
  } finally {
    lock.releaseLock();
  }
}

/**
 * POST /api/refresh equivalent
 */
function apiRefresh() {
  return apiSyncSheets({});
}

/**
 * POST /api/draft-nudge equivalent
 */
function apiDraftNudge(payload) {
  const data = buildPortfolioPayload_();
  const workloads = data.workloads || [];
  const wid = payload && payload.workload_id;
  const q = String((payload && (payload.workload_name || payload.search)) || '').toLowerCase().trim();

  let target = null;
  for (let i = 0; i < workloads.length; i++) {
    if (wid && String(workloads[i].workload_id) === String(wid)) {
      target = workloads[i];
      break;
    }
  }
  if (!target && q) {
    for (let i = 0; i < workloads.length; i++) {
      const wn = String(workloads[i].workload_name || '').toLowerCase();
      const an = String(workloads[i].account_name || '').toLowerCase();
      if (wn.indexOf(q) !== -1 || an.indexOf(q) !== -1) {
        target = workloads[i];
        break;
      }
    }
  }
  if (!target && workloads.length > 0) target = workloads[0];
  if (!target) return { error: 'Workload not found' };

  const tel = target.activity_telemetry || {};
  const daysInact = tel.days_inactive || 0;
  const recipients = [
    target.partner_technical_email,
    target.primary_ce_email,
    target.workload_owner_email
  ].filter(Boolean);

  const partnerLabel = target.workload_partner || target.opportunity_partner || target.partner_name || 'Partner Team';
  const arrFormatted = '$' + Math.round(Number(target.arr || target.annual_gross_revenue || 0)).toLocaleString('en-US');
  const subject = '[Action Required] Status Técnico & Próximos Passos: ' + target.account_name + ' — ' + target.workload_name;
  const body =
    'Olá time (' + (target.fsr_name || target.workload_owner_name || '') + ', ' + (target.supporting_ce || '') + ' & ' + partnerLabel + '),\n\n' +
    'Estamos revisando o workload "' + target.workload_name + '" da conta ' + target.account_name + ' ' +
    '(ARR: ' + arrFormatted + ' | Stage: ' + (target.workload_progress_short || '—') + ').\n' +
    'Notamos que a última atualização registrada foi há ' + daysInact + ' dias.\n' +
    '• Resumo atual: ' + (target.ai_summary_next_steps || 'Sem atualização recente no Vector') + '\n' +
    '• Bloqueio: ' + (target.blocker || 'A confirmar') + ' | Status Técnico: ' + (target.status_tecnico || 'Pendente') + '\n\n' +
    'Poderiam confirmar se há algum bloqueio técnico ou comercial e atualizar a data de Go-Live (' + (target.production_date || 'TBD') + ')?\n\n' +
    'Link Vector: ' + (target.vector_url || '');

  return {
    workload_id: target.workload_id,
    account_name: target.account_name,
    workload_name: target.workload_name,
    to: recipients,
    subject: subject,
    body: body,
    requires_user_approval: true
  };
}

/**
 * POST /api/chat equivalent for Apps Script Copilot Drawer
 */
function apiChat(payload) {
  const msg = String((payload && payload.message) || '').trim();
  const msgLow = msg.toLowerCase();
  const filters = (payload && (payload.filters || payload.active_filters)) || {};
  const data = buildPortfolioPayload_();
  const workloads = data.workloads || [];

  // 1. Check if the user is asking to set/update a blocker or status_tecnico via chat
  const setMatch = msg.match(/set\s+blocker\s+for\s+(.+?)\s+to\s+(tecnico|técnico|comercial)/i);
  if (setMatch) {
    const qName = setMatch[1].trim();
    const blkVal = setMatch[2].toLowerCase().indexOf('tecnic') === 0 ? 'Tecnico' : 'Comercial';
    const upd = apiUpdateField({ workload_name: qName, field: 'blocker', value: blkVal });
    if (upd.status === 'ok') {
      return {
        reply: '✓ Updated **' + upd.account_name + ' — ' + upd.workload_name + '** (`Bloqueo` set to **' + blkVal + '**) and synced directly to the Google Sheet.',
        updated_workloads: [upd]
      };
    }
  }

  // 2. Filter portfolio based on active UI filters + natural language query
  let subset = workloads.slice();
  if (filters.pdm && filters.pdm !== 'ALL') {
    subset = subset.filter(w => w.pdm_owner === filters.pdm);
  }
  if (filters.fsr && filters.fsr !== 'ALL') {
    subset = subset.filter(w => w.fsr_ldap === filters.fsr);
  }

  const fsrKeywords = [
    { key: 'pilon', ldap: 'fpilon', label: 'Felipe Pilon' },
    { key: 'roberta', ldap: 'robertacoelho', label: 'Roberta Coelho' },
    { key: 'coelho', ldap: 'robertacoelho', label: 'Roberta Coelho' },
    { key: 'vanessa', ldap: 'vmmoyses', label: 'Vanessa Moyses' },
    { key: 'moyses', ldap: 'vmmoyses', label: 'Vanessa Moyses' },
    { key: 'daniela', ldap: 'dbenevides', label: 'Daniela Benevides' },
    { key: 'benevides', ldap: 'dbenevides', label: 'Daniela Benevides' },
    { key: 'daniel ', ldap: 'dprudencio', label: 'Daniel Prudencio' },
    { key: 'prudencio', ldap: 'dprudencio', label: 'Daniel Prudencio' },
    { key: 'sarah', ldap: 'tobiassarah', label: 'Sarah Tobias' },
    { key: 'tobias', ldap: 'tobiassarah', label: 'Sarah Tobias' }
  ];
  for (let i = 0; i < fsrKeywords.length; i++) {
    if (msgLow.indexOf(fsrKeywords[i].key) !== -1) {
      subset = workloads.filter(w => w.fsr_ldap === fsrKeywords[i].ldap);
      break;
    }
  }

  if (msgLow.indexOf('luna') !== -1) {
    subset = workloads.filter(w => w.pdm_owner === 'Luna Longo');
  } else if (msgLow.indexOf('oliver') !== -1) {
    subset = workloads.filter(w => w.pdm_owner === 'Oliver Hartley');
  }

  if (msgLow.indexOf('unpartnered') !== -1 || msgLow.indexOf('without partner') !== -1 || msgLow.indexOf('matchmaker') !== -1 || msgLow.indexOf('recommend') !== -1) {
    const unp = subset
      .filter(w => (!w.is_partnered && !(w.workload_partner || '').trim()))
      .sort((a, b) => Number(b.arr || 0) - Number(a.arr || 0));
    const withOppP = unp.filter(w => (w.opportunity_partner || '').trim());
    const totalUnpArr = unp.reduce((s, w) => s + Number(w.arr || 0), 0);
    const lines = [
      '**Workloads Without Partner**: **' + unp.length + ' workloads** ($' + Math.round(totalUnpArr).toLocaleString('en-US') + ' ARR) — **' + withOppP.length + '** already have an Opportunity Partner on their Associated Opportunity, and **' + (unp.length - withOppP.length) + '** have no partner on either.'
    ];
    unp.slice(0, 7).forEach(w => {
      const oppName = w.opportunity_name || '—';
      const oppP = (w.opportunity_partner || '').trim();
      const oppPartnerLabel = oppP ? ('🔗 Opp Partner: **' + oppP + '**') : '🚨 No Opp Partner';
      const rec = (w.partner_recommendations && w.partner_recommendations[0])
        ? w.partner_recommendations[0].partner
        : 'Evaluate Brazil DRP Tier 1 bench';
      lines.push('• **' + w.account_name + ' — ' + w.workload_name + '** ($' + Math.round(Number(w.arr || 0)).toLocaleString('en-US') + ' | FSR: `' + w.fsr_name + '`) | Opp: `' + oppName + '` (' + oppPartnerLabel + ') → AI Rec: **' + rec + '**');
    });
    return { reply: lines.join('\n'), updated_workloads: [] };
  }

  if (msgLow.indexOf('tecnic') !== -1 || msgLow.indexOf('técnic') !== -1 || msgLow.indexOf('blocker') !== -1) {
    const blocked = subset
      .filter(w => String(w.blocker || '').toLowerCase().indexOf('tecnic') === 0 || (w.health && w.health.status === 'RED'))
      .sort((a, b) => Number(b.arr || 0) - Number(a.arr || 0));
    const totalBlkArr = blocked.reduce((s, w) => s + Number(w.arr || 0), 0);
    const lines = [
      '**Active Technical Blockers & High-Risk Deals**: **' + blocked.length + ' workloads** ($' + Math.round(totalBlkArr).toLocaleString('en-US') + ' ARR).'
    ];
    blocked.slice(0, 7).forEach(w => {
      lines.push('• **' + w.account_name + ' — ' + w.workload_name + '** ($' + Math.round(Number(w.arr || 0)).toLocaleString('en-US') + ' | FSR: `' + w.fsr_name + '` | Bloqueo: `' + (w.blocker || 'Risk') + '` | Status: ' + (w.status_tecnico || w.ai_summary_next_steps || '—') + ')');
    });
    return { reply: lines.join('\n'), updated_workloads: [] };
  }

  if (msgLow.indexOf('stalled') !== -1 || msgLow.indexOf('30') !== -1 || msgLow.indexOf('silent') !== -1 || msgLow.indexOf('dormant') !== -1 || msgLow.indexOf('inactiv') !== -1) {
    const stalled = subset
      .filter(w => (w.activity_telemetry && w.activity_telemetry.inactivity_tier) === 'STALLED_30D')
      .sort((a, b) => Number(b.arr || 0) - Number(a.arr || 0));
    const totalStalledArr = stalled.reduce((s, w) => s + Number(w.arr || 0), 0);
    const lines = [
      '**Stalled Workloads (>30 Days No Activity)**: **' + stalled.length + ' workloads** ($' + Math.round(totalStalledArr).toLocaleString('en-US') + ' ARR).'
    ];
    stalled.slice(0, 7).forEach(w => {
      const days = (w.activity_telemetry && w.activity_telemetry.days_inactive) || '30+';
      lines.push('• **' + w.account_name + ' — ' + w.workload_name + '** ($' + Math.round(Number(w.arr || 0)).toLocaleString('en-US') + ' | `' + days + 'd silent` | FSR: `' + w.fsr_name + '` | Partner Email: `' + (w.partner_technical_email || '—') + '`)');
    });
    return { reply: lines.join('\n'), updated_workloads: [] };
  }

  // Default executive portfolio summary
  subset.sort((a, b) => Number(b.arr || 0) - Number(a.arr || 0));
  const totalArr = subset.reduce((s, w) => s + Number(w.arr || 0), 0);
  const stalledCount = subset.filter(w => (w.activity_telemetry && w.activity_telemetry.inactivity_tier) === 'STALLED_30D').length;
  const lines = [
    '**Portfolio Snapshot**: **' + subset.length + ' active workloads** ($' + Math.round(totalArr).toLocaleString('en-US') + ' ARR | **' + stalledCount + '** stalled >30d). Top workloads by ARR:'
  ];
  subset.slice(0, 6).forEach(w => {
    const days = (w.activity_telemetry && w.activity_telemetry.days_inactive) !== undefined ? w.activity_telemetry.days_inactive + 'd' : '—';
    lines.push('• **' + w.account_name + ' — ' + w.workload_name + '** ($' + Math.round(Number(w.arr || 0)).toLocaleString('en-US') + ' | Stage `' + (w.workload_progress_short || '—') + '` | Last touch: `' + days + '` | FSR: `' + w.fsr_name + '`)');
  });
  return { reply: lines.join('\n'), updated_workloads: [] };
}
