/**
 * SNS月次レポート 自動化（Google Apps Script） v2
 * ============================================================
 * Phase 1: 各社「効果測定シート(生データ)」から対象月を集計 → コントロールSSの「集約」へ出力
 * Phase 2: 「転記マップ」に従い、各「プロジェクトシート」の当月KPI結果セルへ自動転記
 *          ＋ 当月ブロックの追加（テンプレ複製）
 *
 * 安全設計
 *  - 書き込み系は既定が DRY-RUN（実際には書かず、書き込み予定をログ出力）。
 *    実行する場合のみ各関数の実引数で run=true を渡す（メニュー参照）。
 *  - 各社のレイアウト差・KPI差は「転記マップ」タブで吸収（社ごとに行を足す）。
 *  - ハンドル照合で別アカウント混入を検知。
 *
 * タブ構成（コントロールSS）
 *  - 設定        : クライアント一覧（効果測定/PJシートID・アカウント）
 *  - 転記マップ  : PJシートのKPIラベル ⇄ 集計指標キー の対応
 *  - 集約        : 集計結果の出力
 *  - ログ        : 実行ログ／DRY-RUNの転記プレビュー
 */

/** ===== 固定設定 ===== */
var CONFIG_SHEET = '設定';
var MAP_SHEET    = '転記マップ';
var OUTPUT_SHEET = '集約';
var LOG_SHEET    = 'ログ';

var HEADER_ALIASES = {
  date:    ['投稿日'],
  views:   ['再生回数', '再生数'],
  likes:   ['いいね'],
  comments:['コメント'],
  shares:  ['シェア'],
  saves:   ['保存数', '保存'],
  follow:  ['フォロワー増加数', 'フォロワー 増加数', 'フォロワー増加'],
  url:     ['URL', 'url'],
  profile: ['プロフィール閲覧数', 'プロフィール 閲覧数'],
  reach:   ['リーチ数', 'リーチ した数', 'リーチした数'],
  fullview:['フル視聴率'],
  watch:   ['平均視聴時間', '平均閲覧 時間(秒)', '平均閲覧時間(秒)']
};

// 集計が返す指標キー（転記マップの「指標キー」列で使える値）
//  posts, views_sum, views_avg, eg, follow_add, profile_sum, reach_sum, fullview_avg, watch_avg

/** ===== メニュー ===== */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('SNS月次集計')
    .addItem('① 当月を集計', 'runCurrentMonth')
    .addItem('① 前月を集計', 'runPrevMonth')
    .addItem('① 対象月を指定して集計', 'runWithPrompt')
    .addSeparator()
    .addItem('② 転記プレビュー（DRY-RUN）', 'transcribeDryRunPrompt')
    .addItem('②’ 転記を実行（本番・書き込み）', 'transcribeRunPrompt')
    .addSeparator()
    .addItem('③ 当月ブロック追加 プレビュー（DRY-RUN）', 'addBlockDryRunPrompt')
    .addItem('③’ 当月ブロック追加 実行', 'addBlockRunPrompt')
    .addToUi();
}

function runCurrentMonth() { var d = new Date(); 集計実行(d.getFullYear(), d.getMonth() + 1); }
function runPrevMonth()   { var d = new Date(); d.setMonth(d.getMonth() - 1); 集計実行(d.getFullYear(), d.getMonth() + 1); }
function runWithPrompt()  { var ym = promptYM_(); if (ym) 集計実行(ym.y, ym.m); }

function transcribeDryRunPrompt() { var ym = promptYM_(); if (ym) 転記実行(ym.y, ym.m, false); }
function transcribeRunPrompt() {
  var ym = promptYM_(); if (!ym) return;
  if (!confirm_('【本番】' + fmtYM_(ym.y, ym.m) + ' の結果を各プロジェクトシートに書き込みます。よろしいですか？')) return;
  転記実行(ym.y, ym.m, true);
}
function addBlockDryRunPrompt() { var ym = promptYM_(); if (ym) 月次ブロック追加(ym.y, ym.m, false); }
function addBlockRunPrompt() {
  var ym = promptYM_(); if (!ym) return;
  if (!confirm_('【本番】' + fmtYM_(ym.y, ym.m) + ' のブロックを各プロジェクトシートに追加します。よろしいですか？')) return;
  月次ブロック追加(ym.y, ym.m, true);
}

