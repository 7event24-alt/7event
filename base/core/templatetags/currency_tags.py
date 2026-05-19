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
def format_br_phone(phone):
    """Format phone as +55 (21) 99199-6769 for display."""
    digits = clean_phone(phone)
    if not digits:
        return ""

    if len(digits) in (10, 11):
        digits = "55" + digits

    if not digits.startswith("55"):
        return f"+{digits}"

    ddd = digits[2:4]
    number = digits[4:]

    if len(number) == 9:
        formatted = f"{number[:5]}-{number[5:]}"
    elif len(number) == 8:
        formatted = f"{number[:4]}-{number[4:]}"
    else:
        return f"+{digits}"

    return f"+55 ({ddd}) {formatted}"


@register.filter
def format_cpf(value):
    """Format CPF as 000.000.000-00 for display."""
    if not value:
        return ""

    digits = "".join(c for c in str(value) if c.isdigit())
    if len(digits) != 11:
        return str(value)

    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


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
