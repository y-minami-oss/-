/**
 * SNS月次レポート 自動集計（Google Apps Script）
 * ------------------------------------------------------------
 * 目的：各クライアントの「効果測定シート」から対象月の実績を自動集計し、
 *       コントロールSS内の「集約」タブに1行/社で書き出す。
 *       併せて、アカウントハンドル照合・データ有無の品質チェックを行う。
 *
 * 設計のポイント
 *  - 設定シート駆動：クライアントを増やすときは「設定」タブに行を足すだけ。
 *  - ヘッダー名でカラムを自動判定：社ごとに列順が多少違っても壊れない。
 *  - ハンドル照合：効果測定シートの対象月行のURLが、設定のアカウントと
 *    一致するか検証（過去に出光⇄山謙のタブ混入があったため）。
 *  - 集計は「投稿単位の生データタブ」を対象。集計ブロック（#REF!になりがち）は使わない。
 *
 * 注意
 *  - このスクリプトは「読み取り（各効果測定シート）」＋「書き込み（コントロールSSの集約タブ）」
 *    のみを行う安全設計。各プロジェクトシートへの直接転記は phase2（要・社別セル設定）。
 */

/** ===== 固定設定 ===== */
var CONFIG_SHEET = '設定';     // クライアント一覧タブ名
var OUTPUT_SHEET = '集約';     // 集計結果の出力タブ名
var LOG_SHEET    = 'ログ';     // 実行ログ

// 生データタブで探すヘッダーの「別名」辞書（社ごとの表記ゆれを吸収）
var HEADER_ALIASES = {
  date:    ['投稿日'],
  views:   ['再生回数', '再生数'],
  likes:   ['いいね'],
  comments:['コメント'],
  shares:  ['シェア'],
  saves:   ['保存数', '保存'],
  follow:  ['フォロワー増加数', 'フォロワー 増加数', 'フォロワー増加'],
  url:     ['URL', 'url'],
  profile: ['プロフィール閲覧数', 'プロフィール 閲覧数']
};

/** ===== メニュー ===== */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('SNS月次集計')
    .addItem('当月を集計', 'runCurrentMonth')
    .addItem('前月を集計', 'runPrevMonth')
    .addItem('対象月を指定して集計', 'runWithPrompt')
    .addToUi();
}

function runCurrentMonth() {
  var d = new Date();
  集計実行(d.getFullYear(), d.getMonth() + 1);
}
function runPrevMonth() {
  var d = new Date();
  d.setMonth(d.getMonth() - 1);
  集計実行(d.getFullYear(), d.getMonth() + 1);
}
function runWithPrompt() {
  var ui = SpreadsheetApp.getUi();
  var res = ui.prompt('対象月を入力', '例: 2026-05', ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;
  var m = String(res.getResponseText()).match(/(\d{4})\D+(\d{1,2})/);
  if (!m) { ui.alert('形式が不正です。例: 2026-05'); return; }
  集計実行(Number(m[1]), Number(m[2]));
}

/** ===== コア処理 ===== */
function 集計実行(year, month) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ym = year + '-' + ('0' + month).slice(-2); // "2026-05"
  var clients = getConfig_(ss);
  var out = [];
  var logs = [];

  clients.forEach(function (c) {
    if (!c.enabled) return;
    var row = {
      ym: ym, name: c.name, account: c.account,
      posts: '', views: '', avg: '', eg: '', follow: '', profile: '',
      status: '', warn: ''
    };
    try {
      if (!c.dataSheetId) { row.status = '効果測定シートID未設定'; out.push(row); return; }
      var src = SpreadsheetApp.openById(c.dataSheetId);
      var sh = findRawSheet_(src, c.rawTabName);
      if (!sh) { row.status = '生データタブ検出不可'; out.push(row); return; }

      var agg = aggregate_(sh, ym, c.account);
      if (agg.posts === 0) {
        row.status = '対象月の投稿なし（計測対象外/投稿前の可能性）';
        out.push(row); return;
      }
      row.posts = agg.posts;
      row.views = agg.views;
      row.avg = Math.round(agg.views / agg.posts);
      row.eg = agg.views ? +( (agg.eng / agg.views) * 100 ).toFixed(2) : '';
      row.follow = agg.follow;
      row.profile = agg.profile || '';
      row.status = 'OK';
      if (agg.handleWarn) row.warn = '⚠ハンドル不一致:' + agg.handleWarn;
    } catch (e) {
      row.status = 'エラー: ' + e.message;
    }
    out.push(row);
  });

  writeOutput_(ss, ym, out);
  writeLog_(ss, ym, out);
  SpreadsheetApp.getActiveSpreadsheet().toast(ym + ' の集計が完了（' + out.length + '社）', 'SNS月次集計', 5);
}