function promptYM_() {
  var ui = SpreadsheetApp.getUi();
  var res = ui.prompt('対象月を入力', '例: 2026-05', ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return null;
  var m = String(res.getResponseText()).match(/(\d{4})\D+(\d{1,2})/);
  if (!m) { ui.alert('形式が不正です。例: 2026-05'); return null; }
  return { y: Number(m[1]), m: Number(m[2]) };
}
function confirm_(msg) {
  var ui = SpreadsheetApp.getUi();
  return ui.alert('確認', msg, ui.ButtonSet.OK_CANCEL) === ui.Button.OK;
}
function fmtYM_(y, m) { return y + '-' + ('0' + m).slice(-2); }

/** =====================================================================
 *  ① 集計
 *  ===================================================================== */
function 集計実行(year, month) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ym = fmtYM_(year, month);
  var clients = getConfig_(ss);
  var out = [];

  clients.forEach(function (c) {
    if (!c.enabled) return;
    var row = baseRow_(ym, c);
    try {
      if (!c.dataSheetId) { row.status = '効果測定シートID未設定'; out.push(row); return; }
      var src = SpreadsheetApp.openById(c.dataSheetId);
      var sh = findRawSheet_(src, c.rawTabName);
      if (!sh) { row.status = '生データタブ検出不可'; out.push(row); return; }
      var agg = aggregate_(sh, ym, c.account);
      if (agg.posts === 0) { row.status = '対象月の投稿なし'; out.push(row); return; }
      row.metrics = agg;
      row.posts = agg.posts;
      row.views = agg.views_sum;
      row.avg = agg.views_avg;
      row.eg = agg.eg;
      row.follow = agg.follow_add;
      row.profile = agg.profile_sum;
      row.status = 'OK';
      if (agg.handleWarn) row.warn = '⚠ハンドル不一致:' + agg.handleWarn;
    } catch (e) { row.status = 'エラー: ' + e.message; }
    out.push(row);
  });

  writeOutput_(ss, ym, out);
  log_(ss, [new Date(), ym, '集計', '対象' + out.length + '社',
            'OK' + out.filter(function (r) { return r.status === 'OK'; }).length + '社']);
  toast_(ym + ' 集計完了（' + out.length + '社）');
}

function baseRow_(ym, c) {
  return { ym: ym, name: c.name, account: c.account, posts: '', views: '', avg: '',
           eg: '', follow: '', profile: '', status: '', warn: '', metrics: null };
}

/** =====================================================================
 *  ② 転記（DRY-RUN / 本番）
 *  ===================================================================== */
function 転記実行(year, month, run) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ym = fmtYM_(year, month);
  var monthLabel = month + '月';
  var clients = getConfig_(ss);
  var maps = getMap_(ss);              // クライアント名 -> [{label, key, target}]
  var preview = [];

  clients.forEach(function (c) {
    if (!c.enabled || !c.projSheetId) return;
    var rules = maps[c.name] || maps['*'] || [];
    if (!rules.length) return;
    var agg;
    try {
      var src = SpreadsheetApp.openById(c.dataSheetId);
      var raw = findRawSheet_(src, c.rawTabName);
      agg = aggregate_(raw, ym, c.account);
    } catch (e) { preview.push([ym, c.name, '', '', '集計失敗:' + e.message]); return; }
    if (!agg || agg.posts === 0) { preview.push([ym, c.name, '', '', '対象月データなし→スキップ']); return; }

    var proj;
    try { proj = SpreadsheetApp.openById(c.projSheetId); }
    catch (e) { preview.push([ym, c.name, '', '', 'PJシート開けず:' + e.message]); return; }

    rules.forEach(function (rule) {
      var val = pickMetric_(agg, rule.key);
      if (val === null || val === '') { preview.push([ym, c.name, rule.label, '(指標値なし)', 'skip']); return; }
      var loc = locateResultCell_(proj, monthLabel, rule.label, rule.target);
      if (!loc) { preview.push([ym, c.name, rule.label, val, '⚠セル特定不可']); return; }
      preview.push([ym, c.name, rule.label, val, (run ? '書込: ' : 'DRY: ') + loc.sheetName + '!' + loc.a1]);
      if (run) loc.range.setValue(val);
    });
  });

  // プレビュー/結果をログタブへ
  var sh = ss.getSheetByName(LOG_SHEET) || ss.insertSheet(LOG_SHEET);
  sh.appendRow([new Date(), ym, run ? '転記(本番)' : '転記(DRY-RUN)', preview.length + '件', '↓詳細']);
  if (preview.length) {
    sh.appendRow(['対象月', 'クライアント', 'KPIラベル', '値', '結果/予定']);
    sh.getRange(sh.getLastRow() + 1, 1, preview.length, 5).setValues(preview);
  }
  toast_((run ? '転記実行' : 'DRY-RUN') + ' 完了（' + preview.length + '件）。ログタブ参照');
}

