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


def _officer_label(obj):
    """'Name — Designation — PRP-ID' in the active language."""
    is_en = (_lang() == 'en')
    name = obj.display_name_en if is_en else obj.display_name_bn
    desig = (obj.designation_en or obj.designation_bn) if is_en else (
        obj.designation_bn or obj.designation_en)
    if desig:
        return f"{name} — {desig} — {obj.prp_id}"
    return f"{name} — {obj.prp_id}"


class OfficerChoiceField(forms.ModelChoiceField):
    """Single-officer picker — used for the NOC signatory.

    Unlike the tour picker this is a plain Select2 dropdown: there is only one
    signatory, and the roster is small enough to type-search in the native
    widget without the checkbox panel.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('queryset', selectable_queryset())
        kwargs.setdefault('label', 'স্বাক্ষরকারী কর্মকর্তা / Signatory')
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return _officer_label(obj)


class OfficerMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Multi-select over the officer roster, rendered by {% officer_picker %}."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('queryset', selectable_queryset())
        kwargs.setdefault('label', 'সঙ্গী কর্মকর্তাগণ / Accompanying Officers')
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return _officer_label(obj)
