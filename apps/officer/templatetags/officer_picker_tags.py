"""Template tag rendering the filterable officer checkbox-panel picker.

Deliberately emits the same ``.mp-picker`` markup as ``{% mp_picker %}`` so
``static/js/mp_picker.js`` and ``static/css/mp_picker.css`` drive it unchanged —
that JS is generic and treats its filter chips as optional.

**Type-to-search by request (2026-08-22):** no filter chips and no standing
list. The whole roster ships as hidden checkboxes (so the POSTed field and its
validation are unchanged) and `static/js/officer_picker.js` reveals matches as
the user types; picks become chips. Wing and office text feed the search index,
so typing a wing name still narrows the suggestions.

Usage::

    {% load officer_picker_tags %}
    {% officer_picker form.officers %}
"""
from django import template
from django.utils.translation import get_language

register = template.Library()


def _is_en():
    lang = get_language()
    return bool(lang and lang.startswith('en'))


@register.inclusion_tag('partials/_officer_picker.html')
def officer_picker(bound_field):
    field = bound_field.field
    is_en = _is_en()

    raw = bound_field.value()
    if raw is None:
        raw = []
    elif not isinstance(raw, (list, tuple, set)):
        raw = [raw]
    selected = {str(getattr(v, 'pk', v)) for v in raw}

    options = []
    wing_counts = {}
    retired_count = 0
    for obj in field.queryset:
        label = field.label_from_instance(obj)
        wing = (obj.wing_label_en if is_en else obj.wing_label_bn) or \
               (OTHER_WING_EN if is_en else OTHER_WING_BN)
        pk = str(obj.pk)
        wing_counts[wing] = wing_counts.get(wing, 0) + 1
        if not obj.is_active:
            retired_count += 1
        # Everything the search box should match on.
        search = ' '.join(filter(None, [
            obj.name_bn, obj.name_en, obj.prp_id,
            obj.designation_bn, obj.designation_en,
            obj.office_bn, obj.office_en, obj.wing_bn, obj.wing_en,
        ])).lower()
        options.append({
            'value':    pk,
            'label':    label,
            'office':   obj.office_line(is_en),
            'active':   obj.is_active,
            'checked':  pk in selected,
            'search':   search,
        })

    return {
        'name': bound_field.html_name,
        'options': options,
        'selected_count': len(selected),
        'errors': bound_field.errors,
        'is_en': is_en,
    }
