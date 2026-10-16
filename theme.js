/* SPDX-License-Identifier: GPL-3.0-only */
(() => {
  'use strict';
  const key = 'qiqi-theme';
  const root = document.documentElement;
  let choice = 'system';
  const valid = value => value === 'light' || value === 'dark' ? value : 'system';
  const apply = value => {
    choice = valid(value);
    if (choice === 'system') root.removeAttribute('data-theme');
    else root.dataset.theme = choice;
    const select = document.querySelector('#theme-choice');
    if (select) select.value = choice;
  };
  // Read before the page paints. Private/offline browsers may refuse storage;
  // the control still works for this page and CSS still follows the system.
  try { choice = valid(localStorage.getItem(key)); } catch (_) { /* No saved choice. */ }
  apply(choice);
  document.addEventListener('DOMContentLoaded', () => {
    const select = document.querySelector('#theme-choice');
    if (!select) return;
    select.value = choice;
    select.closest('.theme-choice').hidden = false;
    select.addEventListener('change', () => {
      apply(select.value);
      try {
        if (choice === 'system') localStorage.removeItem(key);
        else localStorage.setItem(key, choice);
      } catch (_) { /* Keep the current page's choice without storage. */ }
    });
  });
  addEventListener('storage', event => {
    if (event.key === key || event.key === null) apply(event.newValue);
  });
})();
