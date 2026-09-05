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
