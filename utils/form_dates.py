"""Date-widget normalisation — one place, every form.

Two separate things have to line up for a date field to work here:

1. **What the browser is handed.** A ``<input type="date">`` only understands an
   ISO ``YYYY-MM-DD`` value attribute. Django, however, renders a bound date
   with the *active locale's* first ``DATE_INPUT_FORMATS`` entry — ``%d/%m/%Y``
   under ``bn``. That value is rejected by the input, so an existing date
   silently renders as an empty box. Pinning ``widget.format`` to ISO fixes it,
   and it is also what ``static/js/date_dmy.js`` (flatpickr) parses.

2. **What the browser may post back.** ISO is what the enhanced field submits,
   but a typed ``25/12/1980`` must not be rejected either — hence the explicit
   ``input_formats`` list, which no longer depends on the active locale.

The user-visible format stays DD/MM/YYYY throughout; only the wire format is
ISO. See GOTCHAS in CLAUDE.md.
"""

from django import forms

ISO_DATE = '%Y-%m-%d'

# Accepted on POST, in priority order. Locale-independent on purpose: the same
# form must behave identically in Bangla and English mode.
DATE_INPUT_FORMATS = [ISO_DATE, '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y']


def normalize_date_fields(form):
    """Pin every date field on ``form`` to the ISO wire format.

    Call once at the end of a form's ``__init__`` (the Bootstrap mixins do).
    Safe to call on any form — non-date fields are left alone.
    """
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.DateTimeInput) or not isinstance(widget, forms.DateInput):
            continue
        widget.format = ISO_DATE
        # input_type, not attrs['type'] — a 'type' left in attrs is rendered
        # *in addition to* the widget's own type, producing a duplicate
        # attribute on every date input.
        widget.input_type = 'date'
        widget.attrs.pop('type', None)
        widget.attrs.setdefault('class', 'form-control')
        if isinstance(field, forms.DateField):
            field.input_formats = DATE_INPUT_FORMATS
