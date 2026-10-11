// SPDX-License-Identifier: GPL-3.0-only
'use strict';
// The ledger is complete static HTML; this only adds search and status filters.
(() => {
  const $ = selector => document.querySelector(selector);
  const search = $('#search');
  const filters = $('#filters');
  const count = $('#result-count');
  const empty = $('#empty');
  const features = [...document.querySelectorAll('.feature')];
  const areas = [...document.querySelectorAll('.ledger-area')];
  if (!search || !filters || !features.length) return;
  let status = '';

  function apply() {
    const terms = search.value.toLowerCase().split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const feature of features) {
      const haystack = feature.dataset.search || '';
      const match = (!status || feature.dataset.status === status) && terms.every(term => haystack.includes(term));
      feature.hidden = !match;
      if (match) shown += 1;
    }
    for (const area of areas) area.hidden = !area.querySelector('.feature:not([hidden])');
    for (const button of filters.querySelectorAll('button')) {
      button.setAttribute('aria-pressed', String(button.dataset.status === status));
    }
    count.textContent = `${shown} of ${features.length} features`;
    empty.hidden = shown > 0;
  }

  function reset() {
    search.value = '';
    status = '';
    apply();
  }

  // Reveal a linked feature even when the current filters would hide it.
  function revealTarget() {
    const target = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (target && (target.hidden || target.closest('[hidden]'))) {
      reset();
      target.scrollIntoView();
    }
  }

  filters.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button) return;
    status = button.dataset.status;
    apply();
  });
  search.addEventListener('input', apply);
  search.addEventListener('keydown', event => {
    if (event.key === 'Escape' && search.value) {
      event.preventDefault();
      search.value = '';
      apply();
    }
  });
  $('#reset-filters').addEventListener('click', () => {
    reset();
    search.focus();
  });
  document.addEventListener('keydown', event => {
    const typing = event.target instanceof Element
      && event.target.closest('input, textarea, select, [contenteditable="true"]');
    if (event.key === '/' && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      search.focus();
    }
  });
  window.addEventListener('hashchange', revealTarget);
  $('#ledger-tools').hidden = false;
  $('#ledger-filters-row').hidden = false;
  apply();
})();
