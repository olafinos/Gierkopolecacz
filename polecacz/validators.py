import os
from django.core.exceptions import ValidationError


class TooBigFileException(Exception):
    pass


def validate_file_extension(file_name):
    ext = os.path.splitext(file_name)[1]
    valid_extensions = ['.jpg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


def validate_file_size(file_size):
    if file_size > 6291456:  # Value which corresponds to 6 Megabytes
        raise TooBigFileException
