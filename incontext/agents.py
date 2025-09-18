from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db, dict_factory


bp = Blueprint("agents", __name__, url_prefix="/agents")


@bp.route("/")
@login_required
def index():
    agents = get_agents()
    return render_template("agents/index.html", agents=agents)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
def new():
    agent_models = get_agent_models()
    if request.method == 'POST':
        error = None
        name = request.form['name']
        description = request.form["description"]
        model_id = request.form['model_id']
        if model_id:
            try:
                model_id = int(model_id)
            except:
                model_id = None
        model = next((agent_model for agent_model in agent_models if agent_model["id"] == model_id), None)
        role = request.form['role']
        instructions = request.form['instructions']
        if not name or not model or not role or not instructions:
            error = 'Name, model, role, and instructions are all required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO agents (name, description, model_id, role, instructions, creator_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (name, description, model_id, role, instructions, g.user['id'])
            )
            db.commit()
            return redirect(url_for('agents.index'))
    return render_template('agents/new.html', agent_models=agent_models)


@bp.route('/<int:agent_id>/view')
@login_required
def view(agent_id):
    agent = get_agent(agent_id)
    conversations = get_agent_conversations(agent_id)
    contexts = get_agent_contexts(agent_id)
    return render_template('agents/view.html', agent=agent, conversations=conversations, contexts=contexts)


@bp.route('/<int:agent_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(agent_id):
    agent = get_agent(agent_id)
    agent_models = get_agent_models()
    if request.method == "POST":
        error = None
        name = request.form['name']
        description = request.form['description']
        model_id = request.form['model_id']
        if model_id:
            try:
                model_id = int(model_id)
            except:
                model_id = None
        model = next((agent_model for agent_model in agent_models if agent_model["id"] == model_id), None)
        role = request.form["role"]
        instructions = request.form["instructions"]
        if not name or not model or not role or not instructions:
            error = "Name, model, role, and instructions are all required."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE agents"
                " SET name = ?, description = ?, model_id = ?, role = ?, instructions = ?"
                " WHERE id = ?",
                (name, description, model_id, role, instructions, agent_id)
            )
            db.commit()
            return redirect(url_for('agents.view', agent_id=agent_id))
    return render_template("agents/edit.html", agent=agent, agent_models=agent_models)


@bp.route("<int:agent_id>/delete", methods=("POST",))
@login_required
def delete(agent_id):
    agent = get_agent(agent_id)
    db = get_db()
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    db.commit()
    return redirect(url_for('agents.index'))


def get_agents():
    db = get_db()
    agents = db.execute(
        'SELECT a.id, a.creator_id, a.created, a.name, a.description, a.model_id, a.role, a.instructions, u.username'
        ' FROM agents a JOIN users u ON a.creator_id = u.id'
        " WHERE creator_id = ?",
        (g.user["id"],)
    ).fetchall()
    return agents


def get_agent(agent_id, check_access=True):
    db = get_db()
    agent = db.execute(
        'SELECT a.id, a.creator_id, a.created, a.name, a.description, a.model_id, a.role, a.instructions, m.model_name, m.provider_name, u.username'
        ' FROM agents a'
        ' JOIN agent_models m ON m.id = a.model_id'
        ' JOIN users u ON u.id = a.creator_id'
        ' WHERE a.id = ?',
        (agent_id,)
    ).fetchone()
    if agent is None:
        abort(404)
    if check_access:
        if agent['creator_id'] != g.user['id']:
            abort(403)
    return agent


def get_agent_models():
    db = get_db()
    agent_models = db.execute(
        "SELECT id, provider_name, provider_code, model_name, model_code, model_description"
        " FROM agent_models"
    ).fetchall()
    return agent_models


def get_agent_creator_id(agent_id):
    creator_id = get_db().execute(
        "SELECT a.creator_id"
        " FROM agents a"
        " WHERE a.id = ?",
        (agent_id,)
    ).fetchone()["creator_id"]
    return creator_id


def get_agent_contexts(agent_id, check_access=True):
    if check_access:
        agent_creator_id = get_agent_creator_id(agent_id)
        if agent_creator_id != g.user['id']:
            abort(403)
    db = get_db()
    contexts = db.execute(
        "SELECT ctx.id, ctx.name, ctx.description"
        " FROM contexts ctx"
        " JOIN context_conversation_relations ccr"
        " ON ccr.context_id = ctx.id"
        " JOIN conversation_agent_relations car"
        " ON car.conversation_id = ccr.conversation_id"
        " WHERE car.agent_id = ?",
        (agent_id,)
    ).fetchall()
    return contexts


def get_agent_conversations(agent_id, check_access=True):
    if check_access:
        agent_creator_id = get_agent_creator_id(agent_id)
        if agent_creator_id != g.user['id']:
            abort(403)
    db = get_db()
    conversations = db.execute(
        "SELECT c.id, c.name, ctx.id AS context_id, ctx.name AS context_name"
        " FROM conversations c"
        " JOIN context_conversation_relations ccr ON ccr.conversation_id = c.id"
        " JOIN contexts ctx ON ctx.id = ccr.context_id"
        " JOIN conversation_agent_relations car ON car.conversation_id = c.id"
        " WHERE car.agent_id = ?",
        (agent_id,)
    ).fetchall()
    return conversations
