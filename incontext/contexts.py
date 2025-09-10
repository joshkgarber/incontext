from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

bp = Blueprint('contexts', __name__, url_prefix='/contexts')


@bp.route('/')
@login_required
def index():
    db = get_db()
    contexts = db.execute(
        'SELECT c.id, name, description, created, creator_id, username'
        ' FROM contexts c JOIN users u ON c.creator_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('contexts/index.html', contexts=contexts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None

        if not name or not description:
            error = 'Name and description are required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO contexts (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            db.commit()
            return redirect(url_for('contexts.index'))

    return render_template('contexts/create.html')


@bp.route("/<int:context_id>/view", methods=("GET",))
@login_required
def view(context_id):
    context = get_context(context_id)
    lists = get_context_lists(context_id)
    agents = get_context_agents(context_id)
    return render_template("contexts/view.html", context=context)


def get_context(context_id, check_author=True): # The check_author parameter means this function is also useful for getting the context in general, not just for the update view e.g. displaying a single context on a "view context" page.
    context = get_db().execute(
        'SELECT c.id, name, description, created, creator_id, username'
        ' FROM contexts c JOIN users u ON c.creator_id = u.id'
        ' WHERE c.id = ?',
        (context_id,)
    ).fetchone()

    if context is None:
        abort(404, f"Context id {id} doesn't exist.") # abort() will raise a special exception that returns an HTTP status code. It takes an optional message to show with the error. 404 means "Not Found".

    if check_author and context['creator_id'] != g.user['id']:
        abort(403) # 403 means Forbidden. 401 means "Unauthorized" but you redirect to the login page instead of returning that status.

    return context


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id): # id corresponds to the <int:id> in the route. Flask will capture the "id" from the url, ensure it's an int, and pass it as the id argument. To generate a URL to the update page, `url_for()` needs to be passed the `id` such as `url_for('context.update', id=context['id']).
    context = get_context(id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None

        if not name or not description:
            error = 'Name and description are required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE contexts SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, id)
            )
            db.commit()
            return redirect(url_for('contexts.index'))
    
    return render_template('contexts/update.html', context=context)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_context(id)
    db = get_db()
    db.execute('DELETE FROM contexts WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('contexts.index'))


def get_context_lists(context_id):
    db = get_db()
    lists = db.execute(
        "SELECT r.list_id, l.name, l.description"
        " FROM context_list_relations r"
        " JOIN lists l ON l.id = r.list_id"
        " WHERE context_id = ?",
        (context_id,)
    ).fetchall()
    return lists


def get_context_agents(context_id):
    db = get_db()
    agents = db.execute(
        "SELECT r.agent_id, a.name, a.description"
        " FROM context_agent_relations r"
        " JOIN agents a ON a.id = r.agent_id"
        " WHERE context_id = ?",
        (context_id,)
    ).fetchall()
