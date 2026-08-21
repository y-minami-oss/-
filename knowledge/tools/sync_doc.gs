/**
 * 社内ノウハウ抽出 → Googleドキュメント 同期スクリプト
 *
 * GitHub から本文データ（JSON）を取得し、
 * このスクリプトが紐づいているドキュメントの本文を丸ごと書き換える。
 *
 * 【初回セットアップ】
 *   1. 対象のドキュメントを開く
 *   2. 拡張機能 → Apps Script
 *   3. このファイルの中身をすべて貼り付けて保存
 *   4. リポジトリが非公開の場合は setToken を実行してトークンを保存する（下記参照）
 *   5. 関数 syncNow を選んで実行（初回だけ権限の承認を求められる）
 *   6. 関数 installWeeklyTrigger を実行 → 毎週日曜23時（日本時間）に自動更新される
 *
 * 【非公開リポジトリから取得する場合】
 *   GitHub で fine-grained personal access token を発行する
 *     - リポジトリ：y-minami-oss/- のみ
 *     - 権限：Contents = Read-only
 *   Apps Script のエディタで setToken を開き、TOKEN の中身を書き換えて1回だけ実行する。
 *   トークンはスクリプトプロパティに保存され、コードには残らない。
 *   実行後は setToken の中の文字列を消して保存し直すこと。
 *
 * 【注意】実行のたびに本文は全置換される。ドキュメントに直接書いた内容は消える。
 *         メモを残したい場合はコメント機能を使うか、別ドキュメントに書くこと。
 */

var OWNER  = 'y-minami-oss';
var REPO   = '-';
var BRANCH = 'claude/internal-knowledge-extraction-8s4sca';
var PATH   = 'knowledge/docs/google_doc_body.json';

/** トークンを保存する。実行後は中の文字列を消しておくこと。 */
function setToken() {
  var TOKEN = 'ここにトークンを貼る';
  PropertiesService.getScriptProperties().setProperty('GITHUB_TOKEN', TOKEN);
  Logger.log('トークンを保存しました。この関数の中の文字列を消して保存し直してください。');
}

/** 保存したトークンを消す。 */
function clearToken() {
  PropertiesService.getScriptProperties().deleteProperty('GITHUB_TOKEN');
  Logger.log('トークンを削除しました。');
}

/** 毎週日曜23時（日本時間）のトリガーを仕掛ける。二重登録はしない。 */
function installWeeklyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncNow') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('syncNow')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.SUNDAY)
    .atHour(23)
    .inTimezone('Asia/Tokyo')
    .create();
  Logger.log('毎週日曜23:00（JST）の自動更新を設定しました。');
}

/** トリガーを解除する。 */
function removeWeeklyTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'syncNow') ScriptApp.deleteTrigger(t);
  });
  Logger.log('自動更新を解除しました。');
}

/** 本文データを取る。トークンがあればAPI経由（非公開リポジトリ可）、無ければ公開rawから。 */
function fetchPayload_() {
  var token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  var url, opts = { muteHttpExceptions: true };

  if (token) {
    url = 'https://api.github.com/repos/' + OWNER + '/' + REPO +
          '/contents/' + encodeURI(PATH) + '?ref=' + encodeURIComponent(BRANCH);
    opts.headers = {
      Authorization: 'Bearer ' + token,
      Accept: 'application/vnd.github.raw'
    };
  } else {
    url = 'https://raw.githubusercontent.com/' + OWNER + '/' + REPO + '/' +
          BRANCH + '/' + encodeURI(PATH);
  }

  var res = UrlFetchApp.fetch(url, opts);
  var code = res.getResponseCode();
  if (code === 404 && !token) {
    throw new Error('404。リポジトリを非公開にした場合は setToken でトークンを保存してください。');
  }
  if (code !== 200) {
    throw new Error('取得に失敗しました（HTTP ' + code + '）: ' + url);
  }
  return JSON.parse(res.getContentText());
}

/** 本体。取得 → 本文を全置換。 */
function syncNow() {
  var items = fetchPayload_();

  var body = DocumentApp.getActiveDocument().getBody();
  body.clear();

  var HEADING = {
    h1: DocumentApp.ParagraphHeading.HEADING1,
    h2: DocumentApp.ParagraphHeading.HEADING2,
    h3: DocumentApp.ParagraphHeading.HEADING3,
    h4: DocumentApp.ParagraphHeading.HEADING4
  };

  for (var i = 0; i < items.length; i++) {
    var it = items[i];

    if (it.s === 'hr') {
      body.appendHorizontalRule();
      continue;
    }

    var el;
    if (it.s === 'li') {
      el = body.appendListItem(it.t).setGlyphType(DocumentApp.GlyphType.BULLET);
      if (it.i) el.setNestingLevel(Math.min(it.i, 3));
    } else if (it.s === 'nli') {
      el = body.appendListItem(it.t).setGlyphType(DocumentApp.GlyphType.NUMBER);
      if (it.i) el.setNestingLevel(Math.min(it.i, 3));
    } else {
      el = body.appendParagraph(it.t);
      if (HEADING[it.s]) el.setHeading(HEADING[it.s]);
    }

    var text = el.editAsText();

    if (it.s === 'q') {
      el.setIndentStart(28).setIndentFirstLine(28);
      if (it.t.length) text.setForegroundColor(0, it.t.length - 1, '#5B6764');
    } else if (it.s === 'th') {
      if (it.t.length) text.setBold(0, it.t.length - 1, true);
    } else if (it.s === 'tr') {
      el.setIndentStart(14);
    }

    if (it.b) {
      for (var j = 0; j < it.b.length; j++) {
        var s = it.b[j][0], e = it.b[j][1] - 1;
        if (e >= s && e < it.t.length) text.setBold(s, e, true);
      }
    }
  }

  body.appendParagraph('')
      .appendText('最終同期：' + Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm'))
      .setForegroundColor('#5B6764');

  Logger.log('同期しました：' + items.length + ' 段落');
}
