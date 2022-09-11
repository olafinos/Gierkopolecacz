from django.test import TestCase

from polecacz.service import GameService
from test.factories.game import GameFactory


class TestGameService(TestCase):
    def test_find_most_similar_games_ideal_order(self):
        game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9)
        game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0)
        game_3 = GameFactory(tags=["Tag1"], rating=8.0)
        tags = ["Tag1", "Tag2", "Tag3", "Tag4"]
        result = GameService.find_most_similar_games(tags)
        expected = [game_1, game_2, game_3]
        self.assertEqual(list(result), expected)

    def test_find_most_similar_games_no_tags(self):
        game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9)
        game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0)
        game_3 = GameFactory(tags=["Tag1"], rating=8.0)
        tags = []
        result = GameService.find_most_similar_games(tags)
        expected = []
        self.assertEqual(list(result), expected)

    def test_find_most_similar_games_same_amount_of_tags(self):
        game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9)
        game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0)
        game_3 = GameFactory(tags=["Tag1", "Tag2", "Tag4"], rating=8.0)
        tags = ["Tag1", "Tag2", "Tag3", "Tag4"]
        result = GameService.find_most_similar_games(tags)
        expected = [game_1, game_3, game_2]
        self.assertEqual(list(result), expected)

    def test_find_most_similar_games_filter_out_game_without_tag(self):
        game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9)
        game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0)
        game_3 = GameFactory(tags=["Tag1", "Tag4"], rating=8.0)
        tags = ["Tag2"]
        result = GameService.find_most_similar_games(tags)
        expected = [game_1, game_2]
        self.assertEqual(list(result), expected)
