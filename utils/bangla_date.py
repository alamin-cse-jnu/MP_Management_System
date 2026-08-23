"""Bangla (বঙ্গাব্দ) calendar + date formatting for official letters.

The Bangla NOC forwarding letter prints a **two-line date**::

    তারিখ: ০২ ভাদ্র ১৪৩৩
           ১৭ আগস্ট ২০২৬

so we need both the Bengali-era date and the Gregorian date spelled in Bangla,
in Bengali digits.

**Calendar rule** — the *revised* Bangladesh calendar (in force since 1426 BS /
2019), NOT the older Indian/Surya Siddhanta reckoning:

* ১ বৈশাখ is always **14 April**.
* First six months (বৈশাখ–আশ্বিন) have 31 days, next five (কার্তিক–মাঘ) have 30,
  চৈত্র has 30, and ফাল্গুন has 29 — 30 in a Gregorian leap year.
  (6×31 + 5×30 + 30 + 29 = 365, and 366 in a leap year.)

Verified against both supplied samples:
``2026-08-17 → ০২ ভাদ্র ১৪৩৩`` and ``2026-08-19 → ০৪ ভাদ্র ১৪৩৩``.
"""

from datetime import date

from utils.bn_numerals import to_bn

# বঙ্গাব্দ months, in order.
BS_MONTHS = [
    'বৈশাখ', 'জ্যৈষ্ঠ', 'আষাঢ়', 'শ্রাবণ', 'ভাদ্র', 'আশ্বিন',
    'কার্তিক', 'অগ্রহায়ণ', 'পৌষ', 'মাঘ', 'ফাল্গুন', 'চৈত্র',
]

# Gregorian months spelled in Bangla (used for the second date line).
GREGORIAN_MONTHS_BN = [
    'জানুয়ারি', 'ফেব্রুয়ারি', 'মার্চ', 'এপ্রিল', 'মে', 'জুন',
    'জুলাই', 'আগস্ট', 'সেপ্টেম্বর', 'অক্টোবর', 'নভেম্বর', 'ডিসেম্বর',
]

GREGORIAN_MONTHS_EN = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

# ১ বৈশাখ falls on this Gregorian day, every year, under the revised calendar.
_NEW_YEAR_MONTH = 4
_NEW_YEAR_DAY = 14

# Gregorian year - this = বঙ্গাব্দ year, for dates on/after ১ বৈশাখ.
_BS_OFFSET = 593


def _is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _month_lengths(bs_year):
    """Day counts for each বঙ্গাব্দ month of `bs_year`.

    ফাল্গুন (index 10) gains a day in a Gregorian leap year. A বঙ্গাব্দ year that
    opens in April of Gregorian year Y runs its ফাল্গুন in February of Y+1, so the
    leap test uses ``bs_year + _BS_OFFSET + 1``.
    """
    falgun = 30 if _is_leap(bs_year + _BS_OFFSET + 1) else 29
    return [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, falgun, 30]


def to_bangla_date(d):
    """Gregorian ``date`` → ``(bs_year, bs_month_index_1_based, bs_day)``."""
    greg_year = d.year
    new_year = date(greg_year, _NEW_YEAR_MONTH, _NEW_YEAR_DAY)
    if d < new_year:
        # Still in the বঙ্গাব্দ year that opened last April.
        greg_year -= 1
        new_year = date(greg_year, _NEW_YEAR_MONTH, _NEW_YEAR_DAY)

    bs_year = greg_year - _BS_OFFSET
    offset = (d - new_year).days          # 0 on ১ বৈশাখ

    for index, length in enumerate(_month_lengths(bs_year), start=1):
        if offset < length:
            return bs_year, index, offset + 1
        offset -= length

    # Unreachable: the month lengths always sum to the Gregorian year length.
    raise ValueError(f'could not place {d} in the Bangla calendar')


def format_bangla_date(d):
    """``date`` → ``'০২ ভাদ্র ১৪৩৩'``."""
    if not d:
        return ''
    bs_year, month, day = to_bangla_date(d)
    return f'{to_bn(f"{day:02d}")} {BS_MONTHS[month - 1]} {to_bn(bs_year)}'


def format_gregorian_bn(d):
    """``date`` → ``'১৭ আগস্ট ২০২৬'`` (Gregorian date, Bangla words + digits)."""
    if not d:
        return ''
    return f'{to_bn(f"{d.day:02d}")} {GREGORIAN_MONTHS_BN[d.month - 1]} {to_bn(d.year)}'


def format_gregorian_en(d):
    """``date`` → ``'17 August 2026'`` — the English certificate's date style."""
    if not d:
        return ''
    return f'{d.day:02d} {GREGORIAN_MONTHS_EN[d.month - 1]} {d.year}'


def format_range_en(start, end):
    """Date range in the English certificate's style.

    Matching the samples, a shared month or year is not repeated::

        10 to 28 August 2026
        22 August to 07 September 2026
        28 December 2026 to 03 January 2027
    """
    if not start and not end:
        return ''
    if not start or not end:
        return format_gregorian_en(start or end)

    if start.year == end.year and start.month == end.month:
        return (f'{start.day:02d} to {end.day:02d} '
                f'{GREGORIAN_MONTHS_EN[end.month - 1]} {end.year}')
    if start.year == end.year:
        return (f'{start.day:02d} {GREGORIAN_MONTHS_EN[start.month - 1]} to '
                f'{end.day:02d} {GREGORIAN_MONTHS_EN[end.month - 1]} {end.year}')
    return f'{format_gregorian_en(start)} to {format_gregorian_en(end)}'


def format_range_bn(start, end):
    """Date range in the Bangla letter's style: ``'২১-২৯ আগস্ট ২০২৬'``."""
    if not start and not end:
        return ''
    if not start or not end:
        return format_gregorian_bn(start or end)

    if start.year == end.year and start.month == end.month:
        return (f'{to_bn(f"{start.day:02d}")}-{to_bn(f"{end.day:02d}")} '
                f'{GREGORIAN_MONTHS_BN[end.month - 1]} {to_bn(end.year)}')
    if start.year == end.year:
        return (f'{to_bn(f"{start.day:02d}")} {GREGORIAN_MONTHS_BN[start.month - 1]} - '
                f'{to_bn(f"{end.day:02d}")} {GREGORIAN_MONTHS_BN[end.month - 1]} '
                f'{to_bn(end.year)}')
    return f'{format_gregorian_bn(start)} - {format_gregorian_bn(end)}'
