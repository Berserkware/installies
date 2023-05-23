import bleach
import json
import os

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    g,
    abort,
    flash,
    url_for
)
from installies.apps.app_manager.upload import (
    get_distros_from_string,
)
from installies.lib.validate import ValidationError
from installies.apps.app_manager.validate import (
    AppNameValidator,
    AppDescriptionValidator,
    AppVisibilityValidator,
    ScriptActionValidator,
    ScriptDistroValidator,
    ScriptContentValidator
)
from installies.apps.app_manager.groups import ScriptGroup
from installies.config import (
    supported_script_actions,
    supported_visibility_options,
)
from installies.apps.app_manager.models import App, Script, Maintainer
from installies.apps.auth.models import User
from installies.apps.auth.decorators import authenticated_required
from installies.apps.app_manager.form import (
    CreateAppForm,
    EditAppForm,
    ChangeAppVisibilityForm,
    AddScriptForm,
    EditScriptForm,
)
from installies.lib.view import View, FormView, AuthenticationRequiredMixin
from peewee import JOIN


class AppMixin:
    """
    A mixin for getting apps by url params.

    It gets the app slug from the app_slug kwarg.
    """

    public_only = False
    
    def on_request(self, **kwargs):
        app_slug = kwargs.get('app_slug')

        if app_slug is None:
            abort(404)

        app = App.select().where(App.slug == app_slug)

        if app.exists() is False:
            abort(404)

        app = app.get()
        
        if self.public_only and app.visibility != 'public':
            abort(404)

        kwargs['app'] = app
        
        return super().on_request(**kwargs)


class CreateAppFormView(AuthenticationRequiredMixin, FormView):
    """A view for creating an app."""

    template_path = 'create_app.html'
    form_class = CreateAppForm

    def form_valid(self, form, **kwargs):
         app = form.save()

         flash('App successfully created.', 'success')
         return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

app_manager = Blueprint('app_manager', __name__)

app_manager.add_url_rule('/create-app', 'create_app', view_func=CreateAppFormView.as_view(), methods=['GET', 'POST'])

