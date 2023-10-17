import bleach
import json
import os
import re
import math
import io

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    g,
    abort,
    flash,
    url_for,
    send_file,
)
from installies.validators.base import ValidationError
from installies.validators.script import (
    ScriptActionValidator,
    ScriptDistroValidator,
    ScriptContentValidator,
)
from installies.groups.script import ScriptGroup
from installies.models.app import App
from installies.models.maintainer import Maintainer, Maintainers
from installies.models.script import AppScript, Script, Shell
from installies.models.user import User
from installies.forms.script import (
    CreateScriptForm,
    CreateAppScriptForm,
    EditScriptForm,
)
from installies.lib.view import (
    View,
    FormView,
    EditFormView,
    AuthenticationRequiredMixin,
    TemplateView,
    ListView,
    DetailView,
)
from peewee import JOIN, DoesNotExist
from installies.blueprints.admin.views import AdminRequiredMixin
from installies.groups.modifiers import Paginate
from installies.blueprints.app_manager.app import (
    AppMixin,
)


class ScriptMixin:
    """
    A mixin to get Scripts by url params.

    It gets the script's id from the script_id kwarg.
    """

    script_maintainer_only = False

    def on_request(self, **kwargs):
        script_id = kwargs['script_id']

        script = Script.select().where(Script.id == script_id)

        if script.exists() is False:
            abort(404)

        script = script.get()

        if kwargs['app'] != script.app_data.get().app:
            abort(404)

        if script.can_user_edit(g.user) is False and self.script_maintainer_only:
            flash(
                'You do not have permission to do that.',
                'error'
            )
            return redirect(url_for('app_manager.app_scripts', app_name=kwargs['app'].name), 303)

        kwargs['script'] = script

        return super().on_request(**kwargs)

    def get_script_view_redirect(self, **kwargs):
        """Gets the redirect to the script view page."""
        script = kwargs['script']
        return redirect(
            url_for('app_manager.script_view', app_name=kwargs['app'].name, script_id=script.id),
            303
        )


class AppScriptMixin:
    """
    A mixin to get AppScripts by url_params.

    It gets the AppScript's id from the script_id kwarg.
    """

    script_maintainer_only = False

    def on_request(self, **kwargs):
        app_script_id = kwargs['app_script_id']

        app_script = AppScript.select().where(AppScript.id == app_script_id)

        if app_script.exists() is False:
            abort(404)

        app_script = app_script.get()

        if kwargs['app'] != app_script.app:
            abort(404)

        if app_script.script.can_user_edit(g.user) is False and self.script_maintainer_only:
            flash(
                'You do not have permission to do that.',
                'error'
            )
            return redirect(url_for('app_manager.app_scripts', app_name=kwargs['app'].name), 303)

        kwargs['app_script'] = app_script

        return super().on_request(**kwargs)


    def get_script_view_redirect(self, **kwargs):
        """Gets the redirect to the script view page."""
        app_script = kwargs['app_script']
        return redirect(
            url_for('app_manager.script_view', app_name=kwargs['app'].name, app_script_id=app_script.id),
            303
        )


class ScriptListView(AppMixin, ListView):
    """A view for listing scripts"""

    template_path = 'app/script/app_scripts.html'
    group_name = 'scripts'
    paginator = Paginate(
        default_per_page = 10,
        max_per_page = 50,
    )

    def get_group(self, **kwargs):
        group = ScriptGroup.get(
            request.args,
            query=(
                Script
                .select()
                .join(AppScript)
                .where(AppScript.app == kwargs['app'])
                .switch(Script)
            )
        )
        
        return group


class ScriptDetailView(AppMixin, AppScriptMixin, DetailView):
    """A view for getting the details of a script."""

    template_path = 'app/script/info.html'
    model_name = 'script'

    def get_object(self, **kwargs):
        return kwargs['app_script']


