import string
import typing as t

from peewee import DoesNotExist

class EmptyChecker:
    """A checker class that checks if a string is empty."""

    def check(self, data: str):
        """
        Check if data string is empty.

        A ValueError is raised if data is empty.

        :param data: The data to check.
        """
        if data is None or data.strip() == '' or data == []:
            raise ValueError(
                '{} cannot be empty.'
            )


class LengthChecker:
    """
    A class that checks the length of a string.

    :param max_len: The max length of the string.
    :param min_len: The minimium length of the string.
    """

    def __init__(self, max_len=None, min_len=None):
        self.max_len = max_len
        self.min_len = min_len

    def check(self, data: str):
        """
        Check the length of a data string.

        A ValueError is raised if the data is too long or short.

        :param data: The data to check.
        """
        if self.max_len is not None and len(data) > self.max_len:
            raise ValueError(
                '{} ' + f'must not contain more than {self.max_len} characters.'
            )

        if self.min_len is not None and len(data) < self.min_len:
            raise ValueError(
                '{} ' + f'must contain at least {self.min_len} characters.'
            )


class AllowedCharactersChecker:
    """
    A class that checks that a string only contains a set of characters.

    :param allow_spaces: Allow spaces.
    :param allow_lowercase: Allow lowercase letters.
    :param allow_uppercase: Allow uppercase letters.
    :param allow_numbers: Allow numbers.
    :param allow_extra: A list of extra characters to allow.
    """

    def __init__(
        self,
        allow_spaces=True,
        allow_lowercase=True,
        allow_uppercase=True,
        allow_numbers=True,
        allow_extra=[]
    ):
        self.allowed_characters = []

        if allow_spaces:
            self.allowed_characters.extend(' ')

        if allow_lowercase:
            self.allowed_characters.extend(string.ascii_lowercase)

        if allow_uppercase:
            self.allowed_characters.extend(string.ascii_uppercase)

        if allow_numbers:
            self.allowed_characters.extend(string.digits)

        self.allowed_characters.extend(allow_extra)

    def check(self, data: str):
        """
        Check that only allowed characters in data string.

        Raises ValueError if data contains characters that are not allowed.

        :param data: The data string to check.
        """
        for char in data:
            if char not in self.allowed_characters:
                raise ValueError(
                    '{} ' + f'cannot contain character "{char}".'
                )


class DisallowedCharactersChecker:
    """
    A checker that checks that a string does not contain certain charecters.

    :param disallowed_characters: The characters that are not allowed.
    """

    def __init__(self, disallowed_characters=[]):
        self.disallowed_characters = disallowed_characters

    def check(self, data: str):
        """
        Check that no disallowed characters in data string.

        Raises ValueError if data contains characters that are not allowed.

        :param data: The data string to check.
        """
        for char in data:
            if char in self.allowed_characters:
                raise ValueError(
                    '{}' + f'cannot contain character "{char}".'
                )


class ExistsInDatabaseChecker:
    """
    A checker that checks that a string does not exist in the database.

    :param table: The table to check in.
    :param column_name: The name of the column to check in.
    :param data_modifier: A callable to modify the data before checking it in
        the database.
    """

    def __init__(
        self,
        table,
        column_name: str,
        data_modifier: t.Callable=None
    ):
        self.table = table
        self.column_name = column_name
        self.data_modifier = data_modifier

    def check(self, data: str):
        """
        Check that data string does not exist in the database.

        A ValueError is raised if the string exists in the database.

        :param data: The data string to check.
        """
        if self.data_modifier is not None:
            data = self.data_modifier(data)

        try:
            self.table.get(getattr(self.table, self.column_name) == data)
        except DoesNotExist:
            return

        raise ValueError(
            '{} already exists.'
        )


class NotInContainerChecker:
    """
    A checker that checks that a string is in a container.

    :param container: The container to check that a string is in.
    :param container_name: The name of the container the data needs to be in.
    """

    def __init__(self, container, container_name: str):
        self.container = container
        self.container_name = container_name

    def check(self, data: str):
        """
        Check that a data string exists in the database.

        A ValueError is raised if the string is not in the container.

        :param data: The data string to check.
        """
        if data not in self.container:
            raise ValueError('{} ' + f'must be in {self.container_name}.')
