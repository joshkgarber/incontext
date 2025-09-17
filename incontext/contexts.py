from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db, dict_factory
from incontext.lists import get_user_lists, get_list
from incontext.agents import get_agents, get_agent


bp = Blueprint('contexts', __name__, url_prefix='/contexts')


@bp.route("/")
@login_required
def index():
    db = get_db()
    contexts = db.execute(
        "SELECT c.id, name, description, created, creator_id, username"
        " FROM contexts c JOIN users u ON c.creator_id = u.id"
        " WHERE creator_id = ?"
        " ORDER BY created DESC",
        (g.user["id"],)
    ).fetchall()
    return render_template('contexts/index.html', contexts=contexts)


@bp.route("/new", methods=("GET", "POST"))
@login_required
def new():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        error = None
        if not name or not description:
            error = "Name and description are required."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO contexts (name, description, creator_id)"
                " VALUES (?, ?, ?)",
                (name, description, g.user["id"])
            )
            db.commit()
            return redirect(url_for("contexts.index"))
    return render_template("contexts/new.html")


@bp.route("/<int:context_id>/view", methods=("GET",))
@login_required
def view(context_id):
    context = get_context(context_id)
    lists = get_context_lists(context_id)
    conversations = get_context_conversations(context_id)
    return render_template("contexts/view.html", context=context, lists=lists, conversations=conversations)


@bp.route("/<int:context_id>/edit", methods=("GET", "POST"))
@login_required
def edit(context_id):
    context = get_context(context_id)
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        error = None
        if not name or not description:
            error = "Name and description are required."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE contexts SET name = ?, description = ?"
                " WHERE id = ?",
                (name, description, context_id)
            )
            db.commit()
            return redirect(url_for("contexts.view", context_id=context_id))
    return render_template("contexts/edit.html", context=context)


@bp.route('/<int:context_id>/delete', methods=('POST',))
@login_required
def delete(context_id):
    get_context(context_id)
    db = get_db()
    db.execute('DELETE FROM contexts WHERE id = ?', (context_id,))
    db.execute("DELETE FROM context_list_relations WHERE context_id = ?", (context_id,))
    db.commit()
    return redirect(url_for('contexts.index'))


@bp.route("/<int:context_id>/new-list", methods=("GET", "POST"))
@login_required
def new_list(context_id):
    context = get_context(context_id)
    if request.method == "POST":
        list_id = request.form["list_id"]
        alist = get_list(list_id)
        db = get_db()
        db.execute(
            "INSERT INTO context_list_relations (creator_id, context_id, list_id)"
            " VALUES (?, ?, ?)",
            (g.user["id"], context_id, list_id)
        )
        db.commit()
        return redirect(url_for("contexts.view", context_id=context_id))
    lists = get_unrelated_lists(context_id)
    return render_template("contexts/new_list.html", context=context, lists=lists)


@bp.route("/<int:context_id>/remove-list", methods=("POST",))
@login_required
def remove_list(context_id):
    context = get_context(context_id)
    list_id = request.form["list_id"]
    alist = get_list(list_id)
    db = get_db()
    db.execute(
        "DELETE FROM context_list_relations"
        " WHERE context_id = ? AND list_id = ?",
        (context_id, list_id)
    )
    db.commit()
    return redirect(url_for("contexts.view", context_id=context_id))


def get_context(context_id, check_author=True): # The check_author parameter means this function is also useful for getting the context in general, not just for the update view e.g. displaying a single context on a "view context" page.
    context = get_db().execute(
        'SELECT c.id, name, description, created, creator_id, username'
        ' FROM contexts c JOIN users u ON c.creator_id = u.id'
        ' WHERE c.id = ?',
        (context_id,)
    ).fetchone()
    if context is None:
        abort(404, f"Context id {context_id} doesn't exist.") # abort() will raise a special exception that returns an HTTP status code. It takes an optional message to show with the error. 404 means "Not Found".
    if check_author and context['creator_id'] != g.user['id']:
        abort(403) # 403 means Forbidden. 401 means "Unauthorized" but you redirect to the login page instead of returning that status.
    return context


def get_context_lists(context_id):
    db = get_db()
    db.row_factory = dict_factory
    lists = db.execute(
        "SELECT r.list_id AS id, l.name, l.description"
        " FROM context_list_relations r"
        " JOIN lists l ON l.id = r.list_id"
        " WHERE context_id = ?",
        (context_id,)
    ).fetchall()
    return lists


def get_context_agents(context_id):
    db = get_db()
    agents = db.execute(
        "SELECT r.agent_id AS id, a.name, a.description"
        " FROM context_agent_relations r"
        " JOIN agents a ON a.id = r.agent_id"
        " WHERE context_id = ?",
        (context_id,)
    ).fetchall()
    return agents


def get_context_conversations(context_id):
    conversations = get_db().execute(
        "SELECT c.id, c.name, a.id AS agent_id, a.name AS agent_name"
        " FROM conversations c"
        " JOIN context_conversation_relations ccr ON ccr.conversation_id = c.id"
        " JOIN conversation_agent_relations car ON car.conversation_id = c.id"
        " JOIN agents a ON a.id = car.agent_id"
        " WHERE ccr.context_id = ?",
        (context_id,)
    ).fetchall()
    return conversations


def get_unrelated_lists(context_id):
    db = get_db()
    context_lists = get_context_lists(context_id)
    context_list_ids = [context_list["id"] for context_list in context_lists]
    user_lists = get_user_lists()
    unrelated_lists = [user_list for user_list in user_lists if user_list["id"] not in context_list_ids]
    return unrelated_lists


def get_unrelated_agents(context_id):
    db = get_db()
    agents = get_agents()
    context_agents = get_context_agents(context_id)
    context_agent_ids = None
    if context_agents is not None:
        context_agent_ids = [context_agent["id"] for context_agent in context_agents]
    if context_agent_ids is not None:
        agents = [agent for agent in agents if agent["id"] not in context_agent_ids]
    return agents
