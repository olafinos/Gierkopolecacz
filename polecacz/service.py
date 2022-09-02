from polecacz.models import Game
from django.db.models import Count

class PolecaczService:

    @staticmethod
    def get_20_most_similar_games(tags: list[str]):
        similar_games = Game.objects.filter(tags__name__in=tags)
        similar_games = similar_games.annotate(same_tags=Count('tags')).order_by('-same_tags','-rating')[:20]
        return similar_games

