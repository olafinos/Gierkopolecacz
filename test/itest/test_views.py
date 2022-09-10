from datetime import datetime
from http import HTTPStatus
from unittest.mock import patch, ANY

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.models import User
from django.test import TestCase

from polecacz.models import SelectedGames, Recommendation
from test.factories.game import GameFactory


class UserViewTests(TestCase):

    def test_signup_not_valid_data(self):
        username = 'a' * 200
        response = self.client.post("/signup", data={'username': username,
                                                     'password1': 'validpassword1',
                                                     'password2': 'validpassword1',
                                                     'email': 'valid@email.com'
                                                     })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Upewnij się, że ta wartość ma co najwyżej 150 znaków (obecnie ma 200).', html=True)

    @patch('gierkopolecacz.views.send_activation_email')
    def test_signup_valid_data(self, mocked_email):
        response = self.client.post("/signup", data={'username': 'valid_username',
                                                     'password1': 'validpassword1',
                                                     'password2': 'validpassword1',
                                                     'email': 'valid@email.com'
                                                     })
        # call(WSGIRequest: POST '/signup'), call(User: valid_username)
        mocked_email.assert_called_with(ANY, ANY, 'valid@email.com')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/polecacz/')
        user = User.objects.get(username='valid_username')
        self.assertFalse(user.is_active)

    @patch('django.core.mail.EmailMessage.send')
    def test_activate_email(self, mocked_email):
        response = self.client.post("/signup", data={'username': 'valid_username1',
                                                     'password1': 'validpassword1',
                                                     'password2': 'validpassword1',
                                                     'email': 'valid@email.com'
                                                     })
        mocked_email.assert_called_with()

    @patch('gierkopolecacz.views.account_activation_token.check_token')
    def test_activate_correct_token(self, mocked_token):
        mocked_token.return_value = True
        user = User.objects.create(username='username', password='password', email='email@email.com', is_active = False)
        encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.post(f"/activate/{encoded_id}/token")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/login/')
        user = User.objects.get(username='username')
        self.assertTrue(user.is_active)

    @patch('gierkopolecacz.views.account_activation_token.check_token')
    def test_activate_uncorrect_token(self, mocked_token):
        mocked_token.return_value = False
        user = User.objects.create(username='username', password='password', email='email@email.com', is_active = False)
        encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.post(f"/activate/{encoded_id}/invalid_token")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'polecacz/')
        user = User.objects.get(username='username')
        self.assertFalse(user.is_active)


