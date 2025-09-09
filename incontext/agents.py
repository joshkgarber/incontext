from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db
from incontext.master_agents import get_agent_models
from incontext.master_agents import get_master_agents
from incontext.master_agents import get_master_agent


bp = Blueprint('agents', __name__, url_prefix='/agents')


@bp.route('/')
@login_required
def index():
    agents, tethered_agents = get_agents()
    return render_template('agents/index.html', agents=agents, tethered_agents=tethered_agents)


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


@bp.route("/new-tethered", methods=("GET", "POST"))
@login_required
def new_tethered():
    if request.method == "POST":
        requested_master_agent = get_master_agent(request.form["master_agent_id"], False)
        db = get_db()
        db.execute(
            "INSERT INTO tethered_agents (creator_id, master_agent_id)"
            " VALUES (?, ?)",
            (g.user["id"], request.form["master_agent_id"])
        )
        db.commit()
        return redirect(url_for("agents.index"))
    master_agents = get_master_agents()
    return render_template("agents/new_tethered.html", master_agents=master_agents)


@bp.route('/<int:agent_id>/view')
@login_required
def view(agent_id):
    agent = get_agent(agent_id)
    return render_template('agents/view.html', agent=agent)


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
            return redirect(url_for('agents.index'))
    return render_template("agents/edit.html", agent=agent, agent_models=agent_models)


@bp.route("<int:agent_id>/delete", methods=("POST",))
@login_required
def delete(agent_id):
    agent = get_agent(agent_id)
    db = get_db()
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    db.commit()
    return redirect(url_for('agents.index'))


@bp.route("<int:tethered_agent_id>/delete-tethered", methods=("POST",))
@login_required
def delete_tethered(tethered_agent_id):
    tethered_agent = get_tethered_agent(tethered_agent_id)
    db = get_db()
    db.execute("DELETE FROM tethered_agents WHERE id = ?", (tethered_agent_id,))
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
    tethered_agents = db.execute(
        "SELECT ta.id, ma.name, ma.description, ta.created, ma.id as master_agent_id"
        " FROM master_agents ma"
        " JOIN tethered_agents ta"
        " ON ma.id = ta.master_agent_id"
        " WHERE ta.creator_id = ?",
        (g.user["id"],)
    )
    return agents, tethered_agents


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


def get_tethered_agent(tethered_agent_id, check_access=True):
    db = get_db()
    tethered_agent = db.execute(
        'SELECT ta.creator_id'
        ' FROM tethered_agents ta'
        ' WHERE ta.id = ?',
        (tethered_agent_id,)
    ).fetchone()
    if tethered_agent is None:
        abort(404)
    if check_access:
        if tethered_agent['creator_id'] != g.user['id']:
            abort(403)
    return tethered_agent
