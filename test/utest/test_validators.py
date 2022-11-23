from django.test import TestCase
from django.core.exceptions import ValidationError

from polecacz.validators import validate_file_size, validate_file_extension, TooBigFileException


class UserRegistrationFormTests(TestCase):

    def test_file_extension_is_correct(self):
        filenames=['file.jpg', 'file.png']
        for filename in filenames:
            validate_file_extension(file_name=filename)

    def test_file_extension_is_not_correct(self):
        with self.assertRaises(ValidationError):
            filename='file.txt'
            validate_file_extension(file_name=filename)
        with self.assertRaises(ValidationError):
            filename = 'file.pdf'
            validate_file_extension(file_name=filename)

    def test_file_size_is_correct(self):
        filesizes=[1, 100, 1000, 6291455]
        for filesize in filesizes:
            validate_file_size(file_size=filesize)

    def test_file_size_is_not_correct(self):
        with self.assertRaises(TooBigFileException):
            filesize = 6291457
            validate_file_size(file_size=filesize)