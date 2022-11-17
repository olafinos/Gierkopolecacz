import uuid

from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase

from polecacz.models import SelectedGames, Recommendation, OwnedGames
from polecacz.service import GameService, SelectedGamesService, RecommendationService, OwnedGamesService
from test.factories.game import GameFactory


class TestGameService(TestCase):
    def setUp(self) -> None:
        self.game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9, name='game1')
        self.game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0, name='game2')

    def test_get_all_games_ordered_by(self):
        game_3 = GameFactory(tags=["Tag1"], rating=8.0)
        result = GameService.get_all_games_ordered_by('rating')
        expected = [game_3, self.game_2, self.game_1]
        self.assertEqual(list(result), expected)
        result = GameService.get_all_games_ordered_by('-rating')
        expected =  [self.game_1, self.game_2, game_3]
        self.assertEqual(list(result), expected)

    def test_filter_games_which_contains_string(self):
        game_3 = GameFactory(tags=["Tag1"], rating=8.0, name='some_name')
        result = GameService.filter_games_which_contains_string('some')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], game_3)

    def test_filter_games_which_name_contains_tag(self):
        GameFactory(tags=["Tag5"], rating=8.0, name='some_name')
        result = GameService.filter_games_which_name_contains_tag('Tag1')
        self.assertEqual(len(result), 2)
        self.assertTrue(self.game_1 in result)
        self.assertTrue(self.game_2 in result)

    def test_get_game_by_id(self):
        id = uuid.uuid4()
        game_3 = GameFactory(tags=["Tag1"], rating=8.0, name='some_name',
                             id=id)
        result = GameService.get_game_by_id(id)
        self.assertEqual(result.id, game_3.id)

    def test_get_game_by_id_raises_404(self):
        id = 'a76cc505-fddf-463b-a5e1-9b047167aca5'
        with self.assertRaises(Http404):
            GameService.get_game_by_id(id)

    def test_get_ids_from_game_queryset(self):
        games = GameService.get_all_games_ordered_by('rating')
        result = GameService.get_ids_from_game_queryset(games)
        self.assertEqual(result, [self.game_2.id, self.game_1.id])

    def test_get_ids_from_game_queryset_empty_queryset(self):
        games = GameService.filter_games_which_contains_string('SOME_STRING')
        result = GameService.get_ids_from_game_queryset(games)
        self.assertEqual(result, [])

    def test_get_tag_names_from_game_queryset(self):
        result = GameService.get_tag_names_list_from_game(self.game_1)
        self.assertListEqual(sorted(result), ['Tag1', 'Tag2', 'Tag3'])

    def test_find_most_similar_games_ideal_order(self):
        game_3 = GameFactory(tags=["Tag1"], rating=8.0)
        tags = ["Tag1", "Tag2", "Tag3", "Tag4"]
        result = GameService.find_most_similar_games(tags)
        expected = [self.game_1, self.game_2, game_3]
        self.assertEqual(list(result), expected)

    def test_find_most_similar_games_no_tags(self):
        GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9)
        GameFactory(tags=["Tag1", "Tag2"], rating=9.0)
        GameFactory(tags=["Tag1"], rating=8.0)
        tags = []
        result = GameService.find_most_similar_games(tags)
        expected = []
        self.assertEqual(list(result), expected)

    def test_find_most_similar_games_same_amount_of_tags(self):
        game_3 = GameFactory(tags=["Tag1", "Tag2", "Tag4"], rating=8.0)
        tags = ["Tag1", "Tag2", "Tag3", "Tag4"]
        result = GameService.find_most_similar_games(tags)
        expected = [self.game_1, game_3, self.game_2]
        self.assertEqual(list(result), expected)

    def test_find_most_similar_games_filter_out_game_without_tag(self):
        GameFactory(tags=["Tag1", "Tag4"], rating=8.0)
        tags = ["Tag2"]
        result = GameService.find_most_similar_games(tags)
        expected = [self.game_1, self.game_2]
        self.assertEqual(list(result), expected)


