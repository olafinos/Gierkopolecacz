import factory

import factory.fuzzy

from polecacz.models import Game


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game

    name = factory.Sequence(lambda n: 'awesome game %d' % n)
    game_id = factory.Sequence(lambda n: n)
    rank = factory.Sequence(lambda n: n)
    rating = factory.fuzzy.FuzzyFloat(0,10)
    thumbnail = factory.Sequence(lambda n: 'http://thumbnail.com/%d' % n)
    artist = 'artist'
    designer = 'designer'
    year_published = '2022'
    min_players = 1
    max_players = 4
    playing_time = 120

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.tags.add(*extracted)
