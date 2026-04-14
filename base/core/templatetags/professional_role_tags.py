from django import template
from base.accounts.models import ProfessionalRole

register = template.Library()


@register.simple_tag
def get_professional_roles():
    return ProfessionalRole.choices