@app_manager.route('/apps/<slug>', methods=['GET', 'POST'])
def app_view(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    return render_template('app_view/info.html', app=app)


@app_manager.route('/apps/<slug>/delete', methods=['GET', 'POST'])
@authenticated_required()
def app_delete(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot delete an app that you are not a maintainer of.',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        app.delete_instance()
        flash('App successfully deleted!', 'success')
        return redirect('/', 303)

    return render_template('app_view/delete.html', app=app)


@app_manager.route('/apps/<slug>/edit', methods=['GET', 'POST'])
@authenticated_required()
def app_edit(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot edit an app that you are not a maintainer of.',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        form = EditAppForm(request.form)

        if form.is_valid() is False:
            flash(form.error, 'error')
            return redirect(url_for('app_manager.app_edit', slug=app.slug), 303)

        form.save()

        flash('App succesfully edited.', 'success')
        return redirect(url_for('app_manager.app_view', slug=slug), 303)
    
    return render_template('app_view/edit.html', app=app)


@app_manager.route('/apps/<slug>/change-visibility', methods=['GET', 'POST'])
@authenticated_required()
def change_visibility(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot edit an app that you are not a maintainer of.',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        form = ChangeAppVisibilityForm(request.form)

        if form.is_valid() is False:
            flash(form.error, 'error')
            return redirect(url_for('app_manager.change_visibility', slug=app.slug), 303)

        # if app has no scripts, dont allow to make public
        if form.data['visibility'] != 'private' and len(app.scripts) == 0:
            flash('App must have at least one script to be made public', 'error')
            return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

        form.save()

        flash(f'App visibility successfully changed to {form.data["visibility"]}.', 'success')
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    return render_template(
        'app_view/change_visibility.html',
        app=app,
        visibility_options=supported_visibility_options,
    )

@app_manager.route('/apps/<slug>/add-maintainer', methods=['GET', 'POST'])
def add_maintainer(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)

    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot add a maintainer to an app that you are not a maintainer of.',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        username = request.form.get('username').strip()

        user = User.select().where(User.username == username)

        if user.exists() is False:
            flash(f'{username} does not exist.', 'error')
            return redirect(url_for('app_manager.add_maintainer', slug=app.slug), 303)

        user = user.get()
        
        if (Maintainer.select()
            .where(Maintainer.user == user)
            .where(Maintainer.app == app)
            .exists()):
            flash(f'{user.username} is already a maintainer.', 'error')
            return redirect(url_for('app_manager.add_maintainer', slug=app.slug), 303)

        maintainer = Maintainer.create(user=user, app=app)

        flash(f'{user.username} successfully added as a maintainer.', 'success')
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    return render_template('app_view/add_maintainer.html', app=app)

@app_manager.route('/apps/<slug>/maintainer/<username>/remove', methods=['GET', 'POST'])
def remove_maintainer(slug, username):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)

    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot remove a maintainer from an app that you are not a maintainer of.',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    user = User.select().where(User.username == username)

    if user.exists() is False:
        abort(404)

    user = user.get()

    maintainer = (
        Maintainer
        .select()
        .where(Maintainer.user == user)
        .where(Maintainer.app == app)
    )

    if maintainer.exists() is False:
        abort(404)

    maintainer = maintainer.get()
    
    if request.method == 'POST':
        if len(app.maintainers) == 1:
            flash(f'You cannot remove the last maintainer.', 'error')
            return redirect(url_for('app_manager.app_view', slug=app.slug), 303)
        
        maintainer.delete_instance()

        flash(f'Maintainer successfully removed.', 'success')
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    return render_template('app_view/remove_maintainer.html', user=user, app=app)

@app_manager.route('/apps/<slug>/scripts')
def app_scripts(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)

    scripts = ScriptGroup.get(**request.args).where(Script.app == app)
    
    return render_template(
        'app_view/scripts.html',
        app=app,
        scripts=scripts,
        supported_script_actions=supported_script_actions,
    )

@app_manager.route('/apps/<slug>/scripts/<int:script_id>')
def script_view(slug, script_id):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)

    script = Script.get_by_id(script_id)

    return render_template(
        'app_view/script_info.html',
        app=app,
        script=script,
    )

@app_manager.route('/apps/<slug>/add-script', methods=['get', 'post'])
@authenticated_required()
def add_script(slug):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot add a script to an app that you are not a maintainer of.',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        form = AddScriptForm(request.form)

        if form.is_valid() is False:
            flash(form.error, 'error')
            return redirect(url_for('app_manager.add_script', slug=app.slug))
        
        form.save(app=app)

        flash('Script successfully created.', 'success')
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    return render_template(
        'app_view/add_script.html',
        app=app,
        possible_script_actions=supported_script_actions
    )


@app_manager.route('/apps/<slug>/scripts/<int:script_id>/delete')
@authenticated_required()
def delete_script(slug, script_id):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    script = Script.get_by_id(script_id)
    
    if app.submitter != app.can_user_edit(g.user) is False:
        flash(
            'You cannot delete a script of an app that you are not a maintainer of..',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        script.delete_instance()
        flash('Script successfully deleted.', 'success')
        return redirect(url_for('app_mananger.app_view', slug=app.slug), 303)
    
    return render_template('app_view/delete_script.html', app=app, script=script)


@app_manager.route('/apps/<slug>/scripts/<int:script_id>/edit', methods=['GET', 'POST'])
@authenticated_required()
def edit_script(slug, script_id):
    app = App.get_by_slug(slug)

    if app.visibility == 'private' and app.can_user_edit(g.user) is False:
        abort(404)
    
    script = Script.get_by_id(script_id)
    
    if app.can_user_edit(g.user) is False:
        flash(
            'You cannot edit a script of an app that you are not a maintainer of',
            'error'
        )
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)

    if request.method == 'POST':
        form = EditScriptForm(request.form)

        if form.is_valid() is False:
            flash(form.error, 'error')
            return redirect(url_for('app_manager.add_script', slug=app.slug), 303)

        form.save(script=script)

        flash('Script successfully edited.', 'success')
        return redirect(url_for('app_manager.app_view', slug=app.slug), 303)
    
    return render_template(
        'app_view/edit_script.html',
        app=app,
        script=script,
        possible_script_actions=supported_script_actions,
    )
