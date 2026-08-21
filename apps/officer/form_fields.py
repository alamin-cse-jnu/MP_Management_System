"""Form field + queryset helpers for picking officers from the PRP roster."""

from django import forms
from django.db.models import Q

from .models import Officer


def _lang():
    try:
        from django.utils.translation import get_language
        lang = get_language()
        return 'en' if lang and lang.startswith('en') else 'bn'
    except Exception:
        return 'bn'


def selectable_queryset(include_pks=None):
    """Officers that may be picked.

    ``include_pks`` re-admits officers already attached to the tour being
    edited — even retired ones — so opening an old tour can never silently drop
    an officer who has since left. They render pre-checked with a retired badge;
    unchecking and saving removes them for good, and they cannot be re-added.
    """
    qs = Officer.objects.all()
    if include_pks:
        qs = qs.filter(Q(is_active=True) | Q(pk__in=list(include_pks)))
    else:
        qs = qs.selectable()
    return qs.order_by('-is_active', 'name_bn', 'prp_id')


class OfficerMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Multi-select over the officer roster, rendered by {% officer_picker %}."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('queryset', selectable_queryset())
        kwargs.setdefault('label', 'সঙ্গী কর্মকর্তাগণ / Accompanying Officers')
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        is_en = (_lang() == 'en')
        name = obj.display_name_en if is_en else obj.display_name_bn
        desig = (obj.designation_en or obj.designation_bn) if is_en else \
                (obj.designation_bn or obj.designation_en)
        if desig:
            return f"{name} — {desig} — {obj.prp_id}"
        return f"{name} — {obj.prp_id}"
