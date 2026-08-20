"""Group ministry assignments by minister.

13 ministers in the 13th parliament hold more than one ministry (three hold
three). Listing raw MinistryAssignment rows sorts them by minister-type then
ministry name, which scatters one person's rows across the table and across
pages — so the list reads as if only one ministry were recorded.

Both the ministry module list and the cabinet report group by MP instead, and
paginate the GROUPS, so a minister's ministries are always shown together and
can never straddle a page break.
"""
from django.db.models import Min

from apps.mp.models import MP


def minister_group_order(qs):
    """Ordered distinct ministers in ``qs``, as a values() queryset.

    Ordered by cabinet rank (প্রধানমন্ত্রী → মন্ত্রী → প্রতিমন্ত্রী → উপমন্ত্রী →
    উপদেষ্টা) then by name. Pass this to a Paginator to paginate by minister.

    The bare ``order_by()`` is required: MinistryAssignment.Meta.ordering would
    otherwise be folded into the GROUP BY and break the grouping.
    """
    return (
        qs.order_by()
          .values('mp')
          .annotate(rank=Min('minister_type__ordering'),
                    sort_name=Min('mp__name_bn'))
          .order_by('rank', 'sort_name')
    )


def build_minister_groups(qs, mp_ids):
    """Return ``[{'mp': MP, 'assignments': [...]}, ...]`` in ``mp_ids`` order.

    Fetches the assignments for these ministers in a single query; ``qs`` keeps
    its Meta.ordering (minister-type rank, then ministry name) *within* each
    minister.
    """
    mp_ids = list(mp_ids)
    by_mp = {}
    for a in qs.filter(mp_id__in=mp_ids):
        by_mp.setdefault(a.mp_id, []).append(a)

    mps = {m.pk: m for m in MP.objects.filter(pk__in=mp_ids)}
    return [
        {'mp': mps[mp_id], 'assignments': by_mp.get(mp_id, [])}
        for mp_id in mp_ids if mp_id in mps
    ]


def all_minister_groups(qs):
    """Every minister in ``qs``, grouped and ordered. For print/PDF/exports."""
    return build_minister_groups(qs, [g['mp'] for g in minister_group_order(qs)])


def group_by_parliament(qs):
    """Group ONE minister's assignments by parliament, newest parliament first.

    The MP profile's ministry tab shows a single person, so the repeating column
    there is Parliament, not the minister. MinistryAssignment.Meta.ordering sorts
    by minister-type then ministry name and ignores parliament entirely, so an MP
    who held office in two parliaments got interleaved rows. Ordering by
    parliament first keeps each tenure together.

    Returns ``[{'parliament': Parliament, 'assignments': [...]}, ...]``; within a
    parliament the Meta.ordering (rank, then ministry name) still applies.
    """
    groups, order = {}, []
    for a in qs.order_by('-parliament__ordinal', 'minister_type__ordering',
                         'ministry__name_bn'):
        if a.parliament_id not in groups:
            groups[a.parliament_id] = {'parliament': a.parliament, 'assignments': []}
            order.append(a.parliament_id)
        groups[a.parliament_id]['assignments'].append(a)
    return [groups[pid] for pid in order]
