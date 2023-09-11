from flask import g
from installies.forms.base import Form, FormInput
from installies.validators.script import (
    ScriptActionValidator,
    ScriptShellValidator,
    ScriptDistroValidator,
    ScriptContentValidator,
    ScriptDistroDictionaryValidator,
    ScriptMethodValidator,
    ScriptVersionValidator,
)
from installies.models.supported_distros import SupportedDistrosJunction
from installies.models.app import App
from installies.models.script import Script


class ModifyScriptForm(Form):
    """
    A form for adding or editing scripts.
    """

    inputs = [
        FormInput(
            'script-actions',
            ScriptActionValidator,
            lambda action_string: [x.strip() for x in action_string.split(',')],
            default='',
        ),
        FormInput(
            'script-shells',
            ScriptShellValidator,
            lambda shell_string: [x.strip() for x in shell_string.split(',')],
            default='bash',
        ),
        FormInput(
            'script-supported-distros',
            ScriptDistroDictionaryValidator,
            SupportedDistrosJunction.get_from_string,
            '',
        ),
        FormInput('script-content', ScriptContentValidator),
        FormInput(
            'script-method',
            ScriptMethodValidator,
            original_data_getter=lambda script: script.script_data.method,
        ),
        FormInput('for-version', ScriptVersionValidator, default=None)
    ]
    model = Script


class AddScriptForm(ModifyScriptForm):
    """A form for adding scripts."""

    def save(self, app: App):
        return Script.create(
            supported_distros=self.data['script-supported-distros'],
            content=self.data['script-content'],
            app=app,
            version=self.data['for-version'],
            actions=self.data['script-actions'],
            shells=self.data['script-shells'],
            method=self.data['script-method'],
            submitter=g.user,
        )


class EditScriptForm(ModifyScriptForm):
    """A form for editing scripts."""

    edit_form = True
    
    def save(self):
        return self.original_object.edit(
            actions=self.data['script-actions'],
            shells=self.data['script-shells'],
            supported_distros=self.data['script-supported-distros'],
            content=self.data['script-content'],
            version=self.data['for-version'],
            method=self.data['script-method'],
        )
