class Group:
    """
    A class for getting multiple objects from the database.

    This is a base class that needs to be inherited to work. The derivitive classes
    should have a model attribute with the model that the group is of. It should
    also have a list of Modifier classes named 'modifiers'.
    """

    modifiers = []
    model = None

    @classmethod
    def get(cls, **kwargs):
        """
        Gets a group of objects from the database.

        It uses the Modifier classes in the 'modifier' attribute. If the model in
        the `model` attribute is none, then an empty list is returned.
        """

        if cls.model is None:
            return []

        query = cls.model.select()

        for modifier in cls.modifiers:
            query = modifier.modify(query, **kwargs)

        return query

        