class ScriptDownloadView(AppMixin, AppScriptMixin, View):
    """A view for getting the content of scripts."""

    def get(self, **kwargs):
        app_script = kwargs['app_script']
        content = app_script.script.complete_content(request.args.get('version'))
        script_file = io.BytesIO(content.encode('utf-8'))
        return send_file(
            script_file,
            mimetype=app_script.script.shell.file_mimetype,
            download_name=f'{app_script.app.name}.{app_script.script.shell.file_extension}',
            as_attachment=True
        )
    

class AddScriptFormView(AuthenticationRequiredMixin, AppMixin, FormView):
    """A view for adding apps."""

    template_path = 'app/script/add_script.html'
    form_class = CreateAppScriptForm

    def form_valid(self, form, **kwargs):
        app_script = form.save(app=kwargs['app'])
        
        flash('Script successfully created.', 'success')
        return redirect(
            url_for(
                'app_manager.script_view',
                app_name=kwargs['app'].name,
                script_id=app_script.script.id
            ),
            303
        )


class EditScriptFormView(AuthenticationRequiredMixin, AppMixin, AppScriptMixin, EditFormView):
    """A view for editing scripts."""

    template_path = 'app/script/edit_script.html'
    script_maintainer_only = True
    form_class = EditScriptForm
    
    def get_object_to_edit(self, **kwargs):
        return kwargs['app_script'].script
    
    def form_valid(self, form, **kwargs):
        form.save()

        flash('Script successfully edited.', 'success')
        return self.get_script_view_redirect(**kwargs)


class DeleteScriptView(AuthenticationRequiredMixin, AppMixin, AppScriptMixin, TemplateView):
    """A view for deleting scripts."""

    template_path = 'app/script/delete_script.html'
    script_maintainer_only = True

    def post(self, **kwargs):
        app_script = kwargs['app_script']
        app_script.delete_instance()
        flash('Script successfully deleted.', 'success')
        return self.get_app_view_redirect(**kwargs)


class AddScriptMaintainerView(AuthenticationRequiredMixin, AppMixin, AppScriptMixin, TemplateView):
    """A view for adding maintainers to scripts."""

    template_path = 'app/script/add_maintainer.html'
    script_maintainer_only = True

    def post(self, **kwargs):
        username = request.form.get('username').strip()

        user = User.select().where(User.username == username)

        if user.exists() is False:
            flash(f'{username} is not a user.', 'error')
            return self.get(**kwargs)

        user = user.get()
        script = kwargs['app_script'].script
        
        if script.maintainers.is_maintainer(user):
            flash(f'{user.username} is already a maintainer.', 'error')
            return redirect(
                url_for(
                    'app_manager.add_script_maintainer',
                    app_name=app.name,
                    script_id=script.id,
                ),
                303
            )

        maintainer = script.maintainers.add_maintainer(user)

        flash(f'{user.username} successfully added as a maintainer.', 'success')
        return self.get_script_view_redirect(**kwargs)


class RemoveScriptMaintainerView(AuthenticationRequiredMixin, AppMixin, AppScriptMixin, TemplateView):
    """A view for removing a maintainer."""

    template_path = 'app/script/remove_maintainer.html'
    maintainer_only = True

    def on_request(self, **kwargs):
        user = User.select().where(User.username == kwargs['username'])

        if user.exists() is False:
            abort(404)

        user = user.get()

        kwargs['user'] = user

        return super().on_request(**kwargs)
    
    def post(self, **kwargs):
        script = kwargs['app_script'].script

        if len(script.maintainers.get_maintainers()) == 1:
            flash(f'You cannot remove the last maintainer.', 'error')
            return self.get_script_view_redirect(**kwargs)

        if script.maintainers.is_maintainer(kwargs['user']) is False:
            abort(404)
            
        script.maintainers.delete_maintainer(kwargs['user'])
        
        flash(f'Maintainer successfully removed.', 'success')
        return self.get_script_view_redirect(**kwargs)
