from django import template
from decimal import Decimal, InvalidOperation

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


@register.filter
def split(value, delimiter):
    if value:
        return value.split(delimiter)
    return []


@register.filter
def getattr(obj, attr):
    try:
        return getattr(obj, attr)
    except Exception:
        return ''


# ✅ DIVIDE FILTER
@register.filter
def div(value, arg):
    """
    Divides value by arg
    Usage: {{ value|div:arg }}
    """
    try:
        value = Decimal(value)
        arg = Decimal(arg)
        if arg == 0:
            return 0
        return value / arg
    except (TypeError, InvalidOperation):
        return 0


# ✅ MULTIPLY FILTER
@register.filter
def mul(value, arg):
    """
    Multiplies value by arg
    Usage: {{ value|mul:arg }}
    """
    try:
        return Decimal(value) * Decimal(arg)
    except (TypeError, InvalidOperation):
        return 0

# ✅ SUM ATTRIBUTE FILTER
@register.filter
def sum_attr(queryset, attr):
    """
    Sums a numeric attribute from a queryset or list of objects

    Usage:
    {{ suppliers|sum_attr:"total_paid" }}
    """
    total = Decimal('0')

    if not queryset:
        return total

    for obj in queryset:
        try:
            value = getattr(obj, attr, 0)
            if value is not None:
                total += Decimal(value)
        except (TypeError, InvalidOperation):
            continue

    return total