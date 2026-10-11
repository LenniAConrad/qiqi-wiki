// SPDX-License-Identifier: GPL-3.0-only
// Progressive enhancement for the controls reference: filters the generated
// tables by key, action or feature. Every row is present without this script.
(function () {
  "use strict";
  var tools = document.getElementById("controls-tools");
  var input = document.getElementById("controls-search");
  if (!tools || !input) { return; }
  var rows = Array.prototype.slice.call(document.querySelectorAll(".control-row"));
  var groups = Array.prototype.slice.call(document.querySelectorAll(".control-group"));
  var count = document.getElementById("controls-count");
  var empty = document.getElementById("controls-empty");
  tools.hidden = false;

  function apply() {
    var terms = input.value.toLowerCase().split(/\s+/).filter(Boolean);
    var shown = 0;
    rows.forEach(function (row) {
      var haystack = row.getAttribute("data-search") || "";
      var match = terms.every(function (term) { return haystack.indexOf(term) !== -1; });
      row.hidden = !match;
      if (match) { shown += 1; }
    });
    groups.forEach(function (group) {
      group.hidden = !group.querySelector(".control-row:not([hidden])");
    });
    count.textContent = terms.length ? shown + " of " + rows.length + " controls" : rows.length + " controls";
    empty.hidden = shown !== 0;
  }

  input.addEventListener("input", apply);
  document.addEventListener("keydown", function (event) {
    var target = event.target;
    var typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
    if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      input.focus();
    } else if (event.key === "Escape" && target === input && input.value) {
      input.value = "";
      apply();
    }
  });
  apply();
})();