/** 集計結果から指標キーの値を取り出す */
function pickMetric_(agg, key) {
  switch (key) {
    case 'posts':        return agg.posts;
    case 'views_sum':    return agg.views_sum;
    case 'views_avg':    return agg.views_avg;
    case 'eg':           return agg.eg;
    case 'follow_add':   return agg.follow_add;
    case 'profile_sum':  return agg.profile_sum;
    case 'reach_sum':    return agg.reach_sum;
    case 'fullview_avg': return agg.fullview_avg;
    case 'watch_avg':    return agg.watch_avg;
    default:             return null;
  }
}

/**
 * プロジェクトシート内で「対象月の列グループ × KPIラベル行」の結果セルを特定。
 *  - 月見出しセル（例 "5月"）を探し、その列を起点に4列を月グループとみなす。
 *  - KPIラベルは目標行（区分B列が"目標"）の月グループ内テキストで照合。
 *  - 結果セルは同じ列・直下の「結果」行。
 * target: '結果'(既定) など。複数ヒット時は最初の月ブロックを採用（DRY-RUNで要確認）。
 */
function locateResultCell_(ss, monthLabel, kpiLabel, target) {
  var sheets = ss.getSheets();
  for (var s = 0; s < sheets.length; s++) {
    var sheet = sheets[s];
    var lr = sheet.getLastRow(), lc = sheet.getLastColumn();
    if (lr < 2 || lc < 2) continue;
    var vals = sheet.getRange(1, 1, lr, lc).getValues();

    // 月見出し行と月列を探す
    for (var r = 0; r < vals.length; r++) {
      for (var col = 0; col < lc; col++) {
        if (String(vals[r][col]).trim() === monthLabel) {
          // この月グループ [col .. col+3] の目標/結果ペアでKPIラベルを探す
          var found = scanMonthGroup_(sheet, vals, r, col, kpiLabel);
          if (found) return found;
        }
      }
    }
  }
  return null;
}

function scanMonthGroup_(sheet, vals, headerRow, monthCol, kpiLabel) {
  var lr = vals.length;
  var grpEnd = Math.min(monthCol + 3, vals[0].length - 1);
  var re = labelRegex_(kpiLabel);
  // 目標行(=B列が"目標")で、月グループ内にKPIラベルを含む行を探す
  for (var r = headerRow + 1; r < lr; r++) {
    var bcol = String(vals[r][1]).trim();
    if (bcol !== '目標') continue;
    var labelHit = false;
    for (var c = monthCol; c <= grpEnd; c++) {
      if (re.test(String(vals[r][c]))) { labelHit = true; break; }
    }
    if (!labelHit) continue;
    // 直下の "結果" 行を探す（通常 r+1）
    for (var rr = r + 1; rr < Math.min(r + 3, lr); rr++) {
      if (String(vals[rr][1]).trim() === '結果') {
        // 値の書き込み先：目標値が入っていた列に合わせる。無ければ月グループ先頭+2列目。
        var writeCol = monthCol + 2;
        var a1 = sheet.getRange(rr + 1, writeCol + 1).getA1Notation();
        return { sheet: sheet, sheetName: sheet.getName(),
                 range: sheet.getRange(rr + 1, writeCol + 1), a1: a1 };
      }
    }
  }
  return null;
}

function labelRegex_(kpiLabel) {
  // 転記マップのラベルは正規表現としても使える（"再生数|平均再生" など）
  try { return new RegExp(kpiLabel); }
  catch (e) { return new RegExp(kpiLabel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); }
}

/** =====================================================================
 *  ③ 当月ブロック追加（テンプレ複製）
 *     設定の「テンプレタブ名」または直近月ブロックを複製する想定。
 *     レイアウト差が大きいため既定はDRY-RUN（プレビューのみ）。
 *  ===================================================================== */
