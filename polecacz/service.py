from polecacz.models import Game
from django.db.models import Count, QuerySet


class PolecaczService:

    @staticmethod
    def find_most_similar_games(tags: list[str]) -> QuerySet:
        """
        Finds most similar games using provided tags.
        :param tags: List with tags used in games.
        :return: QuerySet with games ordered by similarity
        """
        similar_games = Game.objects.filter(tags__name__in=tags)
        similar_games = similar_games.annotate(same_tags=Count('tags')).order_by('-same_tags','-rating')
        return similar_games
