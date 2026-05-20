from django import template

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    """Get any attribute from an object by name string. Supports callables."""
    val = getattr(obj, attr_name, '')
    return val() if callable(val) else val
