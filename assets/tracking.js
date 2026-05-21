/* ──────────────────────────────────────────────────────────────────────
   9Speak — Tracking module
   --------------------------------------------------------------------
   - Quản lý Google Tag Manager (GTM) cho 9Speak landing
   - Auto-attach event tracking cho CTA, form, FAQ
   - Auto-inject UTM params cho mọi link outbound tới 9speak.vn
   - Không can thiệp vào nội dung hiển thị

   Cài GTM ID thật:
     Đổi const GTM_ID dưới đây thành 'GTM-XXXXXXX' của bạn.
     Khi vẫn là placeholder, script sẽ no-op (không inject GTM) nhưng
     vẫn log event ra console nếu ?debug=1 trên URL.
   ────────────────────────────────────────────────────────────────── */

(function () {
  'use strict';

  // === CẤU HÌNH — đổi giá trị này khi có GTM ID thật ===
  var GTM_ID = 'GTM-XXXXXXX'; // <— placeholder, đổi khi đi production

  var PLACEHOLDER = 'GTM-XXXXXXX';
  var isProd = GTM_ID && GTM_ID !== PLACEHOLDER;
  var debug = /\bdebug=1\b/.test(window.location.search);

  // Page id từ pathname (vd index.html → "home", blog.html → "blog")
  var pageId = (function () {
    var p = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase();
    if (p === '' || p === 'index.html') return 'home';
    return p.replace(/\.html$/, '').replace(/[^a-z0-9_-]/g, '_');
  })();

  // === 1. GTM snippet (chỉ inject nếu có ID thật) ===
  window.dataLayer = window.dataLayer || [];

  function gtmPush(payload) {
    window.dataLayer.push(payload);
    if (debug || !isProd) {
      // eslint-disable-next-line no-console
      console.log('[track]', payload);
    }
  }

  if (isProd) {
    (function (w, d, s, l, i) {
      w[l] = w[l] || [];
      w[l].push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
      var f = d.getElementsByTagName(s)[0],
        j = d.createElement(s),
        dl = l !== 'dataLayer' ? '&l=' + l : '';
      j.async = true;
      j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl;
      f.parentNode.insertBefore(j, f);
    })(window, document, 'script', 'dataLayer', GTM_ID);
  }

  // === 2. Helper public ===
  window.track = function (event, params) {
    var payload = Object.assign({ event: event, page_id: pageId }, params || {});
    gtmPush(payload);
  };

  // === 3. Auto-attach event listener khi DOM ready ===
  function onReady(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  function ctaContext(el) {
    var section = el.closest('section, .final-cta, .sticky-cta, footer, nav');
    var sid = section && (section.id || section.tagName.toLowerCase());
    var text = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60);
    return { cta_section: sid || 'unknown', cta_text: text, cta_href: el.href || '' };
  }

  function attachCtaTracking() {
    document.querySelectorAll('a.btn, a.price-cta, .sticky-cta a').forEach(function (a) {
      if (a.dataset.trackBound) return;
      a.dataset.trackBound = '1';
      a.addEventListener('click', function () {
        window.track('cta_click', ctaContext(a));
      });
    });
  }

  function attachFormTracking() {
    document.querySelectorAll('form').forEach(function (form) {
      if (form.dataset.trackBound) return;
      form.dataset.trackBound = '1';
      form.addEventListener('submit', function () {
        window.track('form_submit_attempt', { form_id: form.id || 'unknown' });
      });
    });
  }

  function attachFaqTracking() {
    document.querySelectorAll('.faq-question').forEach(function (q) {
      if (q.dataset.trackBound) return;
      q.dataset.trackBound = '1';
      q.addEventListener('click', function () {
        var item = q.parentElement;
        var wasOpen = item.classList.contains('open');
        // Click sẽ toggle — log trạng thái sẽ chuyển sang
        if (!wasOpen) {
          var qText = (q.textContent || '').trim().slice(0, 120);
          window.track('faq_open', { faq_question: qText });
        }
      });
    });
  }

  // === 4. UTM injection cho link outbound 9speak.vn ===
  function injectUtm() {
    document.querySelectorAll('a[href^="https://9speak.vn"]').forEach(function (a) {
      try {
        var url = new URL(a.href);
        // Không động vào link đã có utm_* sẵn
        if (Array.from(url.searchParams.keys()).some(function (k) { return k.indexOf('utm_') === 0; })) return;
        var section = a.closest('section, .sticky-cta, footer, nav');
        var sid = (section && (section.id || section.className.split(' ')[0])) || 'misc';
        url.searchParams.set('utm_source', 'landing');
        url.searchParams.set('utm_medium', pageId);
        url.searchParams.set('utm_campaign', sid);
        a.href = url.toString();
      } catch (e) { /* link không hợp lệ — bỏ qua */ }
    });
  }

  // === 5. Scroll depth (25/50/75/100%) ===
  function attachScrollDepth() {
    var marks = [25, 50, 75, 100];
    var fired = {};
    var doc = document.documentElement;
    function check() {
      var top = window.scrollY || doc.scrollTop;
      var height = doc.scrollHeight - doc.clientHeight;
      if (height <= 0) return;
      var pct = Math.min(100, Math.round((top / height) * 100));
      marks.forEach(function (m) {
        if (pct >= m && !fired[m]) {
          fired[m] = true;
          window.track('scroll_depth', { percent: m });
        }
      });
    }
    window.addEventListener('scroll', check, { passive: true });
  }

  onReady(function () {
    attachCtaTracking();
    attachFormTracking();
    attachFaqTracking();
    injectUtm();
    attachScrollDepth();
    window.track('page_view', { page_id: pageId, page_path: window.location.pathname });

    // Khi blog/faq pre-rendered, FAQ items có thể được hydrate lại từ JS;
    // chạy lại tracking sau 1 tick để bắt các phần tử mới render
    setTimeout(function () {
      attachCtaTracking();
      attachFaqTracking();
      injectUtm();
    }, 400);
  });
})();
