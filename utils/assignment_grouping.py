"""Group a single MP's assignments by parliament.

Shared by the MP profile's Ministry and Committee tabs. Both tabs show ONE
person, so the column that repeats is Parliament — grouping by it is the
single-person equivalent of the group-by-minister used on the ministry list
and cabinet report.

It also fixes an ordering bug both models share: neither
``MinistryAssignment.Meta.ordering`` (minister type, ministry name) nor
``CommitteeAssignment.Meta.ordering`` (committee name) mentions parliament, so
an MP who served in more than one parliament had their tenures interleaved.
"""


def group_by_parliament(qs, *order_within):
    """Return ``[{'parliament': Parliament, 'assignments': [...]}, ...]``.

    Newest parliament first. ``order_within`` are extra ordering fields applied
    inside each parliament, e.g.::

        group_by_parliament(qs, 'minister_type__ordering', 'ministry__name_bn')
        group_by_parliament(qs, 'position__ordering', 'committee__name_bn')
    """
    groups, order = {}, []
    for a in qs.order_by('-parliament__ordinal', *order_within):
        if a.parliament_id not in groups:
            groups[a.parliament_id] = {'parliament': a.parliament, 'assignments': []}
            order.append(a.parliament_id)
        groups[a.parliament_id]['assignments'].append(a)
    return [groups[pid] for pid in order]