function 月次ブロック追加(year, month, run) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ym = fmtYM_(year, month);
  var clients = getConfig_(ss);
  var note = [];
  clients.forEach(function (c) {
    if (!c.enabled || !c.projSheetId) return;
    // 本番のブロック自動挿入はレイアウト破損リスクが高いため、
    // ここでは「当月見出しが既に存在するか」を点検し、無ければ要手動追加を通知。
    try {
      var proj = SpreadsheetApp.openById(c.projSheetId);
      var exists = hasMonthLabel_(proj, month + '月');
      note.push([ym, c.name, exists ? '当月ブロックあり' : '⚠当月ブロック無し→要追加(手動/テンプレ複製)']);
    } catch (e) { note.push([ym, c.name, 'PJシート開けず:' + e.message]); }
  });
  var sh = ss.getSheetByName(LOG_SHEET) || ss.insertSheet(LOG_SHEET);
  sh.appendRow([new Date(), ym, 'ブロック点検', note.length + '社', run ? '(run指定だが安全のため点検のみ)' : 'DRY']);
  if (note.length) sh.getRange(sh.getLastRow() + 1, 1, note.length, 3).setValues(note);
  toast_('ブロック点検 完了（' + note.length + '社）。ログタブ参照');
}

function hasMonthLabel_(ss, monthLabel) {
  var sheets = ss.getSheets();
  for (var s = 0; s < sheets.length; s++) {
    var f = sheets[s].createTextFinder('^' + monthLabel + '$').useRegularExpression(true).matchEntireCell(true).findNext();
    if (f) return true;
  }
  return false;
}

/** =====================================================================
 *  設定 / 転記マップ 読み込み
 *  ===================================================================== */
function getConfig_(ss) {
  var sh = ss.getSheetByName(CONFIG_SHEET);
  if (!sh) throw new Error('「' + CONFIG_SHEET + '」タブがありません');
  var values = sh.getDataRange().getValues();
  var h = values[0].map(function (v) { return String(v).trim(); });
  function ci(n) { return h.indexOf(n); }
  var iEn = ci('有効'), iNm = ci('クライアント名'), iD = ci('効果測定シートID'),
      iR = ci('生データタブ名'), iP = ci('プロジェクトシートID'), iA = ci('アカウント');
  var list = [];
  for (var r = 1; r < values.length; r++) {
    var row = values[r]; if (!row[iNm]) continue;
    var en = String(row[iEn]).toUpperCase();
    list.push({
      enabled: (en === 'TRUE' || en === '1' || en === '有効' || en === ''),
      name: String(row[iNm]).trim(),
      dataSheetId: String(row[iD] || '').trim(),
      rawTabName: iR >= 0 ? String(row[iR] || '').trim() : '',
      projSheetId: iP >= 0 ? String(row[iP] || '').trim() : '',
      account: iA >= 0 ? String(row[iA] || '').trim().replace(/^@/, '') : ''
    });
  }
  return list;
}

function getMap_(ss) {
  var sh = ss.getSheetByName(MAP_SHEET);
  if (!sh) return {};
  var values = sh.getDataRange().getValues();
  if (values.length < 2) return {};
  var h = values[0].map(function (v) { return String(v).trim(); });
  function ci(n) { return h.indexOf(n); }
  var iC = ci('クライアント名'), iL = ci('KPIラベル'), iK = ci('指標キー'), iT = ci('対象');
  var map = {};
  for (var r = 1; r < values.length; r++) {
    var row = values[r];
    var name = String(row[iC] || '').trim(); if (!name) continue;
    var label = String(row[iL] || '').trim(); var key = String(row[iK] || '').trim();
    if (!label || !key) continue;
    (map[name] = map[name] || []).push({
      label: label, key: key, target: iT >= 0 ? (String(row[iT] || '結果').trim() || '結果') : '結果'
    });
  }
  return map;
}

/** =====================================================================
 *  生データ集計（共通）
 *  ===================================================================== */
