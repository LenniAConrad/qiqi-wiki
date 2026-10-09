// SPDX-License-Identifier: GPL-3.0-only
'use strict';
const atlas = window.ANIMAL_ATLAS;
const animals = atlas.animals;
const $ = s => document.querySelector(s);
for (const count of document.querySelectorAll('[data-animal-count]')) count.textContent = animals.length;
const dialog = $('#detail');
const search = $('#search');
const habitat = $('#habitat');
let group = 'All animals';
let visible = [];
let selectedId = null;
const groups = ['All animals', 'Mammals', 'Birds', 'Reptiles & amphibians', 'Fish', 'Invertebrates'];
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
for (const [id, name] of Object.entries(atlas.biomes).sort((a, b) => a[1].localeCompare(b[1]))) {
  const option = el('option', '', name); option.value = id; habitat.append(option);
}
const initialBiome = new URLSearchParams(location.search).get('biome');
if (Object.hasOwn(atlas.biomes, initialBiome)) habitat.value = initialBiome;
for (const name of groups) {
  const button = el('button', '', name); button.type = 'button';
  button.addEventListener('click', () => { group = name; render(); });
  $('#filters').append(button);
}
function render() {
  const words = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  visible = animals.filter(a => (group === 'All animals' || a.category === group)
    && (!habitat.value || a.habitats.includes(habitat.value))
    && words.every(word => `${a.name} ${a.description} ${a.category} ${a.habitats.map(id => atlas.biomes[id]).join(' ')}`.toLocaleLowerCase().includes(word)));
  for (const button of $('#filters').children) button.setAttribute('aria-pressed', String(button.textContent === group));
  const fragment = document.createDocumentFragment();
  for (const a of visible) {
    const article = el('article', 'card');
    const button = el('button', 'card-image'); button.type = 'button';
    button.setAttribute('aria-label', `Explore ${a.name}`);
    const image = el('img'); image.src = a.views[0].image; image.alt = `${a.name}, resting model in three-quarter view`;
    image.width = 512; image.height = 512; image.loading = 'lazy'; image.decoding = 'async';
    const arrow = el('span', 'image-open', '↗'); arrow.setAttribute('aria-hidden', 'true');
    button.append(image, arrow); button.addEventListener('click', () => openAnimal(a.id));
    const line = el('div', 'card-topline');
    line.append(el('span', '', a.category), el('span', '', `${a.habitats.length} ${a.habitats.length === 1 ? "habitat" : "habitats"}`));
    article.append(button, line, el('h3', '', a.name), el('p', '', a.description)); fragment.append(article);
  }
  $('#grid').replaceChildren(fragment);
  $('#result-count').textContent = `${visible.length} of ${animals.length} animals`;
  $('#empty').hidden = visible.length !== 0;
}
function selectView(index) {
  const a = animals.find(a => a.id === selectedId);
  const view = a.views[index];
  $('#detail-image').src = view.image;
  $('#detail-image').alt = `${a.name} — ${view.label}`;
  $('#original-image').href = view.image;
  [...$('#view-controls').children].forEach((button, i) => button.setAttribute('aria-pressed', String(i === index)));
}
function openAnimal(id) {
  const a = animals.find(a => a.id === id); if (!a) return;
  selectedId = id;
  $('#detail-title').textContent = a.name;
  $('#detail-category').textContent = a.category;
  $('#detail-number').textContent = `${animals.indexOf(a) + 1} / ${animals.length}`;
  $('#detail-description').textContent = a.description;
  const size = el('div');
  size.append(el('dt', '', 'Resting model · width × height × length'), el('dd', '', a.sizeMetres.map(n => `${Number(n.toPrecision(3))} m`).join(' × ')));
  $('#detail-size').replaceChildren(size);
  $('#detail-habitats').replaceChildren(...a.habitats.map(id => {
    const link = el('a', '', atlas.biomes[id]); link.href = `index.html#biome=${encodeURIComponent(id)}`; return link;
  }));
  $('#view-controls').replaceChildren(...a.views.map((view, i) => {
    const button = el('button', '', view.label); button.type = 'button';
    button.addEventListener('click', () => selectView(i)); return button;
  }));
  selectView(0);
  if (!dialog.open) { dialog.showModal(); document.body.classList.add('modal-open'); }
  dialog.scrollTop = 0;
}
function navigate(direction) {
  const list = visible.length && visible.some(a => a.id === selectedId) ? visible : animals;
  const i = list.findIndex(a => a.id === selectedId);
  openAnimal(list[(i + direction + list.length) % list.length].id);
}
search.addEventListener('input', render);
habitat.addEventListener('change', render);
$('#reset-filters').addEventListener('click', () => { search.value = ''; habitat.value = ''; group = 'All animals'; render(); search.focus(); });
$('#close-detail').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => document.body.classList.remove('modal-open'));
dialog.addEventListener('click', event => {
  if (event.target === dialog) {
    const r = dialog.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
  }
});
$('#previous').addEventListener('click', () => navigate(-1));
$('#next').addEventListener('click', () => navigate(1));
document.addEventListener('keydown', event => {
  if (dialog.open && ['ArrowRight', 'ArrowLeft'].includes(event.key)) { event.preventDefault(); navigate(event.key === 'ArrowRight' ? 1 : -1); }
  else if (event.key === '/' && !dialog.open && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) { event.preventDefault(); search.focus(); }
});
render();
