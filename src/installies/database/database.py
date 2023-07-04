from installies.config import database
from installies.models.app import App, Maintainer
from installies.models.script import Script
from installies.models.supported_distros import Distro, SupportedDistro, Architechture, AlternativeArchitechtureName
from installies.models.user import User
from installies.models.report import AppReport, ScriptReport


def create_database():
    """Create tables in database."""
    with database:
        database.create_tables(
            [
                User,
                App,
                Script,
                Distro,
                SupportedDistro,
                Maintainer,
                Architechture,
                AlternativeArchitechtureName,
                AppReport,
                ScriptReport,
            ]
        )


def drop_database():
    """Drop tables in database."""
    with database:
        database.drop_tables(
            [
                User,
                App,
                Script,
                Distro,
                SupportedDistro,
                Maintainer,
                Architechture,
                AlternativeArchitechtureName,
                AppReport,
                ScriptReport,
            ]
        )


def recreate_database():
    """Drop and recreates the database tables."""
    drop_database()
    create_database()
