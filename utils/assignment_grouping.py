"""Group assignment rows (ministry / committee / institution) for display.

Two shapes, both born of the same problem: these models' ``Meta.ordering``
sorts by type and name and never mentions the MP or the parliament, so rows
belonging to one person — or one tenure — end up scattered across the table and
across pages, and the list reads as if only one row were recorded.

* :func:`group_by_parliament` — for a page showing ONE person (the MP profile
  tabs), where the repeating column is Parliament.
* :func:`mp_group_order` / :func:`build_mp_groups` / :func:`all_mp_groups` —
  for a page listing MANY people (module lists and reports), where the
  repeating column is the MP. Paginate ``mp_group_order`` so a person's rows
  can never straddle a page break.

Lives in ``utils/`` beside ``go_files.py`` because ministry, committee,
institution and the reports module all use it.
"""
from django.db.models import Min

from apps.mp.models import MP


# ── one person, grouped by parliament ────────────────────────────────────────

def group_by_parliament(qs, *order_within):
    """Return ``[{'parliament': Parliament, 'assignments': [...]}, ...]``.

    Newest parliament first. ``order_within`` are extra ordering fields applied
    inside each parliament, e.g.::

        group_by_parliament(qs, 'minister_type__ordering', 'ministry__name_bn')
        group_by_parliament(qs, 'position__ordering', 'committee__name_bn')
        group_by_parliament(qs, 'role__ordering', 'institution_bn')
    """
    groups, order = {}, []
    for a in qs.order_by('-parliament__ordinal', *order_within):
        if a.parliament_id not in groups:
            groups[a.parliament_id] = {'parliament': a.parliament, 'assignments': []}
            order.append(a.parliament_id)
        groups[a.parliament_id]['assignments'].append(a)
    return [groups[pid] for pid in order]


# ── many people, grouped by MP ───────────────────────────────────────────────

def mp_group_order(qs, rank_field=None):
    """Ordered distinct MPs in ``qs``, as a values() queryset.

    ``rank_field`` ranks the people — e.g. ``'minister_type__ordering'`` puts
    প্রধানমন্ত্রী before মন্ত্রী before প্রতিমন্ত্রী; a person is ranked by their
    highest role. Ties break by name. Omit it to order by name alone.

    Pass the result to a Paginator to paginate by MP.

    The bare ``order_by()`` is required: the model's Meta.ordering would
    otherwise be folded into the GROUP BY and break the grouping.
    """
    base = qs.order_by().values('mp')
    if rank_field:
        return (base.annotate(rank=Min(rank_field), sort_name=Min('mp__name_bn'))
                    .order_by('rank', 'sort_name'))
    return base.annotate(sort_name=Min('mp__name_bn')).order_by('sort_name')


def build_mp_groups(qs, mp_ids):
    """Return ``[{'mp': MP, 'assignments': [...]}, ...]`` in ``mp_ids`` order.

    Fetches the assignments in a single query; ``qs`` keeps its Meta.ordering
    *within* each MP.
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


def all_mp_groups(qs, rank_field=None):
    """Every MP in ``qs``, grouped and ordered. For print/PDF/exports."""
    return build_mp_groups(qs, [g['mp'] for g in mp_group_order(qs, rank_field)])
