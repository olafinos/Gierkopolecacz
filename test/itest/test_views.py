from http import HTTPStatus
from unittest.mock import patch, ANY

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.test import TestCase

from polecacz.models import SelectedGames, Recommendation, Opinion, OwnedGames, ImageMetadata
from polecacz.validators import TooBigFileException
from test.factories.game import GameFactory


class UserViewTest(TestCase):
    def test_signup_not_valid_data(self):
        username = "a" * 200
        response = self.client.post(
            "/signup/",
            data={
                "username": username,
                "password1": "validpassword1",
                "password2": "validpassword1",
                "email": "valid@email.com",
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response,
            "Upewnij się, że ta wartość ma co najwyżej 150 znaków (obecnie ma 200).",
            html=True,
        )

    @patch("gierkopolecacz.views.send_activation_email")
    def test_signup_valid_data(self, mocked_email):
        response = self.client.post(
            "/signup/",
            data={
                "username": "valid_username",
                "password1": "validpassword1",
                "password2": "validpassword1",
                "email": "valid@email.com",
            },
        )
        # call(WSGIRequest: POST '/signup'), call(User: valid_username)
        mocked_email.assert_called_with(ANY, ANY, "valid@email.com")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/polecacz/")
        user = User.objects.get(username="valid_username")
        self.assertFalse(user.is_active)

    @patch("django.core.mail.EmailMessage.send")
    def test_activate_email(self, mocked_email):
        response = self.client.post(
            "/signup/",
            data={
                "username": "valid_username1",
                "password1": "validpassword1",
                "password2": "validpassword1",
                "email": "valid@email.com",
            },
        )
        mocked_email.assert_called_with()

    @patch("gierkopolecacz.views.account_activation_token.check_token")
    def test_activate_correct_token(self, mocked_token):
        mocked_token.return_value = True
        user = User.objects.create(
            username="username",
            password="password",
            email="email@email.com",
            is_active=False,
        )
        encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.get(f"/activate/{encoded_id}/token/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")
        user = User.objects.get(username="username")
        self.assertTrue(user.is_active)

    @patch("gierkopolecacz.views.account_activation_token.check_token")
    def test_activate_uncorrect_token(self, mocked_token):
        mocked_token.return_value = False
        user = User.objects.create(
            username="username",
            password="password",
            email="email@email.com",
            is_active=False,
        )
        encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.get(f"/activate/{encoded_id}/invalid_token/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "polecacz/")
        user = User.objects.get(username="username")
        self.assertFalse(user.is_active)


class IndexViewTest(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_index_view(self):
        for i in range(15):
            GameFactory()
        response = self.client.get("/polecacz/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context["object_list"]) == 12)


class GameDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    @patch("polecacz.service.pyrebase")
    def test_game_detail_view(self, mocked_firebase_service):
        game = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="SuperGame"
        )
        response = self.client.get(f"/polecacz/game/{game.id}/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_game"])
        self.assertContains(response, "SuperGame", html=True)
        self.assertContains(response, "Detale gry", html=True)
        self.assertContains(
            response, f"<strong>Ranking:</strong>{game.rank}", html=True
        )
        self.assertContains(
            response,
            f"<strong>Minimalna liczba graczy:</strong>{game.min_players}",
            html=True,
        )
        self.assertContains(
            response,
            f"<strong>Maksymalna liczba graczy:</strong>{game.max_players}",
            html=True,
        )
        self.assertContains(
            response, f"<strong>Rok wydania:</strong>{game.year_published}", html=True
        )
        self.assertContains(
            response, f"<strong>Designer:</strong>{game.designer}", html=True
        )
        self.assertContains(
            response, f"<strong>Artysta:</strong>{game.artist}", html=True
        )
        self.assertContains(response, "Tag1", html=True)
        self.assertContains(response, "Tag2", html=True)
        self.assertContains(response, "Tag3", html=True)


class GameListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_game_list_view(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="SuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="SuperGame2"
        )
        response = self.client.get("/polecacz/game/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertContains(response, "Lista gier", html=True)
        self.assertContains(response, "SuperGame", html=True)
        self.assertContains(response, "SuperGame2", html=True)
        self.assertContains(
            response, f"<strong>Ranking:</strong>{game1.rank}", html=True
        )
        self.assertContains(
            response, f"<strong>Ranking:</strong>{game2.rank}", html=True
        )
        self.assertContains(
            response,
            f"<strong>Minimalna liczba graczy:</strong>{game1.min_players}",
            html=True,
        )
        self.assertContains(
            response,
            f"<strong>Maksymalna liczba graczy:</strong>{game1.max_players}",
            html=True,
        )
        self.assertContains(
            response, f"<strong>Rok wydania:</strong>{game1.year_published}", html=True
        )
        self.assertContains(
            response,
            f"<strong>Minimalna liczba graczy:</strong>{game2.min_players}",
            html=True,
        )
        self.assertContains(
            response,
            f"<strong>Maksymalna liczba graczy:</strong>{game2.max_players}",
            html=True,
        )
        self.assertContains(
            response, f"<strong>Rok wydania:</strong>{game2.year_published}", html=True
        )
        self.assertContains(response, "Dodaj grę do listy preferencji", html=True)
        self.assertContains(response, "Dodaj grę do listy posiadanych gier", html=True)
        self.assertContains(response, "Ranking rosnąco", html=True)
        self.assertTrue(response.context["object_list"][0] == game1)

    def test_game_list_view_order_alphabetic(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        response = self.client.get("/polecacz/game/?ordering=name")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertContains(response, "Lista gier", html=True)
        self.assertContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertContains(response, "Alfabetycznie A-Z", html=True)
        self.assertTrue(response.context["object_list"][0] == game2)

    def test_game_list_view_search(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        response = self.client.get("/polecacz/game/?game_name=Zuper")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertContains(response, "Lista gier", html=True)
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context["object_list"][0] == game1)
        self.assertTrue(len(response.context["object_list"]) == 1)

    def test_game_list_view_search_with_selected_mechanics(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        response = self.client.get(
            "/polecacz/game/?game_name=Zuper&selected_mechanics=Tag1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertContains(response, "Lista gier", html=True)
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context["object_list"][0] == game1)
        self.assertTrue(len(response.context["object_list"]) == 1)

    def test_game_list_view_search_with_selected_categories(self):
        game1 = GameFactory(tags=["Tag1"], rank=1, rating=9.02, name="ZuperGame")
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        response = self.client.get(
            "/polecacz/game/?game_name=Zuper&selected_categories=Tag1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context["object_list"][0] == game1)
        self.assertTrue(len(response.context["object_list"]) == 1)

    def test_game_list_view_search_with_selected_categories_and_mechanics(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        response = self.client.get(
            "/polecacz/game/?game_name=Zuper&selected_categories=Tag1&selected_mechanics=Tag2"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context["object_list"][0] == game1)
        self.assertTrue(len(response.context["object_list"]) == 1)

    def test_game_list_view_with_selected_categories_and_mechanics(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        game3 = GameFactory(tags=["Tag3"], rank=3, rating=8.00, name="NotFilteredGame")
        response = self.client.get(
            "/polecacz/game/?selected_categories=Tag1&selected_mechanics=Tag2"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["selected_games"])
        self.assertContains(response, game1.name, html=True)
        self.assertContains(response, game2.name, html=True)
        self.assertNotContains(response, game3.name, html=True)
        self.assertTrue(response.context["object_list"][0] == game1)
        self.assertTrue(len(response.context["object_list"]) == 2)


class GameSearchTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_game_search_returns_proper_data(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )

        response = self.client.get("/polecacz/game_search/?game_name=Zu")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name)
        self.assertNotContains(response, game2.name)

        response = self.client.get("/polecacz/game_search/?game_name=u")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name)
        self.assertContains(response, game2.name)

        response = self.client.get("/polecacz/game_search/?game_name=test")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, game1.name)
        self.assertNotContains(response, game2.name)

    def test_game_search_post_405(self):
        response = self.client.post("/polecacz/game_search/?game_name=Zu")
        self.assertEqual(response.status_code, 405)


class SelectedGamesListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_selected_games_list_view_selected_games_created(self):
        with self.assertRaises(SelectedGames.DoesNotExist):
            SelectedGames.objects.get(user__username="testuser")

        response = self.client.get("/polecacz/selected_games/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(SelectedGames.objects.get(user__username="testuser"))

    def test_selected_games_list_view_shows_selected_games(self):
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        response = self.client.get("/polecacz/selected_games/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name, html=True)
        self.assertNotContains(response, game2.name, html=True)


class OwnedGamesListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_owned_games_list_view_owned_games_created(self):
        with self.assertRaises(OwnedGames.DoesNotExist):
            OwnedGames.objects.get(user__username="testuser")

        response = self.client.get("/polecacz/owned_games/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(OwnedGames.objects.get(user__username="testuser"))

    def test_owned_games_list_view_shows_owned_games(self):
        owned_games_obj = OwnedGames.objects.create(user=self.user)
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        owned_games_obj.owned_games.add(game1)
        owned_games_obj.save()

        response = self.client.get("/polecacz/owned_games/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name, html=True)
        self.assertNotContains(response, game2.name, html=True)


class AddToOwnedGamesTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_add_to_owned_games_adds_game(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        response = self.client.get(f"/polecacz/add_game_to_owned/{game1.id}/")
        owned_games_obj = OwnedGames.objects.get(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 in owned_games_obj.owned_games.all())

    def test_add_to_owned_games_proper_redirect(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        response = self.client.get(
            f"/polecacz/add_game_to_owned/{game1.id}/?ordering=rank&page=2&game_name=&selected_categories=Tag1&selected_mechanics=Tag2"
        )
        owned_games_obj = OwnedGames.objects.get(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 in owned_games_obj.owned_games.all())
        self.assertEqual(
            response.url,
            "/polecacz/game/?&ordering=rank&page=2&selected_categories=Tag1&selected_mechanics=Tag2",
        )

    def test_add_to_owned_games_post_405(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        response = self.client.post(f"/polecacz/add_game_to_owned/{game1.id}/")
        self.assertEqual(response.status_code, 405)


class RemoveFromOwnedGamesTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_remove_from_owned_games_removes_game(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        owned_games_obj = OwnedGames.objects.create(user=self.user)
        owned_games_obj.owned_games.add(game1)
        owned_games_obj.save()

        response = self.client.get(f"/polecacz/remove_game_from_owned/{game1.id}/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 not in owned_games_obj.owned_games.all())

    def test_remove_from_owned_games_proper_redirect(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        owned_games_obj = OwnedGames.objects.create(user=self.user)
        owned_games_obj.owned_games.add(game1)
        owned_games_obj.save()

        response = self.client.get(
            f"/polecacz/remove_game_from_owned/{game1.id}/?ordering=rank&page=2&game_name=&selected_categories=Tag1&selected_mechanics=Tag2/"
        )
        owned_games_obj = OwnedGames.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 not in owned_games_obj.owned_games.all())
        self.assertEqual(
            response.url,
            "/polecacz/game/?&ordering=rank&page=2&selected_categories=Tag1&selected_mechanics=Tag2/",
        )

    def test_remove_from_owned_games_post_405(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )

        response = self.client.post(f"/polecacz/remove_game_from_owned/{game1.id}/")
        self.assertEqual(response.status_code, 405)


class AddToSelectedGamesTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_add_to_selected_games_adds_game(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        response = self.client.get(f"/polecacz/add_game_to_selected/{game1.id}/")
        selected_games_obj = SelectedGames.objects.get(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 in selected_games_obj.selected_games.all())

    def test_add_to_selected_games_proper_redirect(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        response = self.client.get(
            f"/polecacz/add_game_to_selected/{game1.id}/?ordering=rank&page=2&game_name=&selected_categories=Tag1&selected_mechanics=Tag2/"
        )
        selected_games_obj = SelectedGames.objects.get(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 in selected_games_obj.selected_games.all())
        self.assertEqual(
            response.url,
            "/polecacz/game/?&ordering=rank&page=2&selected_categories=Tag1&selected_mechanics=Tag2/",
        )

    def test_add_to_selected_games_post_405(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        response = self.client.post(f"/polecacz/add_game_to_selected/{game1.id}/")
        self.assertEqual(response.status_code, 405)


class RemoveFromSelectedGamesTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_remove_from_selected_games_removes_game(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        response = self.client.get(f"/polecacz/remove_game_from_selected/{game1.id}/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 not in selected_games_obj.selected_games.all())

    def test_remove_from_selected_games_proper_redirect(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        response = self.client.get(
            f"/polecacz/remove_game_from_selected/{game1.id}/?ordering=rank&page=2&game_name=&selected_categories=Tag1&selected_mechanics=Tag2/"
        )
        selected_games_obj = SelectedGames.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 not in selected_games_obj.selected_games.all())
        self.assertEqual(
            response.url,
            "/polecacz/game/?&ordering=rank&page=2&selected_categories=Tag1&selected_mechanics=Tag2/",
        )

    def test_remove_from_selected_games_post_405(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )

        response = self.client.post(f"/polecacz/remove_game_from_selected/{game1.id}/")
        self.assertEqual(response.status_code, 405)


class RecommendationListViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_recommendations_list_shows_all_recommendations(self):
        recommendation = Recommendation.objects.create(user=self.user)
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        for game in [game1, game2]:
            recommendation.selected_games.add(game)
        game3 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3", "Tag4"],
            rank=3,
            rating=8.00,
            name="AuperGame3",
        )
        recommendation.recommended_games.add(game3)
        recommendation.save()

        response = self.client.get(f"/polecacz/recommendation/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dodaj opinię dla rekomendacji")
        self.assertTrue(len(response.context["object_list"]) == 1)

        recommendation.opinion_created = True
        recommendation.save()
        response = self.client.get(f"/polecacz/recommendation/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Dodaj opinię dla rekomendacji")
        self.assertContains(response, "Opinia została już dodana")
        self.assertTrue(len(response.context["object_list"]) == 1)


class RecommendationDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_recommendation_detail(self):
        recommendation = Recommendation.objects.create(user=self.user)
        game1 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=1, rating=9.02, name="ZuperGame"
        )
        game2 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"], rank=2, rating=9.00, name="AuperGame2"
        )
        for game in [game1, game2]:
            recommendation.selected_games.add(game)
        game3 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3", "Tag4"],
            rank=3,
            rating=8.00,
            name="AuperGame3",
        )
        recommendation.recommended_games.add(game3)
        recommendation.save()

        response = self.client.get(f"/polecacz/recommendation/{recommendation.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Oto Twoja rekomendacja")
        self.assertContains(response, game1.thumbnail)
        self.assertContains(response, game2.thumbnail)
        self.assertContains(response, game3.thumbnail)
        self.assertTrue(game1 in response.context["selected_games"])
        self.assertTrue(game2 in response.context["selected_games"])
        self.assertTrue(game3 not in response.context["selected_games"])
        self.assertTrue(game3 in response.context["recommended_games"])
        self.assertEqual(response.context["opinion_created"], False)
        self.assertEqual(response.context["id"], recommendation.id)


class OpinionFormViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_opinion_form_view_shows_form(self):
        recommendation = Recommendation.objects.create(user=self.user)
        response = self.client.get(f"/polecacz/opinion/{recommendation.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zostaw opinie")
        self.assertContains(response, "Ocena:")
        self.assertContains(response, "Uwagi do rekomendacji:")


class OpinionCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_opinion_create_view(self):
        recommendation = Recommendation.objects.create(user=self.user)
        self.assertFalse(recommendation.opinion_created)
        response = self.client.post(
            f"/polecacz/opinion/create/{recommendation.id}/",
            data={"description": "TestDescription", "rating": 2},
        )
        self.assertEqual(response.status_code, 302)
        opinion = Opinion.objects.get(recommendation=recommendation)
        recommendation = Recommendation.objects.get(id=recommendation.id)
        self.assertTrue(recommendation.opinion_created)
        self.assertEqual(opinion.description, "TestDescription")
        self.assertEqual(opinion.rating, 2)
        self.assertEqual(opinion.user, self.user)

    def test_opinion_create_view_returns_errors(self):
        recommendation = Recommendation.objects.create(user=self.user)
        response = self.client.post(
            f"/polecacz/opinion/create/{recommendation.id}/",
            data={"description": "T" * 1000, "rating": 2},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Popraw następujące pola")
        self.assertContains(
            response, "Upewnij się, że ta wartość ma co najwyżej 500 znaków"
        )

        recommendation = Recommendation.objects.create(user=self.user)
        response = self.client.post(
            f"/polecacz/opinion/create/{recommendation.id}/",
            data={"description": "T" * 10, "rating": 12},
        )
        self.assertContains(response, "Popraw następujące pola")
        self.assertContains(
            response, "Upewnij się, że ta wartość jest mniejsza lub równa 10"
        )


class RecommendationCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")

    def test_create_recommendation_get_405(self):
        response = self.client.get(f"/polecacz/create_recommendation/")
        self.assertEqual(response.status_code, 405)

    def test_create_recommendation_create_recommendations(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2"], rank=1, rating=9.02, name="ZuperGame1"
        )
        game2 = GameFactory(tags=["Tag3"], rank=2, rating=9.01, name="ZuperGame2")
        game3 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"],
            rank=5,
            rating=8.92,
            name="SuperRecommendation",
        )
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.selected_games.add(game2)
        selected_games_obj.save()

        response = self.client.post(f"/polecacz/create_recommendation/")
        self.assertEqual(response.status_code, 302)

        recommendation = Recommendation.objects.filter(user=self.user).first()
        self.assertEqual(response.url, f"/polecacz/recommendation/{recommendation.id}/")
        self.assertEqual(len(recommendation.recommended_games.all()), 1)
        self.assertTrue(game3 in recommendation.recommended_games.all())

        selected_games_obj = SelectedGames.objects.get(id=selected_games_obj.id)
        self.assertEqual(len(selected_games_obj.selected_games.all()), 0)

    def test_create_recommendation_create_recommendations_excludes_owned_game(self):
        game1 = GameFactory(
            tags=["Tag1", "Tag2"], rank=1, rating=9.02, name="ZuperGame1"
        )
        game2 = GameFactory(tags=["Tag2"], rank=2, rating=9.01, name="ZuperGame2")
        game3 = GameFactory(
            tags=["Tag1", "Tag2", "Tag3"],
            rank=5,
            rating=8.92,
            name="SuperRecommendation",
        )
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        owned_games_obj = OwnedGames.objects.create(user=self.user)
        owned_games_obj.owned_games.add(game2)
        owned_games_obj.save()

        response = self.client.post(f"/polecacz/create_recommendation/")
        self.assertEqual(response.status_code, 302)

        recommendation = Recommendation.objects.filter(user=self.user).first()
        self.assertEqual(response.url, f"/polecacz/recommendation/{recommendation.id}/")
        self.assertEqual(len(recommendation.recommended_games.all()), 1)
        self.assertTrue(game3 in recommendation.recommended_games.all())
        self.assertTrue(game2 not in recommendation.recommended_games.all())

        selected_games_obj = SelectedGames.objects.get(id=selected_games_obj.id)
        self.assertEqual(len(selected_games_obj.selected_games.all()), 0)


class TestRemoveImageView(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")
        self.game1 = GameFactory(
            tags=["Tag1", "Tag2"], rank=1, rating=9.02, name="ZuperGame1"
        )
        self.path_to_image = "test/itest/image.jpg"
        self.token = 'token123'
        self.image_name = 'image.jpg'
        self.image_metadata = ImageMetadata.objects.create(user=self.user, game=self.game1, download_token=self.token, image_name=self.image_name)

    @patch("polecacz.service.FirebaseStorageService.remove_image")
    @patch("polecacz.service.pyrebase")
    def test_image_removed_successfully(self, mocked_pyrebase, mocked_remove_image):
        image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name=self.image_name,
                                                      download_token=self.token).first()
        self.assertTrue(image_metadata)
        response = self.client.get(f"/polecacz/remove_image/{self.game1.id}/?image_name={self.image_name}")
        image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name=self.image_name,
                                                      download_token=self.token).first()
        self.assertFalse(image_metadata)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/polecacz/game/{self.game1.id}/")


class TestAddImageView(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user.set_password("12345")
        self.user.save()
        self.client.login(username="testuser", password="12345")
        self.game1 = GameFactory(
            tags=["Tag1", "Tag2"], rank=1, rating=9.02, name="ZuperGame1"
        )
        self.path_to_image = "test/itest/image.jpg"
        self.token = 'token123'

    @patch("polecacz.service.FirebaseStorageService.insert_image")
    @patch("polecacz.service.pyrebase")
    def test_add_image_successfully(self, mocked_pyrebase, mocked_insert_image):
        with open(self.path_to_image, 'rb') as file:
            mocked_insert_image.return_value = {'downloadTokens': self.token}
            image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name='image.jpg', download_token=self.token).first()
            self.assertFalse(image_metadata)
            response = self.client.post(f"/polecacz/add_image/{self.game1.id}/", {'uploaded_file': file})
            self.assertEqual(response.status_code, 302)
            image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name='image.jpg', download_token=self.token).first()
            self.assertTrue(image_metadata)
            self.assertEqual(response.url, f"/polecacz/game/{self.game1.id}/")

    @patch("polecacz.views.validate_file_size")
    @patch("polecacz.service.FirebaseStorageService.insert_image")
    @patch("polecacz.service.pyrebase")
    def test_image_size_too_big(self, mocked_pyrebase, mocked_insert_image, mocked_file_size_validator):
        with open(self.path_to_image, 'rb') as file:
            mocked_file_size_validator.side_effect = TooBigFileException()
            mocked_insert_image.return_value = {'downloadTokens': self.token}
            image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name='image.jpg', download_token=self.token).first()
            self.assertFalse(image_metadata)
            response = self.client.post(f"/polecacz/add_image/{self.game1.id}/", {'uploaded_file': file})
            self.assertEqual(response.status_code, 302)
            image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name='image.jpg', download_token=self.token).first()
            self.assertFalse(image_metadata)
            self.assertEqual(response.url, f"/polecacz/game/{self.game1.id}/")

    @patch("polecacz.views.validate_file_extension")
    @patch("polecacz.service.FirebaseStorageService.insert_image")
    @patch("polecacz.service.pyrebase")
    def test_image_wrong_extension(self, mocked_pyrebase, mocked_insert_image, mocked_file_extension_validator):
        with open(self.path_to_image, 'rb') as file:
            mocked_file_extension_validator.side_effect = ValidationError('Unsupported file extension.')
            mocked_insert_image.return_value = {'downloadTokens': self.token}
            image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name='image.jpg', download_token=self.token).first()
            self.assertFalse(image_metadata)
            response = self.client.post(f"/polecacz/add_image/{self.game1.id}/", {'uploaded_file': file})
            self.assertEqual(response.status_code, 302)
            image_metadata = ImageMetadata.objects.filter(user=self.user, game=self.game1, image_name='image.jpg', download_token=self.token).first()
            self.assertFalse(image_metadata)
            self.assertEqual(response.url, f"/polecacz/game/{self.game1.id}/")
