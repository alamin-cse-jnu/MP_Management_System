"""Template tag that renders the filterable MP checkbox-panel picker.

Replaces a bare ``{{ form.mps }}`` (an ``MPMultipleChoiceField``) with a
searchable, party/seat-type-filterable checkbox panel. The field keeps its
normal name/values, so form validation and cleaning are unchanged — only the
rendering differs.

Usage in a template::

    {% load mp_picker_tags %}
    {% mp_picker form.mps %}

Pass ``total_field`` (another bound field, e.g. a "total members" guide) to
show the live count as "X / Y selected", reconciled as that input changes::

    {% mp_picker form.mps form.total_count %}
"""
from django import template
from django.utils.translation import get_language

register = template.Library()


def _is_en():
    lang = get_language()
    return bool(lang and lang.startswith('en'))


@register.inclusion_tag('partials/_mp_picker.html')
def mp_picker(bound_field, total_field=None):
    field = bound_field.field
    qs = field.queryset
    is_en = _is_en()

    # Selected pks from the bound value (model instances on initial, raw
    # strings on a re-rendered POST).
    raw = bound_field.value()
    if raw is None:
        raw = []
    elif not isinstance(raw, (list, tuple, set)):
        raw = [raw]
    selected = {str(getattr(v, 'pk', v)) for v in raw}

    options = []
    party_counts = {}
    for obj in qs:
        label = field.label_from_instance(obj)
        p_bn = getattr(obj, '_party_bn', None)
        p_en = getattr(obj, '_party_en', None)
        party = ((p_en or p_bn) if is_en else (p_bn or p_en)) or ''
        pk = str(obj.pk)
        if party:
            party_counts[party] = party_counts.get(party, 0) + 1
        options.append({
            'value': pk,
            'label': label,
            'party': party,
            'mtype': getattr(obj, 'member_type', 'direct'),
            'checked': pk in selected,
            'search': label.lower(),
        })

    return {
        'name': bound_field.html_name,
        'field_id': bound_field.id_for_label or ('id_' + bound_field.html_name),
        'options': options,
        'parties': sorted(party_counts.keys()),
        'selected_count': len(selected),
        'total_input_id': total_field.id_for_label if total_field is not None else '',
        'errors': bound_field.errors,
        'is_en': is_en,
    }
