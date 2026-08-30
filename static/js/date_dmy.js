/* date_dmy.js — every date field reads and writes DD/MM/YYYY.
 *
 * A native <input type="date"> renders in the *browser's* locale, so a machine
 * set to en-US shows MM/DD/YYYY no matter what the server sends. flatpickr is
 * attached in altInput mode instead: the visible box is a text input formatted
 * d/m/Y, while the original input keeps the ISO Y-m-d value Django parses. The
 * original is switched to type=hidden by flatpickr, so the native picker (and
 * its locale-dependent format) never appears.
 *
 * Idempotent: already-enhanced inputs are skipped, so it is safe to re-run
 * after an htmx swap or when a hidden edit panel is revealed.
 */
(function () {
  'use strict';

  if (typeof flatpickr === 'undefined') return;

  var OPTS = {
    altInput: true,
    altFormat: 'd/m/Y',
    dateFormat: 'Y-m-d',
    allowInput: true,      // typing "25/12/1980" works, parsed with altFormat
    disableMobile: true,   // otherwise mobile browsers fall back to the native picker
  };

  function enhance(input) {
    if (input._flatpickr || input.dataset.dmyDone) return;
    input.dataset.dmyDone = '1';

    var opts = Object.assign({}, OPTS, {
      // Keep whatever sizing/validation classes the field already had
      // (form-control, form-control-sm, is-invalid …) on the visible box.
      altInputClass: input.className,
    });
    if (input.hasAttribute('min')) opts.minDate = input.getAttribute('min');
    if (input.hasAttribute('max')) opts.maxDate = input.getAttribute('max');

    flatpickr(input, opts);
  }

  function enhanceAll(root) {
    (root || document)
      .querySelectorAll('input[type="date"]:not([data-no-dmy])')
      .forEach(enhance);
  }

  document.addEventListener('DOMContentLoaded', function () { enhanceAll(); });

  // htmx-swapped fragments (master-data inline CRUD, education cascade, …).
  document.body.addEventListener('htmx:afterSwap', function (e) {
    enhanceAll(e.target);
  });

  // Bootstrap modals/tabs render their contents hidden; flatpickr copes with
  // that, but a panel injected later still needs a sweep.
  document.addEventListener('shown.bs.modal', function (e) { enhanceAll(e.target); });
  document.addEventListener('shown.bs.tab', function () { enhanceAll(); });

  // Expose for any page that builds rows itself.
  window.enhanceDateFields = enhanceAll;
}());
