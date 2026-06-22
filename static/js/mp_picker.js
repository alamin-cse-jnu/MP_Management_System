/* MP picker — filterable checkbox panel.
 * Wires search, party/seat-type chips, "select all shown", clear, the live
 * count and the chosen-chip strip. Idempotent and safe to call repeatedly
 * (e.g. after HTMX swaps); each panel initialises once. */
(function () {
  function initPicker(panel) {
    if (panel.dataset.mpInit) return;
    panel.dataset.mpInit = '1';

    var q        = panel.querySelector('.mp-picker-q');
    var list     = panel.querySelector('.mp-picker-list');
    var items    = Array.prototype.slice.call(panel.querySelectorAll('.mp-picker-item'));
    var countEl  = panel.querySelector('.mp-picker-count');
    var chosenEl = panel.querySelector('.mp-picker-chosen');
    var emptyEl  = panel.querySelector('.mp-picker-empty');
    var suffix   = countEl ? (countEl.dataset.suffix || '') : '';
    var totalId  = countEl ? (countEl.dataset.totalInput || '') : '';
    var totalInp = totalId ? document.getElementById(totalId) : null;
    var activeParty = '';
    var activeType  = '';

    function matches(it) {
      if (activeParty && it.dataset.party !== activeParty) return false;
      if (activeType && it.dataset.type !== activeType) return false;
      var term = (q.value || '').trim().toLowerCase();
      if (term && it.dataset.search.indexOf(term) === -1) return false;
      return true;
    }

    function applyFilter() {
      var shown = 0;
      items.forEach(function (it) {
        var ok = matches(it);
        it.hidden = !ok;
        if (ok) shown++;
      });
      if (emptyEl) emptyEl.hidden = shown !== 0;
    }

    function checkedItems() {
      return items.filter(function (it) { return it.querySelector('input').checked; });
    }

    function refresh() {
      var checked = checkedItems();
      if (countEl) {
        var n = checked.length;
        var total = totalInp ? parseInt(totalInp.value, 10) : NaN;
        if (!isNaN(total) && total > 0) {
          countEl.textContent = n + ' / ' + total + suffix;
          countEl.classList.toggle('over', n > total);
        } else {
          countEl.textContent = n + suffix;
          countEl.classList.remove('over');
        }
      }
      items.forEach(function (it) {
        it.classList.toggle('checked', it.querySelector('input').checked);
      });
      // Rebuild chosen chips
      chosenEl.innerHTML = '';
      checked.forEach(function (it) {
        var chip = document.createElement('span');
        chip.className = 'mp-chosen-chip';
        var label = document.createElement('span');
        label.textContent = it.querySelector('.mp-picker-name').textContent;
        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'mp-chosen-x';
        x.setAttribute('aria-label', 'Remove');
        x.innerHTML = '&times;';
        x.addEventListener('click', function () {
          it.querySelector('input').checked = false;
          refresh();
        });
        chip.appendChild(label);
        chip.appendChild(x);
        chosenEl.appendChild(chip);
      });
    }

    if (q) q.addEventListener('input', applyFilter);
    if (totalInp) totalInp.addEventListener('input', refresh);

    panel.querySelectorAll('.mp-chip[data-party]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        activeParty = btn.dataset.party;
        panel.querySelectorAll('.mp-chip[data-party]').forEach(function (b) {
          b.classList.toggle('active', b === btn);
        });
        applyFilter();
      });
    });

    panel.querySelectorAll('.mp-chip[data-type]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        activeType = (activeType === btn.dataset.type) ? '' : btn.dataset.type;
        panel.querySelectorAll('.mp-chip[data-type]').forEach(function (b) {
          b.classList.toggle('active', b.dataset.type === activeType);
        });
        applyFilter();
      });
    });

    list.addEventListener('change', function (e) {
      if (e.target && e.target.matches('input[type="checkbox"]')) refresh();
    });

    var selectShown = panel.querySelector('.mp-select-shown');
    if (selectShown) selectShown.addEventListener('click', function () {
      items.forEach(function (it) {
        if (!it.hidden) it.querySelector('input').checked = true;
      });
      refresh();
    });

    var clearBtn = panel.querySelector('.mp-clear');
    if (clearBtn) clearBtn.addEventListener('click', function () {
      items.forEach(function (it) { it.querySelector('input').checked = false; });
      refresh();
    });

    applyFilter();
    refresh();
  }

  function initAll(root) {
    (root || document).querySelectorAll('.mp-picker').forEach(initPicker);
  }

  if (document.readyState !== 'loading') initAll();
  else document.addEventListener('DOMContentLoaded', function () { initAll(); });

  document.addEventListener('htmx:afterSwap', function (e) { initAll(e.target); });
})();
