/* SPDX-License-Identifier: GPL-3.0-only */
(() => {
  'use strict';
  const menu = document.querySelector('.site-menu');
  if (menu) {
    menu.dataset.enhanced = 'true';
    const small = matchMedia('(max-width: 760px)');
    const contents = document.querySelector('.wiki-contents');
    const resize = () => {
      menu.open = !small.matches;
      if (contents) contents.open = !small.matches;
    };
    resize();
    small.addEventListener('change', resize);
    menu.addEventListener('keydown', event => {
      if (event.key === 'Escape' && small.matches && menu.open) {
        menu.open = false;
        menu.querySelector('summary').focus();
      }
    });
  }
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey &&
        !event.target.closest('input, textarea, select, [contenteditable]') &&
        !document.querySelector('#wiki-search, input#search, #controls-search')) {
      event.preventDefault();
      location.href = 'index.html#search';
    }
  });
})();