class PolecaczViewsTests(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(username='testuser')
        self.user.set_password('12345')
        self.user.save()
        self.client.login(username='testuser', password='12345')

    def test_index_view(self):
        for i in range(15):
            GameFactory()
        response = self.client.get('/polecacz/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['object_list']) == 12)

    def test_game_detail_view(self):
        game = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='SuperGame')
        response = self.client.get(f'/polecacz/game/{game.id}/', follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_game'])
        self.assertContains(response, 'SuperGame', html=True)
        self.assertContains(response, 'Detale gry', html=True)
        self.assertContains(response, f'<strong>Ranking:</strong>{game.rank}', html= True)
        self.assertContains(response, f'<strong>Minimalna liczba graczy:</strong>{game.min_players}', html=True)
        self.assertContains(response, f'<strong>Maksymalna liczba graczy:</strong>{game.max_players}', html=True)
        self.assertContains(response, f'<strong>Rok wydania:</strong>{game.year_published}', html=True)
        self.assertContains(response, f'<strong>Designer:</strong>{game.designer}', html=True)
        self.assertContains(response, f'<strong>Artysta:</strong>{game.artist}', html=True)
        self.assertContains(response, 'Tag1', html=True)
        self.assertContains(response, 'Tag2', html=True)
        self.assertContains(response, 'Tag3', html=True)

    def test_game_list_view(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='SuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2,rating=9.00, name='SuperGame2')
        response = self.client.get('/polecacz/game/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertContains(response, 'Lista gier', html=True)
        self.assertContains(response, 'SuperGame', html=True)
        self.assertContains(response, 'SuperGame2', html=True)
        self.assertContains(response, f'<strong>Ranking:</strong>{game1.rank}', html= True)
        self.assertContains(response, f'<strong>Ranking:</strong>{game2.rank}', html= True)
        self.assertContains(response, f'<strong>Minimalna liczba graczy:</strong>{game1.min_players}', html=True)
        self.assertContains(response, f'<strong>Maksymalna liczba graczy:</strong>{game1.max_players}', html=True)
        self.assertContains(response, f'<strong>Rok wydania:</strong>{game1.year_published}', html=True)
        self.assertContains(response, f'<strong>Minimalna liczba graczy:</strong>{game2.min_players}', html=True)
        self.assertContains(response, f'<strong>Maksymalna liczba graczy:</strong>{game2.max_players}', html=True)
        self.assertContains(response, f'<strong>Rok wydania:</strong>{game2.year_published}', html=True)
        self.assertContains(response, 'Dodaj grę do listy preferencji', html=True)
        self.assertContains(response, 'Ranking rosnąco', html=True)
        self.assertTrue(response.context['object_list'][0] == game1)

    def test_game_list_view_order_alphabetic(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2,rating=9.00, name='AuperGame2')
        response = self.client.get('/polecacz/game/?ordering=name')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertContains(response, 'Lista gier', html=True)
        self.assertContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertContains(response, 'Alfabetycznie A-Z', html=True)
        self.assertTrue(response.context['object_list'][0] == game2)

    def test_game_list_view_search(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2,rating=9.00, name='AuperGame2')
        response = self.client.get('/polecacz/game/?game_name=Zuper')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertContains(response, 'Lista gier', html=True)
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context['object_list'][0] == game1)
        self.assertTrue(len(response.context['object_list']) == 1)

    def test_game_list_view_search_with_selected_mechanics(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2,rating=9.00, name='AuperGame2')
        response = self.client.get('/polecacz/game/?game_name=Zuper&selected_mechanics=Tag1')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertContains(response, 'Lista gier', html=True)
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context['object_list'][0] == game1)
        self.assertTrue(len(response.context['object_list']) == 1)

    def test_game_list_view_search_with_selected_categories(self):
        game1 = GameFactory(tags=['Tag1'], rank=1,rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1','Tag2', 'Tag3'], rank=2,rating=9.00, name='AuperGame2')
        response = self.client.get('/polecacz/game/?game_name=Zuper&selected_categories=Tag1')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context['object_list'][0] == game1)
        self.assertTrue(len(response.context['object_list']) == 1)

    def test_game_list_view_search_with_selected_categories_and_mechanics(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2,rating=9.00, name='AuperGame2')
        response = self.client.get('/polecacz/game/?game_name=Zuper&selected_categories=Tag1&selected_mechanics=Tag2')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertNotContains(response, game2.name, html=True)
        self.assertContains(response, game1.name, html=True)
        self.assertTrue(response.context['object_list'][0] == game1)
        self.assertTrue(len(response.context['object_list']) == 1)

    def test_game_list_view_with_selected_categories_and_mechanics(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2, rating=9.00, name='AuperGame2')
        game3 = GameFactory(tags=['Tag3'], rank=3, rating=8.00, name='NotFilteredGame')
        response = self.client.get('/polecacz/game/?selected_categories=Tag1&selected_mechanics=Tag2')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertContains(response, game1.name, html=True)
        self.assertContains(response, game2.name, html=True)
        self.assertNotContains(response, game3.name, html=True)
        self.assertTrue(response.context['object_list'][0] == game1)
        self.assertTrue(len(response.context['object_list']) == 2)

    def test_game_search_returns_proper_data(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2, rating=9.00, name='AuperGame2')

        response = self.client.get('/polecacz/game_search/?game_name=Zu')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name)
        self.assertNotContains(response, game2.name)

        response = self.client.get('/polecacz/game_search/?game_name=u')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name)
        self.assertContains(response, game2.name)

        response = self.client.get('/polecacz/game_search/?game_name=test')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, game1.name)
        self.assertNotContains(response, game2.name)

    def test_game_search_post_redirects(self):
        response = self.client.post('/polecacz/game_search/?game_name=Zu')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/polecacz/game_list')

    def test_selected_games_list_view_selected_games_created(self):
        with self.assertRaises(SelectedGames.DoesNotExist):
            SelectedGames.objects.get(user__username='testuser')

        response = self.client.get('/polecacz/selected_games/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(SelectedGames.objects.get(user__username='testuser'))

    def test_selected_games_list_view_shows_selected_games(self):
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2, rating=9.00, name='AuperGame2')
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        response = self.client.get('/polecacz/selected_games/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, game1.name, html=True)
        self.assertNotContains(response, game2.name, html=True)

    def test_add_to_selected_games_adds_game(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        response = self.client.get(f'/polecacz/add_game_to_selected/{game1.id}')
        selected_games_obj = SelectedGames.objects.get(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 in selected_games_obj.selected_games.all())

    def test_add_to_selected_games_proper_redirect(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        response = self.client.get(f'/polecacz/add_game_to_selected/{game1.id}?ordering=rank&page=2&game_name=&selected_categories=Tag1&selected_mechanics=Tag2')
        selected_games_obj = SelectedGames.objects.get(user=self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 in selected_games_obj.selected_games.all())
        self.assertEqual(response.url,'/polecacz/game/?&ordering=rank&page=2&selected_categories=Tag1&selected_categories=Tag2')

    def test_add_to_selected_games_post_redirects(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        response = self.client.post(f'/polecacz/add_game_to_selected/{game1.id}')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/polecacz/game_list')

    def test_remove_to_selected_games_removes_game(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        response = self.client.get(f'/polecacz/remove_game_from_selected/{game1.id}')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 not in selected_games_obj.selected_games.all())

    def test_remove_to_selected_games_proper_redirect(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        selected_games_obj = SelectedGames.objects.create(user=self.user)
        selected_games_obj.selected_games.add(game1)
        selected_games_obj.save()

        response = self.client.get(f'/polecacz/remove_game_from_selected/{game1.id}?ordering=rank&page=2&game_name=&selected_categories=Tag1&selected_mechanics=Tag2')
        selected_games_obj = SelectedGames.objects.get(user=self.user)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(game1 not in selected_games_obj.selected_games.all())
        self.assertEqual(response.url,'/polecacz/game/?&ordering=rank&page=2&selected_categories=Tag1&selected_categories=Tag2')

    def test_remove_to_selected_games_post_redirects(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')

        response = self.client.post(f'/polecacz/remove_game_from_selected/{game1.id}')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/polecacz/game_list')

    def test_recommendations_list_shows_all_recommendations(self):
        recommendation = Recommendation.objects.create(user=self.user)
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2, rating=9.00, name='AuperGame2')
        for game in [game1,game2]:
            recommendation.selected_games.add(game)
        game3 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3', 'Tag4'], rank=3, rating=8.00, name='AuperGame3')
        recommendation.recommended_games.add(game3)
        recommendation.save()

        response = self.client.get(f'/polecacz/recommendation/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dodaj opinię dla rekomendacji')
        self.assertTrue(len(response.context['object_list']) == 1)

        recommendation.opinion_created = True
        recommendation.save()
        response = self.client.get(f'/polecacz/recommendation/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Dodaj opinię dla rekomendacji')
        self.assertContains(response, 'Opinia została już dodana')
        self.assertTrue(len(response.context['object_list']) == 1)

    def test_recommendation_detail(self):
        recommendation = Recommendation.objects.create(user=self.user)
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1, rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2, rating=9.00, name='AuperGame2')
        for game in [game1, game2]:
            recommendation.selected_games.add(game)
        game3 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3', 'Tag4'], rank=3, rating=8.00, name='AuperGame3')
        recommendation.recommended_games.add(game3)
        recommendation.save()

        response = self.client.get(f'/polecacz/recommendation/{recommendation.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oto Twoja rekomendacja')
        self.assertContains(response, game1.thumbnail)
        self.assertContains(response, game2.thumbnail)
        self.assertContains(response, game3.thumbnail)
        self.assertTrue(game1 in response.context['selected_games'])
        self.assertTrue(game2 in response.context['selected_games'])
        self.assertTrue(game3 not in response.context['selected_games'])
        self.assertTrue(game3 in response.context['recommended_games'])
        self.assertEqual(response.context['opinion_created'], False)
        self.assertEqual(response.context['id'], recommendation.id)

    def test_opinion_form_view_shows_form(self):
        recommendation = Recommendation.objects.create(user=self.user)
        response = self.client.get(f'/polecacz/opinion/{recommendation.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zostaw opinie')
        self.assertContains(response, 'Ocena:')
        self.assertContains(response, 'Uwagi do rekomendacji:')


    def test_opinion_create_view(self): # TO BE CONTINUED
        recommendation = Recommendation.objects.create(user=self.user)
        response = self.client.post(f'/polecacz/opinion/create/{recommendation.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zostaw opinie')
        self.assertContains(response, 'Ocena:')
        self.assertContains(response, 'Uwagi do rekomendacji:')

