from installies.models.app import App
from installies.models.script import Script
from installies.models.supported_distros import SupportedDistro
from installies.models.maintainer import Maintainer, Maintainers
from installies.models.user import User
from installies.groups.base import Group
from installies.groups.modifiers import (
    SearchableField,
    SearchInFields,
    BySupportedDistro,
    Paginate,
    BySupportedAction,
    BySupportedShell,
)
from datetime import datetime


class ScriptGroup(Group):
    """
    A class for getting multiple Script objects from the database.
    """

    model = Script

    @classmethod
    def get(cls, params, query=None):
        # gets the base query
        if query is None:
            query = cls.model.select()

        # gets the script by a certain field
        if params.get('id', '') is not '':
            query = query.where(
                (cls.model.id == params.get('id'))
            )

        if params.get('version', '') is not '':
            query = query.where(
                (cls.model.version == params.get('version'))
            )

        if params.get('last_modified', '') is not '':
            query = query.where(
                (cls.model.last_modified == datetime.fromisoformat(params.get('last_modified')))
            )

        if params.get('creation_date', '') is not '':
            query = query.where(
                (cls.model.creation_date == datetime.fromisoformat(params.get('creation_date')))
            )

        # sorts the query
        sort_by = params.get('sort-by', 'last_modified')
        order_by = params.get('order-by', 'desc')

        # the field to sort the object by
        sort_by_field = None

        # gets the field to sort by
        match sort_by:
            case 'version':
                sort_by_field = cls.model.version
            case 'last_modified':
                sort_by_field = cls.model.last_modified
            case 'creation_date':
                sort_by_field = cls.model.creation_date
            case 'submitter':
                sort_by_field = cls.model.submitter
            case _:
                sort_by_field = cls.model.last_modified

        # orders and sorts the query
        if order_by == 'desc':
            query = query.order_by(sort_by_field.desc())
        else:
            query = query.order_by(sort_by_field)

        # gets the scripts by supported distro
        query = BySupportedDistro().modify(query, params)
        query = query.switch(cls.model)
        
        # gets the scripts by supported shell
        query = BySupportedShell().modify(query, params)
        query = query.switch(cls.model)
        
        # gets the scripts by search
        search_modifier = SearchInFields(
            model = cls.model,
            searchable_fields = [
                SearchableField(
                    'description',
                    lambda model, name, data: model.description.contains(data),
                ),
                SearchableField(
                    'maintainers',
                    lambda model, name, data: Maintainer.user.username.contains(data),
                    models=[Maintainers, Maintainer, User],
                ),
                SearchableField(
                    'submitter',
                    lambda model, name, data: getattr(model, name).username.contains(data),
                    models=[User]
                ),
            ],
            default_field = 'maintainers',
        )

        query = search_modifier.modify(query, params)
        query = query.switch(cls.model)

        return query.distinct()
