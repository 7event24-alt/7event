from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def app_version():
    return getattr(settings, "VERSION", "1.0.0")