class TestSelectedGamesService(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")
        self.game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9, name='game1')
        self.game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0, name='game2')
        self.selected_games_object = SelectedGames.objects.create(user=self.user)

    def test_get_user_selected_games(self):
        for game in [self.game_1, self.game_2]:
            self.selected_games_object.selected_games.add(game)
        self.selected_games_object.save()
        result = SelectedGamesService.get_user_selected_games(self.user)
        self.assertTrue(self.game_1 in result)
        self.assertTrue(self.game_2 in result)

    def test_get_selected_games_object_by_user(self):
        result = SelectedGamesService.get_selected_games_object_by_user(self.user)
        self.assertEqual(result.id, self.selected_games_object.id)


class TestOwnedGamesService(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")
        self.game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9, name='game1')
        self.game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0, name='game2')
        self.owned_games_object = OwnedGames.objects.create(user=self.user)

    def test_get_user_owned_games(self):
        for game in [self.game_1, self.game_2]:
            self.owned_games_object.owned_games.add(game)
        self.owned_games_object.save()
        result = OwnedGamesService.get_user_owned_games(self.user)
        self.assertTrue(self.game_1 in result)
        self.assertTrue(self.game_2 in result)

    def test_get_owned_games_object_by_user(self):
        result = OwnedGamesService.get_owned_games_object_by_user(self.user)
        self.assertEqual(result.id, self.owned_games_object.id)


class TestRecommendationService(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")
        self.game_1 = GameFactory(tags=["Tag1", "Tag2", "Tag3"], rating=9.9, name='game1')
        self.game_2 = GameFactory(tags=["Tag1", "Tag2"], rating=9.0, name='game2')
        self.game_3 = GameFactory(tags=["Tag3", "Tag2"], rating=8.9, name='game3')
        self.recommendation_object = Recommendation.objects.create(user=self.user)
        for game in [self.game_1, self.game_2]:
            self.recommendation_object.recommended_games.add(game)
        self.recommendation_object.selected_games.add(self.game_3)
        self.recommendation_object.save()

    def test_get_recommended_games(self):
        result = RecommendationService.get_recommended_games(self.recommendation_object.id)

        self.assertTrue(self.game_1 in result)
        self.assertTrue(self.game_2 in result)
        self.assertEqual(len(result), 2)

    def test_get_recommended_games_does_not_exist(self):
        result = RecommendationService.get_recommended_games('3bb078e5-4a40-44dd-b53c-37a693353cfd')

        self.assertEqual(result, [])

    def test_get_selected_games(self):
        result = RecommendationService.get_selected_games(self.recommendation_object.id)

        self.assertTrue(self.game_3 in result)
        self.assertEqual(len(result), 1)

    def test_get_selected_games_does_not_exist(self):
        result = RecommendationService.get_selected_games('3bb078e5-4a40-44dd-b53c-37a693353cfd')

        self.assertEqual(result, [])

    def test_get_opinion_created(self):
        result = RecommendationService.get_opinion_created(self.recommendation_object.id)

        self.assertFalse(result)

    def test_get_opinion_created_does_not_exist(self):
        result = RecommendationService.get_opinion_created('3bb078e5-4a40-44dd-b53c-37a693353cfd')

        self.assertTrue(result)

    def test_get_all_recommendations(self):
        result = RecommendationService.get_all_recommendations(self.user)

        self.assertTrue(self.recommendation_object in result)
        self.assertEqual(len(result), 1)

    def test_get_recommendation_by_id(self):
        result = RecommendationService.get_recommendation_by_id(self.recommendation_object.id)

        self.assertEqual(result, self.recommendation_object)

    def test_get_recommendation_by_id_does_not_exist(self):
        with self.assertRaises(Http404):
            result = RecommendationService.get_recommendation_by_id('3bb078e5-4a40-44dd-b53c-37a693353cfd')

    def test_create_recommendation_by_user(self):
        user = User.objects.create(username="some_other")
        result = RecommendationService.create_recommendation(user=user)

        self.assertEqual(result.user, user)

    def test_create_recommendation_by_non_existing_keyword(self):
        with self.assertRaises(Http404):
            result = RecommendationService.create_recommendation(non_existing_keyword=123)
