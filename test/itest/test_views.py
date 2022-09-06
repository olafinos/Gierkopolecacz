from http import HTTPStatus

from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from unittest.mock import patch, ANY
from django.contrib.auth.models import User
from django.test import TestCase


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
    def test_activate_correct_token(self, mocked_token):
        mocked_token.return_value = False
        user = User.objects.create(username='username', password='password', email='email@email.com', is_active = False)
        encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.post(f"/activate/{encoded_id}/invalid_token")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'polecacz/')
        user = User.objects.get(username='username')
        self.assertFalse(user.is_active)








