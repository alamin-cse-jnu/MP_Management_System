/* Passport-number rows on the foreign-tour form.

   The NOC prints the MP's passport number, and it is frequently still blank on
   the profile when a tour is entered. This panel shows one input per MP ticked
   in the participant picker, prefilled from the profile where one exists, and
   the view writes non-empty values back to `MP.passport_number` on save.

   Deliberately standalone: `static/js/mp_picker.js` and
   `partials/_mp_picker.html` are shared with committee step-1 and the
   institution bulk form, so this only *listens* to the picker's checkboxes and
   changes nothing about it.  Class prefix `.tp-`. */
(function () {
  'use strict';

  function init(panel) {
    if (!panel || panel.dataset.tpReady === '1') return;

    var pickerName = panel.dataset.pickerName || 'mps';
    var rowsBox = panel.querySelector('.tp-rows');
    var emptyBox = panel.querySelector('.tp-empty');
    if (!rowsBox) return;

    var data = {};
    try {
      data = JSON.parse(panel.dataset.passports || '{}');
    } catch (err) {
      console.error('[tour-passports] bad passport map:', err);
    }

    var labelProfile = panel.dataset.labelProfile || 'from profile';
    var labelNew = panel.dataset.labelNew || 'new';
    var placeholder = panel.dataset.placeholder || 'Passport No.';

    // Values the operator has typed this session, so a row that is unticked and
    // re-ticked doesn't lose the number.
    var typed = {};

    function boxes() {
      return Array.prototype.slice.call(
        document.querySelectorAll('input[type="checkbox"][name="' + pickerName + '"]'));
    }

    function nameFor(box) {
      var label = box.closest('label');
      var span = label ? label.querySelector('.mp-picker-name') : null;
      return (span ? span.textContent : (label ? label.textContent : '')).trim();
    }

    function render() {
      var checked = boxes().filter(function (b) { return b.checked; });

      // Keep whatever is already typed before rebuilding.
      Array.prototype.forEach.call(rowsBox.querySelectorAll('input[data-mp]'), function (input) {
        typed[input.dataset.mp] = input.value;
      });

      rowsBox.textContent = '';
      if (!checked.length) {
        if (emptyBox) emptyBox.style.display = '';
        return;
      }
      if (emptyBox) emptyBox.style.display = 'none';

      checked.forEach(function (box) {
        var pk = box.value;
        var info = data[pk] || { value: '', from_profile: false };
        var value = (pk in typed) ? typed[pk] : (info.value || '');

        var row = document.createElement('div');
        row.className = 'tp-row';

        var who = document.createElement('div');
        who.className = 'tp-who';
        who.textContent = nameFor(box);

        var wrap = document.createElement('div');
        wrap.className = 'tp-input';

        var input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm';
        input.name = 'passport_' + pk;
        input.value = value;
        input.placeholder = placeholder;
        input.maxLength = 30;
        input.autocomplete = 'off';
        input.dataset.mp = pk;

        var tag = document.createElement('span');
        tag.className = 'tp-tag' + (info.from_profile ? ' tp-tag-profile' : ' tp-tag-new');
        tag.textContent = info.from_profile ? labelProfile : labelNew;

        input.addEventListener('input', function () {
          typed[pk] = input.value;
        });

        wrap.appendChild(input);
        wrap.appendChild(tag);
        row.appendChild(who);
        row.appendChild(wrap);
        rowsBox.appendChild(row);
      });
    }

    // One delegated listener: the picker rewrites its list as you search, so
    // binding each checkbox individually would go stale.
    document.addEventListener('change', function (event) {
      var target = event.target;
      if (target && target.name === pickerName && target.type === 'checkbox') {
        render();
      }
    });

    panel.dataset.tpReady = '1';
    render();
  }

  function boot() {
    init(document.getElementById('tour-passports'));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  // The tour form is a normal page, but stay safe if it is ever HTMX-swapped.
  document.body && document.body.addEventListener('htmx:afterSwap', boot);
}());
