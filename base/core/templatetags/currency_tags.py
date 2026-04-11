from django import template

register = template.Library()


@register.filter
def brl(value):
    """Format value as Brazilian Real (R$ 1.234,56)"""
    if value is None:
        return "R$ 0,00"
    try:
        val = float(value)
        if val < 0:
            return (
                f"-R$ {abs(val):,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


@register.filter
def clean_phone(phone):
    """Remove special characters from phone number"""
    if not phone:
        return ""
    return "".join(c for c in str(phone) if c.isdigit())


@register.filter
def abs_val(value):
    """Return absolute value"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def number(value):
    """Format number without decimal places"""
    if value is None:
        return "0"
    try:
        val = float(value)
        return str(int(val)) if val == int(val) else str(val)
    except (ValueError, TypeError):
        return "0"
