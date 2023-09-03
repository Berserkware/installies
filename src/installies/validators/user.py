from installies.validators.base import Validator
from installies.validators.check import (
    EmptyChecker,
    LengthChecker,
    CharacterWhitelistChecker,
    UniqueChecker,
    EmailChecker,
)
from installies.models.user import User


class UsernameValidator(Validator):
    """A class for validating usernames submitted by users."""

    checkers = [
        EmptyChecker(),
        LengthChecker(max_len=32),
        CharacterWhitelistChecker(
            allow_extra=['-', '_', '<', '>', '!']
        ),
        UniqueChecker(table=User, column_name='username'),
    ]

    data_name = 'Username'


class EmailValidator(Validator):
    """A class for validating passwords submitted by users."""

    checkers = [
        EmptyChecker(),
        EmailChecker(),
        UniqueChecker(User, 'email'),
    ]

    data_name = 'Email'


class PasswordValidator(Validator):
    """A class for validating passwords submitted by users."""

    checkers = [
        EmptyChecker(),
        LengthChecker(max_len=32)
    ]

    data_name = 'Password'


class PasswordConfirmValidator(Validator):
    """A class for validating password confirms submitted by users."""

    checkers = [
        EmptyChecker(),
    ]

    data_name = 'Password Confirm'
