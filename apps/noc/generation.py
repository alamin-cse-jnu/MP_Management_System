"""Build an NOC document body from a template + the tour/MP data already held.

Templates are filled by **plain token substitution**, not the Django template
engine: a template body is admin-editable content stored in the database, and
``Template(...).render(...)`` on such a string would let ``{% %}`` tags execute.
``render_body()`` only ever replaces ``{lower_snake_case}`` tokens, so any other
brace in the HTML (or a mistyped token) is left visibly alone.
"""

import re
from datetime import date

from utils.bangla_date import (
    format_bangla_date, format_gregorian_bn, format_gregorian_en,
    format_range_bn, format_range_en,
)
from utils.bn_numerals import to_bn

from .models import LANGUAGE_BN, NOC, NOCLetterhead

_TOKEN_RE = re.compile(r'\{([a-z][a-z0-9_]*)\}')

# Honorifics. The whole body is editable afterwards, so a wrong guess here is a
# one-word fix rather than a blocker.
_TITLE_BN = {'male': 'জনাব', 'female': 'বেগম'}
_TITLE_EN = {'male': 'Mr.', 'female': 'Mrs.'}


def _sex(person):
    """'male' / 'female' / '' from a master.Gender FK, tolerant of naming."""
    gender = getattr(person, 'gender', None)
    if gender is None:
        return ''
    label = f'{getattr(gender, "name_en", "")} {getattr(gender, "name_bn", "")}'.lower()
    if 'female' in label or 'মহিলা' in label or 'নারী' in label:
        return 'female'
    if 'male' in label or 'পুরুষ' in label:
        return 'male'
    return ''


def _join_en(items):
    """['A','B','C'] → 'A, B and C' — the samples' Oxford-less style."""
    items = [i for i in items if i]
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    return f'{", ".join(items[:-1])} and {items[-1]}'


def _join_bn(items):
    items = [i for i in items if i]
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    return f'{", ".join(items[:-1])} ও {items[-1]}'


def _constituency(mp):
    """The MP's seat as printed: '197 Gazipur-4' / '১৯৭ গাজীপুর-৪'.

    Reserved-seat and technocrat members may have no constituency; the caller
    gets empty strings and edits the sentence by hand.
    """
    election = mp.election_infos.filter(parliament=mp.parliament).select_related(
        'constituency').first()
    if election is None:
        election = mp.election_infos.select_related('constituency').first()
    seat = getattr(election, 'constituency', None)
    if seat is None:
        return '', ''
    return seat.display_bn or '', seat.display_en or ''


def _spouse_clause(mp, spouse):
    """Sample-2's ' He will be accompanied by his spouse Mrs. X (Passport No-Y).'"""
    if spouse is None:
        return '', ''
    sex = _sex(mp)
    pronoun, possessive = ('She', 'her') if sex == 'female' else ('He', 'his')
    sp_sex = _sex(spouse)
    sp_title_en = _TITLE_EN.get(sp_sex, 'Mrs.' if sex != 'female' else 'Mr.')
    sp_title_bn = _TITLE_BN.get(sp_sex, 'বেগম' if sex != 'female' else 'জনাব')

    passport = (spouse.passport_number or '').strip()
    tail_en = f' (Passport No-{passport})' if passport else ''
    en = (f' {pronoun} will be accompanied by {possessive} spouse '
          f'{sp_title_en} {spouse.name_en or spouse.name_bn}{tail_en}.')

    tail_bn = f' (পাসপোর্ট নং-{to_bn(passport)})' if passport else ''
    bn = (f' তাঁর সঙ্গে তাঁর সহধর্মিণী/সহধর্মী {sp_title_bn} '
          f'{spouse.name_bn or spouse.name_en}{tail_bn} গমন করবেন।')
    return bn, en


