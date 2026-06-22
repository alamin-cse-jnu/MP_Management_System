from django import forms
from django.db.models import OuterRef, Subquery


def _lang():
    """Return 'en' or 'bn' based on the active Django translation."""
    try:
        from django.utils.translation import get_language
        lang = get_language()
        return 'en' if lang and lang.startswith('en') else 'bn'
    except Exception:
        return 'bn'


class MPChoiceField(forms.ModelChoiceField):
    """
    Bilingual ModelChoiceField for MP selection.

    Bangla mode:  নাম বাংলায় — বাংলা আসন — MP-ID
    English mode: English Name — English Constituency — MP-ID

    Supports Select2 live search by name, MP ID, or constituency.
    Reusable across all modules that need to pick an MP.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('empty_label', '-- সংসদ সদস্য / Select MP --')
        if 'queryset' not in kwargs:
            kwargs['queryset'] = MPChoiceField.annotated_queryset()
        super().__init__(*args, **kwargs)
        self.widget.attrs.setdefault('data-select2', '')
        self.widget.attrs.setdefault('class', 'form-select')

    @staticmethod
    def annotated_queryset(exclude_pks=None):
        from apps.mp.models import MP, ElectionInfo
        from apps.parliament.models import Parliament

        active_parl = Parliament.objects.filter(is_active=True).values('pk')[:1]

        qs = MP.objects.filter(is_active=True).annotate(
            _con_bn=Subquery(
                ElectionInfo.objects.filter(
                    mp=OuterRef('pk'),
                    parliament__in=active_parl,
                ).values('constituency__display_bn')[:1]
            ),
            _con_en=Subquery(
                ElectionInfo.objects.filter(
                    mp=OuterRef('pk'),
                    parliament__in=active_parl,
                ).values('constituency__display_en')[:1]
            ),
            _con_order=Subquery(
                ElectionInfo.objects.filter(
                    mp=OuterRef('pk'),
                    parliament__in=active_parl,
                ).values('constituency__ordering')[:1]
            ),
            # Party (from active-parliament ElectionInfo) — used by the
            # MP picker panel's party quick-filter chips.
            _party_bn=Subquery(
                ElectionInfo.objects.filter(
                    mp=OuterRef('pk'),
                    parliament__in=active_parl,
                ).values('party__name_bn')[:1]
            ),
            _party_en=Subquery(
                ElectionInfo.objects.filter(
                    mp=OuterRef('pk'),
                    parliament__in=active_parl,
                ).values('party__name_en')[:1]
            ),
        ).order_by(
            # Serial order: direct-elected (1→300) by constituency ordering,
            # then reserved seats (301→350) by mp_id. 'direct' < 'reserved'.
            'member_type', '_con_order', 'mp_id',
        )

        if exclude_pks:
            qs = qs.exclude(pk__in=exclude_pks)
        return qs

    def label_from_instance(self, obj):
        lang = _lang()
        is_en = (lang == 'en')

        name = (obj.name_en or obj.name_bn) if is_en else (obj.name_bn or obj.name_en)
        con_bn = getattr(obj, '_con_bn', None)
        con_en = getattr(obj, '_con_en', None)
        constituency = (con_en or con_bn) if is_en else (con_bn or con_en)

        if constituency:
            return f"{name} — {constituency} — {obj.mp_id}"
        if getattr(obj, 'member_type', '') == 'reserved':
            reserved = 'Reserved' if is_en else 'সংরক্ষিত'
            return f"{name} — {reserved} — {obj.mp_id}"
        return f"{name} — {obj.mp_id}"


class MPMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    Multi-select sibling of MPChoiceField — pick several MPs at once
    (e.g. one GO covering 5 MPs). Same serial ordering, same bilingual
    label, same Select2 type-to-filter search.
    """

    def __init__(self, *args, **kwargs):
        if 'queryset' not in kwargs:
            kwargs['queryset'] = MPChoiceField.annotated_queryset()
        super().__init__(*args, **kwargs)
        self.widget.attrs.setdefault('data-select2', '')
        self.widget.attrs.setdefault('class', 'form-select')
        self.widget.attrs.setdefault('data-placeholder', '-- সংসদ সদস্য নির্বাচন করুন / Select MPs --')

    # Reuse the single-field bilingual label.
    label_from_instance = MPChoiceField.label_from_instance
