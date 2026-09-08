/* The "ALL" value on a report filter.
 *
 * Every multi-select filter on the report pages carries one synthetic option,
 * `__all__`, rendered as "সব (ALL)". Picking it means "every option in this
 * dropdown" and is submitted as that single value, so:
 *
 *   - the field shows ONE chip instead of 348 names, and
 *   - the URL carries one value instead of 348. That is not cosmetic: a
 *     fully-ticked MP picker used to put ~5.8 KB on the request line and
 *     gunicorn refused the request outright ("Request Line is too large
 *     (5798 > 4094)"), so the user got a bare 400 page instead of a report.
 *
 * The server expands `__all__` back to that filter's full id list — see
 * ALL_SENTINEL / _ids() in apps/reports/views.py. Expanding is not the same as
 * dropping the filter: these filters cross a relation, so "every district"
 * still excludes an MP with no constituency while "no district filter" keeps
 * them.
 *
 * Three rules, all handled here:
 *   1. ALL is exclusive — picking it clears the individual values, and picking
 *      an individual value clears ALL.
 *   2. The "সব / All" button selects ALL rather than every option.
 *   3. On submit, a selection that happens to cover every option collapses to
 *      ALL, so hand-picking all of them cannot rebuild the 5.8 KB URL.
 *
 * Select2 fires jQuery events, not native ones, so the change handler is bound
 * through jQuery — a native addEventListener never sees a Select2 selection.
 */
(function () {
  var SENTINEL = '__all__';

  function pickers() {
    return Array.prototype.filter.call(
      document.querySelectorAll('select[multiple][name]'),
      function (sel) { return !!sel.querySelector('option[value="' + SENTINEL + '"]'); });
  }

  function values(sel) {
    return Array.prototype.map.call(sel.selectedOptions, function (o) { return o.value; });
  }

  function bindExclusive(sel) {
    var prev = values(sel);
    $(sel).on('change', function () {
      var cur = values(sel);
      var hasAll = cur.indexOf(SENTINEL) !== -1;
      if (!hasAll) { prev = cur; return; }
      var justPicked = prev.indexOf(SENTINEL) === -1;
      var next = (justPicked || cur.length === 1)
        ? [SENTINEL]                                    // ALL wins
        : cur.filter(function (v) { return v !== SENTINEL; });  // something else wins
      prev = next;
      if (next.length !== cur.length) {
        $(sel).val(next).trigger('change.select2');
      }
    });
  }

  // A selection covering every real option means the same as ALL — send ALL.
  function collapse(form) {
    var undo = [];
    pickers().forEach(function (sel) {
      if (sel.form !== form) return;
      var opts = Array.prototype.filter.call(
        sel.options, function (o) { return o.value !== SENTINEL; });
      if (!opts.length) return;
      var picked = values(sel);
      var isAll = picked.indexOf(SENTINEL) !== -1
        || opts.every(function (o) { return o.selected; });
      if (!isAll || (picked.length === 1 && picked[0] === SENTINEL)) return;
      var hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = sel.name;
      hidden.value = SENTINEL;
      // A disabled control is not submitted, so the individual values drop out
      // while the select keeps its selection for the rest of the page's life.
      sel.disabled = true;
      form.appendChild(hidden);
      undo.push(function () { sel.disabled = false; hidden.remove(); });
    });
    // Serialisation runs synchronously once the submit handlers return, so by
    // the time this fires the request is already built: the select never blinks
    // and Back/bfcache restores a working picker.
    if (undo.length) {
      setTimeout(function () { undo.forEach(function (fn) { fn(); }); }, 0);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var forms = [];
    pickers().forEach(function (sel) {
      bindExclusive(sel);
      if (sel.form && forms.indexOf(sel.form) === -1) forms.push(sel.form);
    });
    forms.forEach(function (form) {
      form.addEventListener('submit', function () { collapse(form); });
    });
    // "সব / All" picks the ALL value instead of ticking every option.
    document.querySelectorAll('.select-all-btn[data-target]').forEach(function (btn) {
      var sel = document.querySelector('select[name="' + btn.dataset.target + '"]');
      if (!sel || !sel.querySelector('option[value="' + SENTINEL + '"]')) return;
      btn.addEventListener('click', function () {
        $(sel).val([SENTINEL]).trigger('change');
      });
    });
  });
})();
