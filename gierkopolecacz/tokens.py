from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
import six


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Creates token which is needed for account activation
    """

    def _make_hash_value(self, user: User, timestamp):
        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.is_active)
        )


account_activation_token = AccountActivationTokenGenerator()
