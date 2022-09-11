from django.test import TestCase

from gierkopolecacz.forms import UserRegistrationForm


class UserRegistrationFormTests(TestCase):
    valid_username = "valid_username"
    valid_password = "validpassword1"
    valid_email = "valid@email.com"

    def test_username_too_long(self):
        username = "a" * 200
        form = UserRegistrationForm(
            data={
                "username": username,
                "password1": self.valid_password,
                "password2": self.valid_password,
                "email": self.valid_email,
            }
        )
        self.assertEqual(
            form.errors["username"],
            ["Upewnij się, że ta wartość ma co najwyżej 150 znaków (obecnie ma 200)."],
        )

    def test_email_not_valid(self):
        email = "abc"
        form = UserRegistrationForm(
            data={
                "email": email,
                "password1": self.valid_password,
                "password2": self.valid_password,
                "username": self.valid_username,
            }
        )
        self.assertEqual(form.errors["email"], ["Wprowadź poprawny adres email."])

    def test_passwords_are_not_equal(self):
        password1 = "abc12345"
        password2 = "eabc12345"
        form = UserRegistrationForm(
            data={
                "password1": password1,
                "password2": password2,
                "username": self.valid_username,
                "email": self.valid_email,
            }
        )
        self.assertEqual(
            form.errors["password2"], ["Hasła w obu polach nie są zgodne."]
        )
