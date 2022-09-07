from django import template
from polecacz.models import SelectedGames

register = template.Library()

@register.filter
def selected_games_count(user):
    if user.is_authenticated:
        qs = SelectedGames.objects.filter(user=user)
        if qs.exists():
            return qs[0].selected_games.count()
    return 0