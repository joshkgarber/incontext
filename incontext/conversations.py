from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db
from incontext.agents import get_agents
from incontext.agents import get_agent
from openai import OpenAI
import anthropic
from google import genai
from google.genai import types
import os

bp = Blueprint('conversations', __name__, url_prefix='/conversations')

@bp.route('/')
@login_required
def index():
    db = get_db()
    conversations = db.execute(
        'SELECT c.id, c.name, c.created, c.creator_id, u.username, a.name as agent'
        ' FROM conversations c'
        ' JOIN users u ON c.creator_id = u.id'
        ' JOIN conversation_agent_relations r ON c.id = r.conversation_id'
        ' JOIN agents a ON r.agent_id = a.id'
        ' ORDER BY c.created DESC'
    ).fetchall()
    return render_template('conversations/index.html', conversations=conversations)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        agent_id = request.form['agent']
        error = None

        if not name or not agent_id:
            error = 'Name and agent are required.'
        
        if error is not None:
            flash(error) 
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO conversations (name, creator_id)'
                ' VALUES (?, ?)',
                (name, g.user['id'])
            )
            conversation_id = cur.lastrowid
            cur.execute(
                'INSERT INTO conversation_agent_relations(conversation_id, agent_id)'
                ' VALUES (?, ?)',
                (conversation_id, agent_id)
            )
            db.commit()
            return redirect(url_for('conversations.index'))
    
    agents = get_agents()
    return render_template('conversations/create.html', agents=agents)

def get_conversation(id, check_creator=True):
    conversation = get_db().execute(
        'SELECT c.id, name, created, creator_id, username, r.agent_id as agent_id'
        ' FROM conversations c'
        ' JOIN users u ON c.creator_id = u.id'
        ' JOIN conversation_agent_relations r ON c.id = r.conversation_id'
        ' WHERE c.id = ?',
        (id,)
    ).fetchone()

    if conversation is None:
        abort(404, f"Conversation id {id} doesn't exist.")

    if check_creator and conversation['creator_id'] != g.user['id']:
        abort(403) # 403 means Forbidden. 401 means "Unauthorized" but you redirect to the login page instead of returning that status.
    
    return conversation

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    conversation = get_conversation(id)

    if request.method == 'POST':
        name = request.form['name']
        agent_id = request.form['agent']
        error = None

        if not name or not agent_id:
            error = 'Name and agent are required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE conversations SET name = ?'
                ' WHERE id = ?',
                (name, id)
            )
            db.execute(
                'UPDATE conversation_agent_relations SET agent_id = ?'
                ' WHERE conversation_id = ?',
                (agent_id, id)
            )
            db.commit()
            return redirect(url_for('conversations.index'))

    agents = get_agents()
    return render_template('conversations/update.html', conversation=conversation, agents=agents)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_conversation(id)
    db = get_db()
    db.execute('DELETE FROM conversations WHERE id = ?', (id,))
    db.execute('DELETE FROM conversation_agent_relations WHERE conversation_id = ?', (id,))
    db.commit()
    delete_messages(id)
    return redirect(url_for('conversations.index'))


def get_related_agent(conversation_id):
    agent = get_db().execute(
        'SELECT a.name, a.model, a.role, a.instructions'
        ' FROM agents a'
        ' JOIN conversation_agent_relations r ON r.agent_id = a.id'
        ' WHERE r.conversation_id = ?',
        (conversation_id,)
    ).fetchone()
    return agent


@bp.route('/<int:id>', methods=('GET',))
@login_required
def view(id):
    conversation = get_conversation(id)
    agent = get_related_agent(id)
    messages = get_messages(id)
    return render_template('conversations/view.html', conversation=conversation, agent=agent, messages=messages)


def get_messages(conversation_id):
    messages = get_db().execute(
        'SELECT m.id, m.content, m.human, m.created, c.creator_id'
        ' FROM messages m'
        ' JOIN conversations c'
        ' ON m.conversation_id = c.id'
        ' WHERE c.id = ?',
        (conversation_id,)
    ).fetchall()
    
    return messages


def delete_messages(conversation_id):
    db = get_db()
    db.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
    db.commit()


