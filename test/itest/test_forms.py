from http import HTTPStatus

from django.test import TestCase


class UserRegistrationFormTests(TestCase):
    valid_username = 'valid_username'
    valid_password = 'validpassword1'
    valid_email = 'valid@email.com'

    def test_username_too_long(self):
        username = 'a' * 200
        response = self.client.post("/signup", data={'username': username,
                                                     'password1': self.valid_password,
                                                     'password2': self.valid_password,
                                                     'email': self.valid_email
                                                     })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response,
                         'Upewnij się, że ta wartość ma co najwyżej 150 znaków (obecnie ma 200).', html=True)

    def test_email_not_valid(self):
        email = 'abc'
        response = self.client.post("/signup", data={'email': email,
                                                     'password1': self.valid_password,
                                                     'password2': self.valid_password,
                                                     'username': self.valid_username
                                                     })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Wprowadź poprawny adres email.', html=True)

    def test_passwords_are_not_equal(self):
        password1 = 'abc12345'
        password2 = 'eabc12345'
        response = self.client.post("/signup", data={'password1':password1,
                                                     'password2':password2,
                                                     'username': self.valid_username,
                                                     'email': self.valid_email
                                                     })
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Hasła w obu polach nie są zgodne.', html=True)

    def test_get(self):
        response = self.client.get("/signup")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "<h2>Zarejestruj się</h2>", html=True)

    def test_post_success(self):
        response = self.client.post("/signup",
                                    data={"username": self.valid_username,
                                          "email": self.valid_email,
                                          "password1": self.valid_password,
                                          "password2": self.valid_password})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response["Location"], "/polecacz/")

    def test_post_error(self):
        response = self.client.post("/signup", data={"email": "mailniepoprawny",
                                                     "password1": self.valid_password,
                                                     "password2": self.valid_password,
                                                     "username": self.valid_username
                                                     })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Wprowadź poprawny adres email.", html=True)
