from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key, '')
    return ''


@register.filter(name='abs')
def absolute_value(value):
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


# ✅ ADD THIS
@register.filter
def split(value, delimiter):
    """
    Splits a string by the given delimiter
    Usage: {{ value|split:'/' }}
    """
    if value:
        return value.split(delimiter)
    return []
