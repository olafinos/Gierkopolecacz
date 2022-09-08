from http import HTTPStatus
from unittest.mock import patch, ANY

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.models import User
from django.test import TestCase

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

    @patch('gierkopolecacz.views.activate_email')
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


class UserPolecaczTests(TestCase):

    def setUp(self) -> None:
        user = User.objects.create(username='testuser')
        user.set_password('12345')
        user.save()
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
        self.assertContains(response, 'AuperGame2', html=True)
        self.assertContains(response, 'ZuperGame', html=True)
        self.assertContains(response, 'Alfabetycznie A-Z', html=True)
        self.assertTrue(response.context['object_list'][0] == game2)

    def test_game_list_view_search(self):
        game1 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=1,rating=9.02, name='ZuperGame')
        game2 = GameFactory(tags=['Tag1', 'Tag2', 'Tag3'], rank=2,rating=9.00, name='AuperGame2')
        response = self.client.get('/polecacz/game/?game=Zuper')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['selected_games'])
        self.assertContains(response, 'Lista gier', html=True)
        self.assertNotContains(response, 'AuperGame2', html=True)
        self.assertContains(response, 'ZuperGame', html=True)
        self.assertTrue(response.context['object_list'][0] == game1)
        self.assertTrue(len(response.context['object_list']) == 1)