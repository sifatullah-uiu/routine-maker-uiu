/* Presentation-only enhancements. Course and routine state stay in the original engine. */
(function () {
  'use strict';
  var paths = {
    calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4m10-4v4M3 11h18m-13 4h2m4 0h2m-8 3h2"/>',
    home: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 11h18"/>',
    table: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18M3 15h18M9 3v18"/>',
    book: '<path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1zm0 0v15"/>',
    sliders: '<path d="M4 6h5m4 0h7M4 12h10m4 0h2M4 18h2m4 0h10"/><circle cx="11" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="8" cy="18" r="2"/>',
    layers: '<path d="m12 3 10 5-10 5L2 8zM2 12l10 5 10-5M2 16l10 5 10-5"/>',
    arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    chevron: '<path d="m9 5 7 7-7 7"/>',
    upload: '<path d="M12 16V3m-5 5 5-5 5 5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
    edit: '<path d="m15 4 5 5M4 20l5-1L21 7a2 2 0 0 0-5-5L4 14z"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    shield: '<path d="M12 2 3 6v6c0 5 9 10 9 10s9-5 9-10V6z"/><path d="m8 12 3 3 5-6"/>',
    help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4.2 1.8c-1.2.6-1.7 1.2-1.7 2.2m0 3h.01"/>',
    bulb: '<path d="M9 18h6m-5 3h4M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 2H9s0-1-1-2"/>',
    heart: '<path d="M20 4a5 5 0 0 0-8 2 5 5 0 0 0-8-2c-5 4 0 10 8 16 8-6 13-12 8-16z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
    sunrise: '<path d="M3 18h18M5 21h14M7 15a5 5 0 1 1 10 0M12 2v3M3 7l2 2m14 0 2-2"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    coffee: '<path d="M4 8h12v9a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4zM16 9h2a3 3 0 0 1 0 6h-2M7 2v3m4-3v3"/>',
    search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>'
  };
  document.querySelectorAll('.pref-emoji').forEach(function (el) {
    var card = el.closest('.pref-card');
    if (!card) return;
    var kind = card.dataset.type, value = card.dataset.val;
    if (kind === 'days' && value !== '0') {
      el.textContent = value;
      el.classList.add('pref-day-number');
      return;
    }
    var icon = kind === 'days' ? 'calendar'
      : kind === 'time' ? { any: 'clock', morning: 'sunrise', afternoon: 'sun' }[value]
      : { gap: 'coffee', time: 'target', both: 'sliders' }[value];
    if (icon) el.dataset.icon = icon;
  });
  document.querySelectorAll('.search-icon').forEach(function (el) { el.dataset.icon = 'search'; });
  document.querySelectorAll('[data-icon]').forEach(function (el) {
    if (paths[el.dataset.icon]) {
      el.classList.add('ui-icon');
      el.setAttribute('aria-hidden', 'true');
      el.innerHTML = '<svg viewBox="0 0 24 24" focusable="false">' + paths[el.dataset.icon] + '</svg>';
    }
  });
  var pageNames = { upload: 'Get started', review: 'Review data', select: 'Choose courses', prefs: 'Preferences', results: 'Your routines' };
  function syncPage(page) {
    var crumb = document.getElementById('current-page-label');
    if (crumb) crumb.textContent = pageNames[page] || pageNames.upload;
    document.querySelectorAll('.nav-item').forEach(function (el) {
      if (el.dataset.page === page) el.setAttribute('aria-current', 'step');
      else el.removeAttribute('aria-current');
    });
  }
  document.addEventListener('pageChanged', function (event) { syncPage(event.detail); });
  syncPage('upload');
  var nextButton = document.getElementById('to-prefs-btn');
  var summaryNextButton = document.getElementById('selection-continue');
  if (nextButton && summaryNextButton) {
    function syncNextButton() { summaryNextButton.disabled = nextButton.disabled; }
    summaryNextButton.addEventListener('click', function () { nextButton.click(); });
    new MutationObserver(syncNextButton).observe(nextButton, { attributes: true, attributeFilter: ['disabled'] });
    syncNextButton();
  }
  // The whole alternative source card is clickable; its button remains the keyboard target.
  ['upload-sec-card', 'upload-sec-manual'].forEach(function (id) {
    var card = document.getElementById(id);
    if (!card) return;
    card.addEventListener('click', function (event) {
      if (event.target.closest('button, input')) return;
      var button = card.querySelector('button');
      if (button) button.click();
    });
  });
  var themeSwitch = document.getElementById('theme-tog');
  function syncTheme() {
    var dark = document.body.dataset.theme === 'dark';
    if (themeSwitch) themeSwitch.setAttribute('aria-checked', String(dark));
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = dark ? '#191e26' : '#f6f5f1';
  }
  new MutationObserver(syncTheme).observe(document.body, { attributes: true, attributeFilter: ['data-theme'] });
  syncTheme();
  // An immediate pointer with a quiet hover ring; native text/resize controls
  // and touch input retain their usual cursor behavior.
  var finePointer = matchMedia('(hover: hover) and (pointer: fine)');
  var cursor = document.createElement('div');
  cursor.className = 'planner-cursor';
  cursor.setAttribute('aria-hidden', 'true');
  cursor.innerHTML = '<span class="cursor-ring"></span><span class="cursor-dot"></span>';
  document.body.appendChild(cursor);
  var cursorFrame = 0, pointerX = 0, pointerY = 0;
  function hideCursor() {
    document.documentElement.classList.remove('custom-cursor-active');
    cursor.classList.remove('is-visible', 'is-pressed');
  }
  document.addEventListener('pointermove', function(event) {
    if (!finePointer.matches || event.pointerType !== 'mouse' ||
        event.target.closest('input, textarea, select, [contenteditable], :disabled, [aria-disabled="true"]')) {
      hideCursor(); return;
    }
    pointerX = event.clientX; pointerY = event.clientY;
    cursor.classList.toggle('is-interactive', !!event.target.closest('a, button, summary, label, [role="button"], [role="radio"], [role="switch"], .ht-block'));
    if (!cursorFrame) cursorFrame = requestAnimationFrame(function() {
      cursor.style.transform = 'translate3d(' + pointerX + 'px,' + pointerY + 'px,0)';
      cursorFrame = 0;
    });
    cursor.classList.add('is-visible');
    document.documentElement.classList.add('custom-cursor-active');
  }, {passive:true});
  document.addEventListener('pointerdown', function(event) {
    if (event.pointerType === 'mouse') cursor.classList.add('is-pressed');
    else hideCursor();
  }, {passive:true});
  document.addEventListener('pointerup', function() { cursor.classList.remove('is-pressed'); }, {passive:true});
  document.addEventListener('pointerout', function(event) { if (!event.relatedTarget) hideCursor(); });
  document.addEventListener('keydown', hideCursor);
  document.addEventListener('visibilitychange', hideCursor);
  window.addEventListener('blur', hideCursor);
  finePointer.addEventListener('change', hideCursor);
  var main = document.getElementById('main');
  var backToTop = document.getElementById('back-to-top');
  if (main && backToTop) {
    function syncBackToTop() { backToTop.hidden = main.scrollTop < 400; }
    main.addEventListener('scroll', syncBackToTop, {passive: true});
    document.addEventListener('pageChanged', syncBackToTop);
    backToTop.addEventListener('click', function () {
      main.scrollTo({top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    });
    syncBackToTop();
  }
})();
