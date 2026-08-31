# -*- coding: utf-8 -*-
"""Bangla ⇄ ASCII digit handling for search boxes.

Every number in this system is *stored* in ASCII digits (MP ID `013000101`,
memo numbers, GO numbers) but *shown* in Bangla numerals, so an operator reading
১৫২ off the screen and typing it back gets no results. Searches therefore match
on every digit spelling of the query, not just the one that was typed.
"""

from django.db.models import Q

BN_DIGITS = '০১২৩৪৫৬৭৮৯'
EN_DIGITS = '0123456789'

_TO_EN = str.maketrans(BN_DIGITS, EN_DIGITS)
_TO_BN = str.maketrans(EN_DIGITS, BN_DIGITS)


def to_en_digits(text):
    """'১৫২' → '152' (non-digit characters untouched)."""
    return (text or '').translate(_TO_EN)


def to_bn_digits(text):
    """'152' → '১৫২' (non-digit characters untouched)."""
    return (text or '').translate(_TO_BN)


def digit_variants(q):
    """The query as typed, plus its ASCII- and Bangla-digit spellings.

    Order is stable and duplicates are dropped, so a query with no digits at all
    returns a single-item list and costs nothing extra.
    """
    out = []
    for variant in (q, to_en_digits(q), to_bn_digits(q)):
        if variant and variant not in out:
            out.append(variant)
    return out


def search_q(q, fields):
    """OR'ed ``icontains`` Q over every field × every digit spelling of ``q``.

    ``fields`` are lookup paths, so related fields work too:
        search_q(q, ['mp__name_bn', 'mp__mp_id'])
    Returns an empty Q() for a blank query — safe to pass straight to filter().
    """
    query = Q()
    for variant in digit_variants(q):
        for field in fields:
            query |= Q(**{f'{field}__icontains': variant})
    return query
