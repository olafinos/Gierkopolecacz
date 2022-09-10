from django import template
from django.contrib.auth.models import User

from polecacz.models import SelectedGames

register = template.Library()


@register.filter
def selected_games_count(user: User) -> int:
    """
    Allows to retrieve information about how many games user has selected
    :param user: User object
    """
    if user.is_authenticated:
        qs = SelectedGames.objects.filter(user=user)
        if qs.exists():
            return qs[0].selected_games.count()
    return 0
