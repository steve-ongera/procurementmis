from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (TypeError, ValueError):
        return 0

@register.filter
def add(value, arg):
    """Add arg to value"""
    try:
        return float(value) + float(arg)
    except (TypeError, ValueError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (TypeError, ValueError):
        return 0
