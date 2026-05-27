from django import forms


def _lang():
    """Return 'en' or 'bn' based on the active Django translation."""
    try:
        from django.utils.translation import get_language
        lang = get_language()
        return 'en' if lang and lang.startswith('en') else 'bn'
    except Exception:
        return 'bn'


class BilingualChoiceField(forms.ModelChoiceField):
    """
    Bilingual ModelChoiceField for any model with name_bn + name_en.

    Bangla mode  → shows name_bn
    English mode → shows name_en  (falls back to name_bn if empty)

    Reusable for Ministry, Committee, Institution, Country, etc.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('empty_label', '-- নির্বাচন করুন / Select --')
        super().__init__(*args, **kwargs)
        self.widget.attrs.setdefault('data-select2', '')
        self.widget.attrs.setdefault('class', 'form-select')

    def label_from_instance(self, obj):
        name_bn = getattr(obj, 'name_bn', '') or ''
        name_en = getattr(obj, 'name_en', '') or ''
        if _lang() == 'en':
            return name_en or name_bn
        return name_bn or name_en