def build_context(mp, tour=None, spouse=None, letterhead=None,
                  issue_date=None, memo_no='', signatory=None):
    """Every placeholder a template may use, for both languages."""
    letterhead = letterhead or NOCLetterhead.current()
    issue_date = issue_date or date.today()

    seat_bn, seat_en = _constituency(mp)
    sex = _sex(mp)

    countries = list(tour.countries.select_related('country').all()) if tour else []
    countries_bn = _join_bn([c.country.name_bn for c in countries])
    countries_en = _join_en([c.country.name_en for c in countries])

    start = tour.overall_from_date if tour else None
    end = tour.overall_to_date if tour else None

    spouse_bn, spouse_en = _spouse_clause(mp, spouse)
    passport = (mp.passport_number or '').strip() or '—'

    sig_name_bn = sig_name_en = sig_desig_bn = sig_desig_en = ''
    sig_phone = sig_mobile = ''
    if signatory is not None:
        sig_name_bn = signatory.display_name_bn
        sig_name_en = signatory.display_name_en
        sig_desig_bn = signatory.designation_bn
        sig_desig_en = signatory.designation_en
        sig_phone = signatory.telephone or ''
        sig_mobile = signatory.mobile or ''

    return {
        # ── letterhead ──────────────────────────────────────────────────────
        'org_bn': letterhead.org_bn, 'org_en': letterhead.org_en,
        'wing_bn': letterhead.wing_bn, 'wing_en': letterhead.wing_en,
        'section_bn': letterhead.section_bn, 'section_en': letterhead.section_en,
        'address_bn': letterhead.address_bn, 'address_en': letterhead.address_en,
        'website': letterhead.website, 'telephone': letterhead.telephone,
        'fax': letterhead.fax, 'email': letterhead.email,
        'speaker_title_bn': letterhead.speaker_title_bn,
        'speaker_title_en': letterhead.speaker_title_en,

        # ── memo + dates ────────────────────────────────────────────────────
        'memo_no': memo_no,
        'memo_no_bn': to_bn(memo_no),
        'issue_date_en': format_gregorian_en(issue_date),
        'gregorian_date_bn': format_gregorian_bn(issue_date),
        'bangla_date': format_bangla_date(issue_date),

        # ── the member ──────────────────────────────────────────────────────
        'mp_name_bn': mp.name_bn, 'mp_name_en': mp.name_en,
        'mp_title_bn': _TITLE_BN.get(sex, 'জনাব'),
        'mp_title_en': _TITLE_EN.get(sex, 'Mr.'),
        'mp_id': mp.mp_id,
        'passport_no': passport,
        'passport_no_bn': to_bn(passport),
        'constituency_bn': seat_bn, 'constituency_en': seat_en,

        # ── the trip ────────────────────────────────────────────────────────
        'countries_bn': countries_bn, 'countries_en': countries_en,
        'date_range_bn': format_range_bn(start, end),
        'date_range_en': format_range_en(start, end),
        'go_number': tour.go_number if tour else '',
        'purpose_bn': tour.purpose.name_bn if tour else '',
        'purpose_en': tour.purpose.name_en if tour else '',
        'spouse_clause_bn': spouse_bn, 'spouse_clause_en': spouse_en,

        # ── signatory ───────────────────────────────────────────────────────
        'signatory_name_bn': sig_name_bn, 'signatory_name_en': sig_name_en,
        'signatory_designation_bn': sig_desig_bn,
        'signatory_designation_en': sig_desig_en,
        'signatory_phone': sig_phone,
        'signatory_mobile': sig_mobile,
        'signatory_mobile_bn': to_bn(sig_mobile),
        'signatory_email': letterhead.email,
    }


def render_body(template_html, context):
    """Replace ``{token}`` with its value; unknown tokens are left visible."""
    def replace(match):
        key = match.group(1)
        if key in context:
            value = context[key]
            return '' if value is None else str(value)
        return match.group(0)

    return _TOKEN_RE.sub(replace, template_html or '')


def unresolved_tokens(html, context):
    """Tokens still standing in `html` — used by tests and the editor warning."""
    return sorted({m.group(1) for m in _TOKEN_RE.finditer(html or '')
                   if m.group(1) not in context})



# ── keeping the document in step with the fields beside it ───────────────────
#
# `body_html` is the whole editable page, so the memo number, dates and
# signature block exist BOTH as columns and as text inside the HTML. Changing a
# column alone used to leave the printed letter showing the old value.
#
# Two cases, handled differently:
#   * the body is still exactly what the template produces  -> re-render it, so
#     everything (including a signatory that was empty before, and therefore has
#     no old text to find) lands in the document;
#   * the body has been hand-edited                         -> replace only the
#     old rendered strings with the new ones, preserving the edits.

# Context keys that appear verbatim in a rendered document and can be swapped.
SYNCED_KEYS = (
    'memo_no', 'memo_no_bn',
    'issue_date_en', 'gregorian_date_bn', 'bangla_date',
    'signatory_name_bn', 'signatory_name_en',
    'signatory_designation_bn', 'signatory_designation_en',
    'signatory_phone', 'signatory_mobile', 'signatory_mobile_bn', 'signatory_email',
)

# Below this length a replacement risks hitting unrelated text.
_MIN_REPLACE_LEN = 3


def is_pristine(body_html, template_html, context):
    """True when `body_html` is still exactly what the template renders."""
    if not template_html:
        return False
    return (body_html or '').strip() == render_body(template_html, context).strip()


def patch_body(body_html, old_context, new_context, keys=SYNCED_KEYS):
    """Swap old rendered values for new ones, leaving manual edits alone.

    Returns ``(html, unpatched)`` where `unpatched` names the keys that changed
    but had no old text to find — the caller warns that a Regenerate is needed
    for those.
    """
    html = body_html or ''
    unpatched = []
    for key in keys:
        old = str(old_context.get(key, '') or '')
        new = str(new_context.get(key, '') or '')
        if old == new:
            continue
        if len(old) < _MIN_REPLACE_LEN or old not in html:
            # Nothing to replace (it was blank, or the user rewrote that line).
            unpatched.append(key)
            continue
        html = html.replace(old, new)
    return html, unpatched

def next_serial(issue_date=None):
    """Next memo serial for the calendar year of `issue_date`."""
    issue_date = issue_date or date.today()
    latest = (NOC.objects.filter(issue_date__year=issue_date.year)
              .exclude(serial_no=None).order_by('-serial_no').first())
    return (latest.serial_no + 1) if latest else 1


def suggest_memo_no(serial, issue_date=None, letterhead=None):
    """'11.00.0000.000.610.37.0002.26.197' — prefix + 2-digit year + serial."""
    letterhead = letterhead or NOCLetterhead.current()
    issue_date = issue_date or date.today()
    return f'{letterhead.memo_prefix}.{issue_date.year % 100:02d}.{serial}'