def get_credential(name):
    os_env_var = os.environ.get(name)
    if os_env_var is not None:
        return os_env_var
    else:
        credential_path = os.environ.get('CREDENTIALS_DIRECTORY')
        with open(f'{credential_path}/{name}') as f:
            credential = f.read().strip()
            return credential


def get_openai_response(conversation_history, agent):
    conversation_history = [
        dict(
            role='system',
            content=f'You are a {agent["role"]}. {agent["instructions"]}',
        )
    ] + conversation_history
    openai_api_key = get_credential('OPENAI_API_KEY')
    client = OpenAI(api_key=openai_api_key)
    try:
        response = client.responses.create(
            model=agent['model'],
            input=conversation_history
        )
        return dict(success=True, content=response.output_text)
    except Exception as e:
        return dict(success=False, content=e)    


def get_anthropic_response(conversation_history, agent):
    conversation_history = [
        dict(
            role='user',
            content=agent['instructions']
        )
    ] + conversation_history
    anthropic_api_key = get_credential('ANTHROPIC_API_KEY')
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    try:
        response = client.messages.create(
            model=agent['model'],
            max_tokens=1024,
            system=f'You are a {agent["role"]}.',
            messages=conversation_history
        )
        return dict(success=True, content=response.content[0].text)
    except Exception as e:
        return dict(success=False, content=e)


def get_google_response(conversation_history, agent):
    google_api_key = get_credential('GEMINI_API_KEY')
    client = genai.Client(api_key=google_api_key)
    chat = client.chats.create(
        model=agent['model'],
        config=types.GenerateContentConfig(
            system_instruction=f'You are a {agent["role"]}. {agent["instructions"]}'
        ),
        history=conversation_history[:-1]
    )
    try:
        response = chat.send_message(conversation_history[-1]['parts'][0]['text'])
        return dict(success=True, content=response.text)
    except Exception as e:
        return dict(success=False, content=e)


def get_agent_response(cid):
    agent_id = get_db().execute(
        'SELECT r.agent_id FROM conversation_agent_relations r'
        ' JOIN conversations c ON r.conversation_id = c.id'
        ' WHERE r.conversation_id = ?',
        (cid,)
    ).fetchone()['agent_id']
    agent = get_agent(agent_id)
    vendor = agent['vendor']
    agent_conversation_role = 'model' if vendor == 'google' else 'assistant'
    conversation_history = []
    messages = get_messages(cid)
    for message in messages:
        human = message['human']
        role = 'user' if human == 1 else agent_conversation_role
        content = message['content']
        if vendor == 'google':
            parts = [{'text': content}]
            conversation_history.append(dict(role=role, parts=parts))
        else:
            conversation_history.append(dict(role=role, content=content))
    if vendor == 'openai':
        return get_openai_response(conversation_history, agent)
    elif vendor == 'anthropic':
        return get_anthropic_response(conversation_history, agent)
    else:
        print(conversation_history)
        return get_google_response(conversation_history, agent)

    
@bp.route('/<int:conversation_id>/add-message', methods=('POST',))
@login_required
def add_message(conversation_id):
    conversation = get_conversation(conversation_id) # To check the creator
    message_content = request.json['content']
    error = None

    if not message_content:
        error = 'Message can\'t be empty.'

    if error is not None:
        return error, 400
    else:
        db = get_db()
        db.execute(
            'INSERT INTO messages (conversation_id, content, human)'
            ' VALUES (?, ?, ?)',
            (conversation_id, message_content, 1,)
        )
        db.commit()
        return '', 200


@bp.route('/<int:conversation_id>/agent-response', methods=('POST',))
@login_required
def agent_response(conversation_id):
    conversation = get_conversation(conversation_id) # To check the creator
    agent_response = get_agent_response(conversation_id)
    if agent_response['success']:
        db = get_db()
        db.execute(
            'INSERT INTO messages (conversation_id, content, human)'
            'VALUES (?, ?, ?)',
            (conversation_id, agent_response['content'], 0,)
        )
        db.commit()
        return {'content': agent_response['content']}, 200
    else:
        # print(agent_response['content']) # Log the error
        return {'content': f'An error occurred in get_agent_response: {agent_response["content"]}'}, 200
