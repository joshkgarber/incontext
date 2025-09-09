from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required, admin_only
from incontext.db import get_db

bp = Blueprint('master_agents', __name__, url_prefix='/master-agents')

@bp.route('/')
@login_required
@admin_only
def index():
    master_agents = get_master_agents()
    return render_template('master-agents/index.html', master_agents=master_agents)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
@admin_only
def new():
    agent_models = get_agent_models()
    if request.method == 'POST':
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
        role = request.form['role']
        instructions = request.form['instructions']
        if not name or not model or not role or not instructions:
            error = 'Name, model, role, and instructions are all required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO master_agents (name, description, model_id, role, instructions, creator_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (name, description, model_id, role, instructions, g.user['id'])
            )
            db.commit()
            return redirect(url_for('master_agents.index'))
    return render_template('master-agents/new.html', agent_models=agent_models)


@bp.route('/<int:master_agent_id>/view')
@login_required
def view(master_agent_id):
    master_agent = get_master_agent(master_agent_id, check_access=False)
    return render_template('master-agents/view.html', master_agent=master_agent)


@bp.route('/<int:master_agent_id>/edit', methods=('GET', 'POST'))
@login_required
@admin_only
def edit(master_agent_id):
    master_agent = get_master_agent(master_agent_id)
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
                "UPDATE master_agents"
                " SET name = ?, description = ?, model_id = ?, role = ?, instructions = ?"
                " WHERE id = ?",
                (name, description, model_id, role, instructions, master_agent_id)
            )
            db.commit()
            return redirect(url_for('master_agents.index'))
    return render_template("master-agents/edit.html", master_agent=master_agent, agent_models=agent_models)


@bp.route("<int:master_agent_id>/delete", methods=("POST",))
@login_required
@admin_only
def delete(master_agent_id):
    master_agent = get_master_agent(master_agent_id)
    db = get_db()
    db.execute("DELETE FROM master_agents WHERE id = ?", (master_agent_id,))
    db.commit()
    return redirect(url_for('master_agents.index'))


def get_master_agents():
    db = get_db()
    master_agents = db.execute(
        'SELECT m.id, m.created, m.name, m.description, a.model_name, m.role, m.instructions, u.username'
        ' FROM master_agents m'
        " JOIN agent_models a"
        " JOIN users u"
        " ON a.id = m.model_id"
        " AND u.id = m.creator_id"
    ).fetchall()
    return master_agents


def get_master_agent(master_agent_id, check_access=True):
    db = get_db()
    master_agent = db.execute(
        'SELECT m.id, m.creator_id, m.created, m.name, m.description, m.model_id, m.role, m.instructions, a.model_name, a.provider_name, u.username'
        ' FROM master_agents m'
        ' JOIN agent_models a ON a.id = m.model_id'
        ' JOIN users u ON u.id = m.creator_id'
        ' WHERE m.id = ?',
        (master_agent_id,)
    ).fetchone()
    if master_agent is None:
        abort(404)
    if check_access:
        if not g.user["admin"]:
            abort(403)
    return master_agent


def get_agent_models():
    db = get_db()
    agent_models = db.execute(
        "SELECT id, provider_name, provider_code, model_name, model_code, model_description"
        " FROM agent_models"
    ).fetchall()
    return agent_models
