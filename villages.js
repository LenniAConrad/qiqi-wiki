// SPDX-License-Identifier: GPL-3.0-only
'use strict';
(() => {
  const gallery = window.VILLAGE_GALLERY;
  const shots = Array.isArray(gallery?.shots) ? gallery.shots : [];
  const $ = selector => document.querySelector(selector);
  const dialog = $('#detail');
  const sceneLabel = shot => shot.scene === 'generated' ? 'Generated world' : 'Inspection scene';
  const categoryLabel = category => String(category || 'Village').replace(/[-_]/g, ' ').replace(/^./, letter => letter.toLocaleUpperCase());
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  let category = null;
  let visible = [...shots];
  let browsing = [];
  let selectedId = null;
  let returnFocus = null;

  function setImage(image, shot) {
    image.src = shot.image;
    image.alt = `${shot.title}. ${shot.description}`;
    if (shot.width) image.width = shot.width;
    if (shot.height) image.height = shot.height;
  }

  function render() {
    visible = shots.filter(shot => category === null || shot.category === category);
    const fragment = document.createDocumentFragment();
    for (const shot of visible) {
      const article = el('article', 'card');
      article.dataset.shot = shot.id;
      const button = el('button', 'card-image');
      button.type = 'button';
      button.setAttribute('aria-label', `Open photograph: ${shot.title}`);
      const image = el('img');
      setImage(image, shot);
      image.loading = 'lazy';
      image.decoding = 'async';
      const arrow = el('span', 'image-open', '↗');
      arrow.setAttribute('aria-hidden', 'true');
      button.append(image, arrow);
      button.addEventListener('click', () => openShot(shot.id));
      const line = el('div', 'card-topline');
      line.append(el('span', '', categoryLabel(shot.category)), el('span', '', sceneLabel(shot)));
      article.append(button, line, el('h3', '', shot.title), el('p', '', shot.description));
      fragment.append(article);
    }
    $('#grid').replaceChildren(fragment);
    $('#result-count').textContent = shots.length
      ? `${visible.length} of ${shots.length} photographs`
      : 'The photographs could not be loaded. Reload this page to try again.';
    for (const button of $('#filters').children) {
      button.setAttribute('aria-pressed', String(button.dataset.category === (category ?? '')));
    }
  }

  function openShot(id) {
    const shot = shots.find(shot => shot.id === id);
    if (!shot) return;
    if (!dialog.open) {
      returnFocus = document.activeElement;
      browsing = visible.some(item => item.id === id) ? visible : shots;
    } else if (!browsing.some(item => item.id === id)) {
      browsing = shots;
    }
    selectedId = id;
    const list = browsing;
    setImage($('#detail-image'), shot);
    $('#detail-title').textContent = shot.title;
    $('#detail-category').textContent = categoryLabel(shot.category);
    $('#detail-number').textContent = `${list.findIndex(item => item.id === id) + 1} / ${list.length}`;
    $('#detail-description').textContent = shot.description;
    $('#detail-scene').textContent = shot.scene === 'generated'
      ? 'Generated world · Autumn Forest'
      : 'Inspection scene · authored village at X 0 · Z 0';
    $('#original-image').href = shot.image;
    $('#original-image').setAttribute('aria-label', `Open full-size photograph: ${shot.title}`);
    $('#previous').disabled = list.length < 2;
    $('#next').disabled = list.length < 2;
    if (!dialog.open) {
      dialog.showModal();
      document.body.classList.add('modal-open');
    }
    dialog.scrollTop = 0;
  }

  function navigate(direction) {
    const list = browsing;
    if (list.length < 2) return;
    const index = list.findIndex(shot => shot.id === selectedId);
    openShot(list[(index + direction + list.length) % list.length].id);
  }

  function followHash() {
    const id = new URLSearchParams(location.hash.slice(1)).get('shot');
    if (id) openShot(id);
  }

  for (const value of [null, ...new Set(shots.map(shot => shot.category))]) {
    if (value === undefined) continue;
    const button = el('button', '', value === null ? 'All photographs' : categoryLabel(value));
    button.type = 'button';
    button.dataset.category = value ?? '';
    button.addEventListener('click', () => { category = value; render(); });
    $('#filters').append(button);
  }
  $('#filters').hidden = shots.length === 0;
  $('#close-detail').addEventListener('click', () => dialog.close());
  $('#previous').addEventListener('click', () => navigate(-1));
  $('#next').addEventListener('click', () => navigate(1));
  dialog.addEventListener('close', () => {
    document.body.classList.remove('modal-open');
    if (returnFocus?.isConnected && returnFocus !== document.body) returnFocus.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  document.addEventListener('keydown', event => {
    if (!dialog.open || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      navigate(event.key === 'ArrowRight' ? 1 : -1);
    }
  });
  window.addEventListener('hashchange', followHash);

  if (gallery) {
    if (gallery.description) $('#village-description').textContent = gallery.description;
    $('#shot-count').textContent = String(shots.length);
    if (gallery.packVersion) $('#pack-version').textContent = `Jade Willow Village · ${gallery.packVersion}`;
    if (gallery.seed) $('#world-seed').textContent = String(gallery.seed);
    if (gallery.generatorVersion) $('#world-generation').textContent = `Use world generation ${gallery.generatorVersion}. Existing saved worlds keep their original generation.`;
    const date = new Date(gallery.capturedAt);
    if (Number.isFinite(date.getTime())) {
      const formatted = new Intl.DateTimeFormat('en', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(date);
      $('#capture-date').textContent = `Photographed ${formatted}.`;
    }
  }
  const hero = shots.find(shot => shot.id === 'lantern-court') || shots[0];
  if (hero) {
    setImage($('#hero-image'), hero);
    $('#hero-title').textContent = hero.title;
    $('#hero-category').textContent = categoryLabel(hero.category);
    $('#hero-scene').textContent = sceneLabel(hero);
    $('#open-hero').setAttribute('aria-label', `Open featured photograph: ${hero.title}`);
    $('#open-hero').addEventListener('click', () => openShot(hero.id));
    $('#village-hero').hidden = false;
  }
  render();
  followHash();
})();
