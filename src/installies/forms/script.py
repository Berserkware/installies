from flask import g
from installies.forms.base import Form, FormInput
from installies.validators.script import (
    ScriptActionValidator,
    ScriptShellValidator,
    ScriptDistroValidator,
    ScriptContentValidator,
    ScriptDistroDictionaryValidator,
    ScriptDescriptionValidator,
    ScriptVersionValidator,
)
from installies.models.supported_distros import SupportedDistro
from installies.models.app import App
from installies.models.script import Script


class ModifyScriptForm(Form):
    """
    A form for adding or editing app scripts.
    """

    inputs = [
        FormInput(
            'script-actions',
            ScriptActionValidator,
            lambda action_string: [x.strip() for x in action_string.split(',')],
            default='',
        ),
        FormInput(
            'script-shell',
            ScriptShellValidator,
        ),
        FormInput(
            'script-supported-distros',
            ScriptDistroDictionaryValidator,
            SupportedDistro.get_dict_from_string,
            '',
        ),
        FormInput('script-content', ScriptContentValidator),
        FormInput(
            'script-description',
            ScriptDescriptionValidator,
            original_data_getter=lambda script: script.description,
        ),
        FormInput('for-version', ScriptVersionValidator, default=None),
        FormInput('script-use-default-function-matcher', default=None),
    ]
    model = Script


class CreateScriptForm(ModifyScriptForm):
    """A form for creating Scripts."""

    model = Script
    
    def save(self, app: App):
        script = Script.create(
            content=self.data['script-content'],
            shell=self.data['script-shell'],
            description=self.data['script-description'],
            submitter=g.user,
            app=app,
            version=self.data['for-version'],
            actions=self.data['script-actions'],
            use_default_function_matcher=(True if self.data.get('script-use-default-function-matcher') is not None else False),
        )

        distros = SupportedDistro.create_from_dict(script, self.data['script-supported-distros'])

        return script


class EditScriptForm(ModifyScriptForm):
    """A form for editing Scripts."""

    edit_form = True
    
    def save(self, script: Script):
        for distro in script.supported_distros:
            distro.delete_instance()
        
        SupportedDistro.create_from_dict(
            script,
            self.data['script-supported-distros']
        )
        
        return script.edit(
            shell=self.data['script-shell'],
            content=self.data['script-content'],
            description=self.data['script-description'],
            version=self.data['for-version'],
            use_default_function_matcher=(True if self.data.get('script-use-default-function-matcher') is not None else False),
            actions=self.data['script-actions'],
        )
