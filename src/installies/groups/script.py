from installies.models.app import App
from installies.models.script import Script
from installies.models.supported_distros import SupportedDistro
from installies.models.maintainer import Maintainer, Maintainers
from installies.models.user import User
from installies.groups.base import Group
from installies.groups.modifiers import (
    JoinModifier,
    SortBy,
    ByColumn,
    SearchableAttribute,
    SearchInAttributes,
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

    modifiers = [
        SortBy(
            model = Script,
            allowed_attributes = [
                'version',
                'last_modified',
                'creation_date',
                'submitter',
            ],
            default_attribute = 'last_modified',
            default_order = 'asc',
        ),
        ByColumn(
            model = Script,
            param_name = 'id',
            attribute = 'id'
        ),
        ByColumn(
            model = Script,
            param_name = 'version',
            attribute = 'version'
        ),
        ByColumn(
            model = Script,
            param_name = 'last_modified',
            attribute = 'last_modified',
            converter = datetime.fromisoformat,
        ),
        ByColumn(
            model = Script,
            param_name = 'creation_date',
            attribute = 'last_modified',
            converter = datetime.fromisoformat,
        ),
        SearchInAttributes(
            model = Script,
            searchable_attributes = [
                SearchableAttribute(
                    'method',
                    lambda model, name, data: model.method.contains(data),
                ),
                SearchableAttribute(
                    'maintainers',
                    lambda model, name, data: Maintainer.user.username.contains(data),
                    models=[Maintainers, Maintainer, User],
                ),
                SearchableAttribute(
                    'submitter',
                    lambda model, name, data: getattr(model, name).username.contains(data),
                    models=[User]
                ),
            ],
            default_attribute = 'maintainers',
        ),
        BySupportedDistro(),
        BySupportedAction(),
        BySupportedShell(),
    ]
    model = Script
