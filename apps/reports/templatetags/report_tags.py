from django import template

register = template.Library()


@register.filter
def get_custom_cell(mp, col):
    """Render a cell value for the on-screen custom report table.

    Delegates to the same `_custom_cell` the Excel/CSV/print paths use, so the
    four surfaces cannot drift apart — and so the on-screen table follows the
    language toggle. This used to be a hand-copied Bangla-only twin, which meant
    a report exported in English rendered English while the page it was built on
    showed Bangla.

    Imported inside the function: views imports nothing from templatetags, but a
    module-level import here would load views while the template library is
    being registered.
    """
    from apps.reports.views import _custom_cell
    return _custom_cell(mp, col)


@register.simple_tag(takes_context=True)
def qs_page(context, page):
    """The current query string with `page` set to `page`, every value kept.

    Pagination links used to rebuild the query string with
    `{% for k,v in request.GET.items %}`, and a QueryDict's `.items()` yields
    only the LAST value of a repeated key — so paging a report filtered on
    several MPs quietly dropped every id but one, and nothing was URL-encoded
    either. `urlencode()` keeps every value and escapes them.
    """
    get = context['request'].GET.copy()
    get.setlist('page', [str(page)])
    return get.urlencode()


@register.simple_tag(takes_context=True)
def qs_export(context, *drop):
    """The current query string with `page` and `format` removed.

    The export buttons hang the format on the end of the filters that produced
    the page on screen, so a PDF is the same report the operator is looking at.
    Hand-built `?a={{ a }}&b={{ b }}` strings went stale every time a filter was
    added and, like the pagination links before them, kept only the last value
    of a repeated key — which silently dropped all but one chosen column.
    """
    get = context['request'].GET.copy()
    for key in ('page', 'format') + drop:
        get.pop(key, None)
    return get.urlencode()
