from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.filter
def tr(obj, field='name'):
    """Return the bn or en field value based on session language."""
    request = None
    lang = 'bn'
    try:
        from django.utils.translation import get_language
        current = get_language()
        if current and current.startswith('en'):
            lang = 'en'
    except Exception:
        pass

    bn_val = getattr(obj, f'{field}_bn', None)
    en_val = getattr(obj, f'{field}_en', None)
    if lang == 'en':
        return en_val or bn_val or ''
    return bn_val or en_val or ''


@register.filter
def to_bn(value):
    """Convert ASCII digits to Bengali digits."""
    digits = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
              '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    return ''.join(digits.get(c, c) for c in str(value))


@register.simple_tag
def safe_url(url_name):
    """Resolve url_name to a URL; return '#' if the URL doesn't exist yet."""
    if not url_name:
        return '#'
    try:
        return reverse(url_name)
    except (NoReverseMatch, Exception):
        return '#'


@register.filter
def get_item(dictionary, key):
    """Template filter to access dict values: {{ my_dict|get_item:key }}"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def active(context, url_name):
    """Return 'active' css class if current URL matches url_name."""
    request = context.get('request')
    if request:
        from django.urls import resolve, NoReverseMatch
        try:
            resolved = resolve(request.path)
            if resolved.url_name == url_name or resolved.view_name == url_name:
                return 'active'
        except Exception:
            pass
    return ''
