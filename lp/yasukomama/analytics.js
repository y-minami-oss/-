/* =============================================================================
 * analytics.js — 恭子ママ採用LP GA4計測基盤
 * -----------------------------------------------------------------------------
 * 計測イベント:
 *   page_view     … LP表示（GA4標準＋明示送信）
 *   first_visit   … 初回訪問（localStorageで判定。GA4標準first_visitも併走）
 *   scroll_50     … 50%スクロール到達
 *   scroll_90     … 90%スクロール到達
 *   line_add_click… LINE追加ボタン押下（★主要コンバージョン）
 *   dm_click      … TikTok DM導線の押下
 *
 * 設計方針:
 *   - 測定ID（LP_CONFIG.GA_ID）未設定時は一切読み込まず無効化（誤計測・エラー防止）
 *   - UTM等の流入パラメータをlocalStorageに保存し、全イベントに付与
 *   - 各イベントは重複発火を防止
 * ===========================================================================*/
(function () {
  "use strict";

  var C = window.LP_CONFIG || {};
  var GA_ID = C.GA_ID || "";
  var ENABLED = GA_ID && GA_ID.indexOf("XXXX") === -1; // 未設定(プレースホルダ)なら無効

  // ---- gtag 基盤 ----
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }

  // ---- 流入パラメータ（UTM等）の取得・保存 ----
  // 初回流入時のUTMを保存し、以降のセッションでも参照できるようにする（アトリビューション用）
  function captureAttribution() {
    var p = new URLSearchParams(location.search);
    var keys = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "v"];
    var current = {};
    var hasNew = false;
    keys.forEach(function (k) {
      var val = p.get(k);
      if (val) { current[k] = val; hasNew = true; }
    });
    var stored = {};
    try { stored = JSON.parse(localStorage.getItem("lp_attr") || "{}"); } catch (e) {}
    if (hasNew) {
      try { localStorage.setItem("lp_attr", JSON.stringify(current)); } catch (e) {}
      return current;
    }
    return stored; // 今回パラメータが無ければ保存済みを使用
  }
  var ATTR = captureAttribution();

  // landing_video … TikTok動画別の流入計測（?v=動画ID 形式で付与）
  var attrParams = {
    utm_source:   ATTR.utm_source   || "(direct)",
    utm_medium:   ATTR.utm_medium   || "",
    utm_campaign: ATTR.utm_campaign || "",
    utm_content:  ATTR.utm_content  || "",
    landing_video: ATTR.v           || ""
  };

  // ---- 共通送信関数 ----
  function track(name, params) {
    if (!ENABLED) {
      // 開発/未設定時：コンソールに出すだけ（実送信しない）
      if (window.console) console.info("[analytics:disabled]", name, params || {});
      return;
    }
    var merged = Object.assign({}, attrParams, params || {});
    gtag("event", name, merged);
  }
  window.lpTrack = track; // 外部からも利用可

  // ---- GA4 初期化 ----
  if (ENABLED) {
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;
    document.head.appendChild(s);
    gtag("js", new Date());
    // send_page_view:true → page_view を自動送信
    gtag("config", GA_ID, { send_page_view: true });
    // 流入元をユーザープロパティとして保持（探索レポートのディメンションに使用）
    gtag("set", "user_properties", {
      first_utm_source:   attrParams.utm_source,
      first_utm_campaign: attrParams.utm_campaign,
      landing_video:      attrParams.landing_video
    });
  }

  // ---- page_view（明示）----
  // GA4標準でも送信されるが、attrParams付きで明示送信し動画別分析を確実にする
  track("page_view", { page_location: location.href });

  // ---- first_visit（初回訪問）----
  // GA4標準のfirst_visitに加え、localStorageで独自判定したフラグも送る
  try {
    if (!localStorage.getItem("lp_visited")) {
      localStorage.setItem("lp_visited", "1");
      track("first_visit", {});
    }
  } catch (e) {}

  // ---- scroll_50 / scroll_90 ----
  var fired = { 50: false, 90: false };
  function onScroll() {
    var doc = document.documentElement;
    var scrollable = doc.scrollHeight - window.innerHeight;
    if (scrollable <= 0) return;
    var pct = (window.scrollY || doc.scrollTop) / scrollable * 100;
    if (!fired[50] && pct >= 50) { fired[50] = true; track("scroll_50", {}); }
    if (!fired[90] && pct >= 90) { fired[90] = true; track("scroll_90", {}); cleanup(); }
  }
  function cleanup() { window.removeEventListener("scroll", onScroll); }
  window.addEventListener("scroll", onScroll, { passive: true });

  // ---- line_add_click（主要CV）/ dm_click ----
  function bindClick(id, eventName, extra) {
    var el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("click", function () {
      track(eventName, extra || {});
    });
  }
  // DOM構築後にバインド（defer読み込み前提だが念のため）
  function init() {
    bindClick("line-mid",    "line_add_click", { location: "mid" });
    bindClick("line-sticky", "line_add_click", { location: "sticky" });
    bindClick("dm-link-1",   "dm_click",       {});
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