function findRawSheet_(ss, rawTabName) {
  if (rawTabName) { var s = ss.getSheetByName(rawTabName); if (s) return s; }
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) if (findHeaderRow_(sheets[i]).rowIndex >= 0) return sheets[i];
  return null;
}
function findHeaderRow_(sheet) {
  var maxScan = Math.min(6, sheet.getLastRow()); if (maxScan < 1) return { rowIndex: -1 };
  var values = sheet.getRange(1, 1, maxScan, Math.max(1, sheet.getLastColumn())).getValues();
  for (var r = 0; r < values.length; r++) {
    var t = values[r].map(function (v) { return String(v).trim(); });
    var d = t.some(function (x) { return HEADER_ALIASES.date.indexOf(x) >= 0; });
    var v = t.some(function (x) { return HEADER_ALIASES.views.indexOf(x) >= 0; });
    if (d && v) return { rowIndex: r, header: t };
  }
  return { rowIndex: -1 };
}
function headerMap_(header) {
  var map = {};
  Object.keys(HEADER_ALIASES).forEach(function (key) {
    var al = HEADER_ALIASES[key];
    for (var c = 0; c < header.length; c++) if (al.indexOf(header[c]) >= 0) { map[key] = c; break; }
  });
  return map;
}
function aggregate_(sheet, ym, expectAccount) {
  var hr = findHeaderRow_(sheet); if (hr.rowIndex < 0) return { posts: 0 };
  var col = headerMap_(hr.header);
  var last = sheet.getLastRow(), width = sheet.getLastColumn();
  var start = hr.rowIndex + 2; if (start > last) return { posts: 0 };
  var data = sheet.getRange(start, 1, last - start + 1, width).getValues();

  var posts = 0, views = 0, eng = 0, follow = 0, profile = 0, reach = 0, fvSum = 0, watchSum = 0;
  var handleCount = {};
  data.forEach(function (row) {
    if (parseYM_(row[col.date]) !== ym) return;
    posts++;
    views   += num_(row[col.views]);
    eng     += num_(row[col.likes]) + num_(row[col.comments]) + num_(row[col.shares]) + num_(row[col.saves]);
    follow  += num_(row[col.follow]);
    if (col.profile  != null) profile += num_(row[col.profile]);
    if (col.reach    != null) reach   += num_(row[col.reach]);
    if (col.fullview != null) fvSum   += num_(row[col.fullview]);
    if (col.watch    != null) watchSum+= num_(row[col.watch]);
    if (col.url != null && expectAccount) {
      var m = String(row[col.url]).match(/@([A-Za-z0-9_.]+)/);
      if (m) handleCount[m[1]] = (handleCount[m[1]] || 0) + 1;
    }
  });

  var handleWarn = '';
  if (expectAccount && posts > 0) {
    var top = '', topN = 0;
    Object.keys(handleCount).forEach(function (h) { if (handleCount[h] > topN) { topN = handleCount[h]; top = h; } });
    if (top && top.toLowerCase() !== expectAccount.toLowerCase()) handleWarn = '検出=' + top + ' / 設定=' + expectAccount;
  }
  return {
    posts: posts,
    views_sum: views,
    views_avg: posts ? Math.round(views / posts) : 0,
    eg: views ? +((eng / views) * 100).toFixed(2) : 0,
    follow_add: follow,
    profile_sum: profile,
    reach_sum: reach,
    fullview_avg: posts ? +((fvSum / posts) * 100).toFixed(2) : 0, // フル視聴率は小数(0.03=3%)前提で%化
    watch_avg: posts ? +(watchSum / posts).toFixed(2) : 0,
    handleWarn: handleWarn
  };
}

function parseYM_(v) {
  if (v == null || v === '') return '';
  if (Object.prototype.toString.call(v) === '[object Date]')
    return v.getFullYear() + '-' + ('0' + (v.getMonth() + 1)).slice(-2);
  var m = String(v).trim().match(/^(\d{4})[-\/](\d{1,2})/);
  return m ? m[1] + '-' + ('0' + m[2]).slice(-2) : '';
}
function num_(v) {
  if (v == null || v === '') return 0;
  if (typeof v === 'number') return v;
  var n = parseFloat(String(v).replace(/[,\s%％]/g, ''));
  return isNaN(n) ? 0 : n;
}

/** 出力／ログ */
function writeOutput_(ss, ym, rows) {
  var sh = ss.getSheetByName(OUTPUT_SHEET) || ss.insertSheet(OUTPUT_SHEET);
  var header = ['対象月', 'クライアント', 'アカウント', '投稿数', '再生数合計', '再生平均/本',
                'EG率%(対再生)', 'フォロワー増加', 'プロフ閲覧計', '状態', '警告', '更新日時'];
  if (sh.getLastRow() === 0) sh.appendRow(header);
  var all = sh.getDataRange().getValues();
  for (var r = all.length - 1; r >= 1; r--) if (String(all[r][0]) === ym) sh.deleteRow(r + 1);
  var now = new Date();
  var buf = rows.map(function (x) {
    return [x.ym, x.name, x.account ? '@' + x.account : '', x.posts, x.views, x.avg,
            x.eg, x.follow, x.profile, x.status, x.warn, now];
  });
  if (buf.length) sh.getRange(sh.getLastRow() + 1, 1, buf.length, header.length).setValues(buf);
  sh.autoResizeColumns(1, header.length);
}
function log_(ss, arr) { var sh = ss.getSheetByName(LOG_SHEET) || ss.insertSheet(LOG_SHEET); sh.appendRow(arr); }
function toast_(msg) { SpreadsheetApp.getActiveSpreadsheet().toast(msg, 'SNS月次集計', 5); }