/** 設定タブを読む */
function getConfig_(ss) {
  var sh = ss.getSheetByName(CONFIG_SHEET);
  if (!sh) throw new Error('「' + CONFIG_SHEET + '」タブがありません');
  var values = sh.getDataRange().getValues();
  var header = values[0].map(function (v) { return String(v).trim(); });
  function col(name) { return header.indexOf(name); }
  var iEnabled = col('有効'), iName = col('クライアント名'),
      iData = col('効果測定シートID'), iRaw = col('生データタブ名'),
      iProj = col('プロジェクトシートID'), iAcc = col('アカウント');
  var list = [];
  for (var r = 1; r < values.length; r++) {
    var row = values[r];
    if (!row[iName]) continue;
    var en = String(row[iEnabled]).toUpperCase();
    list.push({
      enabled: (en === 'TRUE' || en === '1' || en === '有効' || en === ''),
      name: String(row[iName]).trim(),
      dataSheetId: String(row[iData] || '').trim(),
      rawTabName: iRaw >= 0 ? String(row[iRaw] || '').trim() : '',
      projSheetId: iProj >= 0 ? String(row[iProj] || '').trim() : '',
      account: iAcc >= 0 ? String(row[iAcc] || '').trim().replace(/^@/, '') : ''
    });
  }
  return list;
}

/** 生データタブを特定（タブ名指定 or ヘッダー検出） */
function findRawSheet_(ss, rawTabName) {
  if (rawTabName) {
    var s = ss.getSheetByName(rawTabName);
    if (s) return s;
  }
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    var hr = findHeaderRow_(sheets[i]);
    if (hr.rowIndex >= 0) return sheets[i];
  }
  return null;
}

/** ヘッダー行を探す（投稿日＋再生回数を含む行を上から探索） */
function findHeaderRow_(sheet) {
  var maxScan = Math.min(6, sheet.getLastRow());
  if (maxScan < 1) return { rowIndex: -1 };
  var values = sheet.getRange(1, 1, maxScan, Math.max(1, sheet.getLastColumn())).getValues();
  for (var r = 0; r < values.length; r++) {
    var rowText = values[r].map(function (v) { return String(v).trim(); });
    var hasDate = rowText.some(function (t) { return HEADER_ALIASES.date.indexOf(t) >= 0; });
    var hasViews = rowText.some(function (t) { return HEADER_ALIASES.views.indexOf(t) >= 0; });
    if (hasDate && hasViews) return { rowIndex: r, header: rowText };
  }
  return { rowIndex: -1 };
}

/** ヘッダー名 → 列index のマップ */
function headerMap_(header) {
  var map = {};
  Object.keys(HEADER_ALIASES).forEach(function (key) {
    var aliases = HEADER_ALIASES[key];
    for (var c = 0; c < header.length; c++) {
      if (aliases.indexOf(header[c]) >= 0) { map[key] = c; break; }
    }
  });
  return map;
}

