/* =============================================================================
 * ui.js — UI体験レイヤー（計測とは分離）
 *   - スクロール・リビール（IntersectionObserver、段階表示）
 *   - グラス・アップバーのスクロール出現
 *   - prefers-reduced-motion を尊重（動きを無効化）
 * ===========================================================================*/
(function () {
  "use strict";
  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function ready(fn) {
    if (document.readyState === "loading")
      document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  ready(function () {
    /* ---- 1. スクロール・リビール ---- */
    // 主要ブロックに data-reveal を付与（HTMLを汚さずJSで適用）
    var sel = [
      ".hero .eyebrow", ".hero h1", ".hero .lead", ".benefits", ".hero .cta",
      ".concept p", ".proof", ".sec-label", ".sec-title", ".sec-sub",
      ".term", ".voice", ".step", "details", "section > .cta", ".frame",
      ".info .mono", ".info .addr", ".info .kpi", ".info .warn"
    ].join(",");
    var nodes = Array.prototype.slice.call(document.querySelectorAll(sel));

    if (reduce || !("IntersectionObserver" in window)) {
      // モーション無効環境：即表示（属性を付けない）
      return;
    }

    nodes.forEach(function (el) { el.setAttribute("data-reveal", ""); });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        // 同一グループ内での軽いスタッガー（隣接順にディレイ）
        var sibs = el.parentNode ? el.parentNode.children : [el];
        var idx = Array.prototype.indexOf.call(sibs, el);
        el.style.transitionDelay = Math.min(idx, 6) * 60 + "ms";
        el.classList.add("in");
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });

    nodes.forEach(function (el) { io.observe(el); });

    /* ---- 2. グラス・アップバー出現（ヒーローを過ぎたら） ---- */
    var bar = document.getElementById("appbar");
    var hero = document.querySelector(".hero");
    if (bar && hero) {
      var trigger = hero.offsetTop + hero.offsetHeight * 0.6;
      var onScroll = function () {
        if ((window.scrollY || document.documentElement.scrollTop) > trigger)
          bar.classList.add("show");
        else bar.classList.remove("show");
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }
  });
})();
