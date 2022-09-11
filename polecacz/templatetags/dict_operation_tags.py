from django import template
from django.contrib.auth.models import User

from polecacz.models import SelectedGames

register = template.Library()


@register.filter(name="lookup")
def lookup(value, arg):
    """Allows to use dictionary lookup in Django Template Language"""
    return value[arg]