/** 対象月を集計 */
function aggregate_(sheet, ym, expectAccount) {
  var hr = findHeaderRow_(sheet);
  if (hr.rowIndex < 0) return { posts: 0 };
  var col = headerMap_(hr.header);
  var last = sheet.getLastRow();
  var width = sheet.getLastColumn();
  var startRow = hr.rowIndex + 2; // データ開始行（1始まり）
  if (startRow > last) return { posts: 0 };
  var data = sheet.getRange(startRow, 1, last - startRow + 1, width).getValues();

  var posts = 0, views = 0, eng = 0, follow = 0, profile = 0;
  var handleCount = {}, handleWarn = '';
  data.forEach(function (row) {
    var ymRow = parseYM_(row[col.date]);
    if (ymRow !== ym) return;
    posts++;
    views  += num_(row[col.views]);
    eng    += num_(row[col.likes]) + num_(row[col.comments]) + num_(row[col.shares]) + num_(row[col.saves]);
    follow += num_(row[col.follow]);
    if (col.profile != null) profile += num_(row[col.profile]);
    if (col.url != null && expectAccount) {
      var m = String(row[col.url]).match(/@([A-Za-z0-9_.]+)/);
      if (m) handleCount[m[1]] = (handleCount[m[1]] || 0) + 1;
    }
  });

  // ハンドル照合：対象月行で最も多いハンドルが設定と違えば警告
  if (expectAccount && posts > 0) {
    var top = '', topN = 0;
    Object.keys(handleCount).forEach(function (h) { if (handleCount[h] > topN) { topN = handleCount[h]; top = h; } });
    if (top && top.toLowerCase() !== expectAccount.toLowerCase()) {
      handleWarn = '検出=' + top + ' / 設定=' + expectAccount;
    }
  }
  return { posts: posts, views: views, eng: eng, follow: follow, profile: profile, handleWarn: handleWarn };
}

/** "2026-05-28 ..." / Dateオブジェクト / "2026/05/28" → "2026-05" */
function parseYM_(v) {
  if (v == null || v === '') return '';
  if (Object.prototype.toString.call(v) === '[object Date]') {
    return v.getFullYear() + '-' + ('0' + (v.getMonth() + 1)).slice(-2);
  }
  var s = String(v).trim();
  var m = s.match(/^(\d{4})[-\/](\d{1,2})/);
  if (m) return m[1] + '-' + ('0' + m[2]).slice(-2);
  return '';
}

/** 数値化（カンマ・空白・％を除去） */
function num_(v) {
  if (v == null || v === '') return 0;
  if (typeof v === 'number') return v;
  var s = String(v).replace(/[,\s%％]/g, '');
  var n = parseFloat(s);
  return isNaN(n) ? 0 : n;
}

/** 集約タブへ出力（対象月の既存行は置換） */
function writeOutput_(ss, ym, rows) {
  var sh = ss.getSheetByName(OUTPUT_SHEET) || ss.insertSheet(OUTPUT_SHEET);
  var header = ['対象月', 'クライアント', 'アカウント', '投稿数', '再生数合計', '再生平均/本',
                'EG率%(対再生)', 'フォロワー増加', 'プロフ閲覧計', '状態', '警告', '更新日時'];
  if (sh.getLastRow() === 0) sh.appendRow(header);

  // 同一対象月の既存行を削除（再実行で重複しないように）
  var all = sh.getDataRange().getValues();
  for (var r = all.length - 1; r >= 1; r--) {
    if (String(all[r][0]) === ym) sh.deleteRow(r + 1);
  }
  var now = new Date();
  var buf = rows.map(function (x) {
    return [x.ym, x.name, x.account ? '@' + x.account : '', x.posts, x.views, x.avg,
            x.eg, x.follow, x.profile, x.status, x.warn, now];
  });
  if (buf.length) sh.getRange(sh.getLastRow() + 1, 1, buf.length, header.length).setValues(buf);
  sh.autoResizeColumns(1, header.length);
}

function writeLog_(ss, ym, rows) {
  var sh = ss.getSheetByName(LOG_SHEET) || ss.insertSheet(LOG_SHEET);
  var ok = rows.filter(function (r) { return r.status === 'OK'; }).length;
  var warn = rows.filter(function (r) { return r.warn; }).length;
  sh.appendRow([new Date(), ym, '対象' + rows.length + '社', 'OK' + ok + '社', '警告' + warn + '件']);
}
