/* Officer picker — type-to-search, pick, chip.
 *
 * The full roster is in the DOM as hidden checkboxes (so the form POSTs a plain
 * `officers` multi-value list and server-side validation is untouched). This
 * script only controls what is visible: typing filters the roster into a
 * suggestion dropdown, picking checks the box and renders a chip, and the chip's
 * × unchecks it. Idempotent and safe after HTMX swaps. */
(function () {
  var MAX_SUGGESTIONS = 12;

  function initPicker(panel) {
    if (panel.dataset.ofInit) return;
    panel.dataset.ofInit = '1';

    var q       = panel.querySelector('.of-picker-q');
    var store   = panel.querySelector('.of-picker-store');
    var box     = panel.querySelector('.of-suggest');
    var chosen  = panel.querySelector('.of-picker-chosen');
    var countEl = panel.querySelector('.of-picker-count');
    var clearBt = panel.querySelector('.of-clear');
    var hint    = panel.querySelector('.of-picker-hint');
    var i18nEl  = panel.querySelector('.of-i18n');
    if (!q || !store || !box) return;   // empty state (roster not synced yet)

    var i18n = {
      noMatch: i18nEl ? i18nEl.dataset.noMatch : 'No officers match.',
      retired: i18nEl ? i18nEl.dataset.retired : 'Retired',
      more:    i18nEl ? i18nEl.dataset.more    : 'Keep typing to narrow',
      remove:  i18nEl ? i18nEl.dataset.remove  : 'Remove'
    };

    var inputs  = Array.prototype.slice.call(store.querySelectorAll('input[type="checkbox"]'));
    var suffix  = countEl ? (countEl.dataset.suffix || '') : '';
    var active  = -1;   // highlighted suggestion index

    function selected() {
      return inputs.filter(function (i) { return i.checked; });
    }

    function renderChips() {
      var picked = selected();
      chosen.innerHTML = '';
      picked.forEach(function (input) {
        var chip = document.createElement('span');
        chip.className = 'of-chip' + (input.dataset.retired ? ' retired' : '');

        var label = document.createElement('span');
        label.className = 'of-chip-label';
        label.textContent = input.dataset.label;
        chip.appendChild(label);

        if (input.dataset.retired) {
          var tag = document.createElement('span');
          tag.className = 'of-chip-tag';
          tag.textContent = i18n.retired;
          chip.appendChild(tag);
        }

        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'of-chip-x';
        x.setAttribute('aria-label', i18n.remove + ': ' + input.dataset.label);
        x.innerHTML = '&times;';
        x.addEventListener('click', function () {
          input.checked = false;
          refresh();
          q.focus();
        });
        chip.appendChild(x);
        chosen.appendChild(chip);
      });

      if (countEl) countEl.textContent = picked.length + suffix;
      if (clearBt) clearBt.hidden = picked.length === 0;
      if (hint) hint.hidden = picked.length > 0;
    }

    function closeBox() {
      box.hidden = true;
      box.innerHTML = '';
      active = -1;
      q.setAttribute('aria-expanded', 'false');
    }

    function pick(input) {
      input.checked = true;
      q.value = '';
      closeBox();
      renderChips();
    }

    function highlight(delta) {
      var items = box.querySelectorAll('.of-suggest-item');
      if (!items.length) return;
      active = (active + delta + items.length) % items.length;
      items.forEach(function (el, i) { el.classList.toggle('active', i === active); });
      items[active].scrollIntoView({ block: 'nearest' });
    }

    function search() {
      var term = (q.value || '').trim().toLowerCase();
      if (!term) { closeBox(); return; }

      var hits = [];
      for (var i = 0; i < inputs.length && hits.length <= MAX_SUGGESTIONS; i++) {
        var input = inputs[i];
        if (input.checked) continue;                                  // already picked
        if (input.dataset.search.indexOf(term) === -1) continue;
        hits.push(input);
      }

      box.innerHTML = '';
      active = -1;

      if (!hits.length) {
        var empty = document.createElement('div');
        empty.className = 'of-suggest-empty';
        empty.textContent = i18n.noMatch;
        box.appendChild(empty);
      } else {
        hits.slice(0, MAX_SUGGESTIONS).forEach(function (input) {
          var btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'of-suggest-item';
          btn.setAttribute('role', 'option');

          var main = document.createElement('span');
          main.textContent = input.dataset.label;
          btn.appendChild(main);

          if (input.dataset.retired) {
            var tag = document.createElement('span');
            tag.className = 'of-chip-tag ms-1';
            tag.textContent = ' · ' + i18n.retired;
            btn.appendChild(tag);
          }
          if (input.dataset.office) {
            var sub = document.createElement('span');
            sub.className = 'of-sub';
            sub.textContent = input.dataset.office;
            btn.appendChild(sub);
          }

          btn.addEventListener('mousedown', function (e) {
            e.preventDefault();        // keep focus in the search box
            pick(input);
          });
          box.appendChild(btn);
        });

        if (hits.length > MAX_SUGGESTIONS) {
          var more = document.createElement('div');
          more.className = 'of-suggest-more';
          more.textContent = i18n.more;
          box.appendChild(more);
        }
      }

      box.hidden = false;
      q.setAttribute('aria-expanded', 'true');
    }

    function refresh() { renderChips(); }

    q.addEventListener('input', search);
    q.addEventListener('focus', function () { if (q.value.trim()) search(); });
    q.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown')      { e.preventDefault(); highlight(1); }
      else if (e.key === 'ArrowUp')   { e.preventDefault(); highlight(-1); }
      else if (e.key === 'Enter') {
        var items = box.querySelectorAll('.of-suggest-item');
        if (!box.hidden && items.length) {
          e.preventDefault();          // never submit the tour form from here
          items[active >= 0 ? active : 0].dispatchEvent(new MouseEvent('mousedown'));
        }
      } else if (e.key === 'Escape')  { closeBox(); }
    });

    document.addEventListener('click', function (e) {
      if (!panel.contains(e.target)) closeBox();
    });

    if (clearBt) clearBt.addEventListener('click', function () {
      inputs.forEach(function (i) { i.checked = false; });
      refresh();
      q.focus();
    });

    renderChips();
  }

  function initAll(root) {
    (root || document).querySelectorAll('.of-picker').forEach(initPicker);
  }

  if (document.readyState !== 'loading') initAll();
  else document.addEventListener('DOMContentLoaded', function () { initAll(); });

  document.addEventListener('htmx:afterSwap', function (e) { initAll(e.target); });
}());
