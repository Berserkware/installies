from flask import g
from installies.lib.form import Form, FormInput
from installies.blueprints.app_manager.validate import (
    AppNameValidator,
    AppDisplayNameValidator,
    AppDescriptionValidator,
    AppCurrentVersionValidator,
    AppVersionRegexValidator,
    AppVisibilityValidator,
    ScriptActionValidator,
    ScriptDistroValidator,
    ScriptContentValidator,
    ScriptDistroDictionaryValidator,
    ScriptVersionValidator,
    ReportTitleValidator,
    ReportBodyValidator,
    ThreadTitleValidator,
    CommentContentValidator,
)
from installies.blueprints.app_manager.upload import get_distros_from_string
from installies.models.app import App
from installies.models.script import AppScript
from installies.models.report import AppReport
from installies.models.discussion import Thread, Comment

class CreateAppForm(Form):
    """
    A form for creating apps.
    """

    inputs = [
        FormInput('app-name', AppNameValidator, default=''),
        FormInput('app-display-name', AppDisplayNameValidator, default=None),
        FormInput('app-desc', AppDescriptionValidator, default=''),
        FormInput('app-current-version', AppCurrentVersionValidator, default=None),
        FormInput('app-version-regex', AppVersionRegexValidator, default=None),
    ]
    model = App

    def save(self):
        """Creates the app."""
        return App.create(
            name=self.data['app-name'],
            display_name=self.data['app-display-name'],
            description=self.data['app-desc'],
            current_version=self.data['app-current-version'],
            version_regex=self.data['app-version-regex'],
            submitter=g.user,
        )


class EditAppForm(Form):
    """
    A form for editing apps.
    """

    inputs = [
        FormInput('app-display-name', AppDisplayNameValidator, default=None),
        FormInput('app-desc', AppDescriptionValidator, default=''),
        FormInput('app-current-version', AppCurrentVersionValidator, default=None),
        FormInput('app-version-regex', AppVersionRegexValidator, default=None),
    ]
    model = App

    def save(self, app):
        """Edits the app."""
        return app.edit(
            display_name=self.data['app-display-name'],
            description=self.data['app-desc'],
            current_version=self.data['app-current-version'],
            version_regex=self.data['app-version-regex'],
        )
    


class ChangeAppVisibilityForm(Form):
    """
    A form for changing the visibility of apps.
    """

    inputs = [
        FormInput('visibility', AppVisibilityValidator)
    ]
    model = App

    def save(self, app: App):
        """Changes the app visibility."""
        app.visibility = self.data['visibility']
        app.save()
        return app


class ModifyScriptForm(Form):
    """
    A form for adding or editing scripts.
    """

    inputs = [
        FormInput('script-action', ScriptActionValidator, default=''),
        FormInput(
            'script-supported-distros',
            ScriptDistroDictionaryValidator,
            get_distros_from_string,
            '',
        ),
        FormInput('script-content', ScriptContentValidator),
        FormInput('for-version', ScriptVersionValidator, default=None)
    ]
    model = AppScript


class AddScriptForm(ModifyScriptForm):
    """A form for adding scripts."""

    def save(self, app: App):
        return AppScript.create(
            action=self.data['script-action'],
            supported_distros=self.data['script-supported-distros'],
            content=self.data['script-content'],
            app=app,
            version=self.data['for-version']
        )


class EditScriptForm(ModifyScriptForm):
    """A form for editing scripts."""

    def save(self, script: AppScript):
        return script.edit(
            action=self.data['script-action'],
            supported_distros=self.data['script-supported-distros'],
            content=self.data['script-content'],
            version=self.data['for-version'],
        )


class CreateReportBaseForm(Form):
    """A form to create reports."""
    
    inputs = [
        FormInput('title', ReportTitleValidator),
        FormInput('body', ReportBodyValidator),
    ]


class ReportAppForm(CreateReportBaseForm):
    """A form to report apps."""

    model = App

    def save(self, app: App):
        return AppReport.create(
            title=self.data['title'],
            body=self.data['body'],
            submitter=g.user,
            app=app,
        )


class CreateThreadForm(Form):
    """A form to create threads."""

    inputs = [
        FormInput('title', ThreadTitleValidator)
    ]
    
    model = Thread

    def save(self, app: App):
        return Thread.create(
            title=self.data['title'],
            app=app,
            creator=g.user,
        )


class CommentForm(Form):
    """A base form for creating or editing comments."""

    inputs = [
        FormInput('content', CommentContentValidator)
    ]

    model = Comment

    
class CreateCommentForm(CommentForm):
    """A form to create comments."""

    def save(self, thread: Thread):
        return Comment.create(
            thread=thread,
            creator=g.user,
            content=self.data['content'],
        )


class EditCommentForm(CommentForm):
    """A form to edit comments"""

    def save(self, comment: Comment):
        comment.content = self.data['content']
        comment.edited = True
        comment.save()
        return comment
