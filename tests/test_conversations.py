import pytest
from incontext.db import get_db


def test_index(client, auth):
    # user must be logged in
    response = client.get('/conversations/', follow_redirects=True) # The follow_redirects is new in just-conversations. Now login is indeed required for the entity (conversations) index page. The login_required decorator is commented out in just-contexts and just-agents, but if future it shouldn't be in a combined app.
    assert b'Log In' in response.data
    assert b'Register' in response.data
    
    # serve the conversations overview page to logged-in user
    auth.login()
    response = client.get('/conversations/')
    # base nav
    assert b'Log Out' in response.data
    # main
    assert b'test name' in response.data
    assert b'Created: 01.01.2025' in response.data
    assert b'Creator: test' in response.data
    assert b'href="/conversations/1"' in response.data
    assert b'href="/conversations/1/update"' in response.data
    assert b'Agent: Test' in response.data


def test_view_conversation(app, client, auth):
    # user must be logged in
    response = client.get('/conversations/1', follow_redirects=True)
    assert b'Log In' in response.data
    assert b'Register' in response.data
    
    auth.login()

    # conversation must exist
    assert client.get('conversations/2').status_code == 404
    
    # serve conversation page to to user who created it (default test data complies)
    response = client.get('/conversations/1')
    assert response.status_code == 200
    assert b'Log Out' in response.data
    assert b'Conversation "test name"' in response.data
    assert b'href="/conversations/1/update"' in response.data
    assert b'Name: Test' in response.data
    assert b'Model: gpt-4.1-mini' in response.data
    assert b'Role: Testing Agent' in response.data
    assert b'Instructions: Reply with one word: &#34;Working&#34;.' in response.data
    assert b'This is a test.' in response.data
    assert b'Working' in response.data
    
    # forbid conv page to non-creator user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE conversations SET creator_id = 3 WHERE id = 1')
        db.commit()
    assert client.get('/conversations/1').status_code == 403


def test_create_conversation(client, auth, app):
    auth.login()
    assert client.get('conversations/create').status_code == 200

    response = client.post('conversations/create', data={'name': 'created', 'agent': 1})

    with app.app_context():
        db = get_db()
        count_c = db.execute('SELECT COUNT(id) FROM conversations').fetchone()[0]
        count_r = db.execute('SELECT COUNT(id) FROM conversation_agent_relations').fetchone()[0]
        assert count_c == 2
        assert count_r == 2
    

def test_update_conversation(client, auth, app):
    auth.login()
    assert client.get('conversations/1/update').status_code == 200
    
    client.post('/conversations/1/update', data={'name': 'Test Updated', 'agent': 2})

    with app.app_context():
        db = get_db()
        conversation = db.execute('SELECT * FROM conversations WHERE id = 1').fetchone()
        assert conversation['name'] == 'Test Updated'
        relation = db.execute('SELECT * FROM conversation_agent_relations WHERE conversation_id = 1').fetchone()
        assert relation['agent_id'] == 2


@pytest.mark.parametrize('path', (
    '/conversations/create',
    '/conversations/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'name': '', 'agent': 1})
    assert b'Name and agent are required.' in response.data
    response = client.post(path, data={'name': 'test', 'agent': ''})
    assert b'Name and agent are required' in response.data


@pytest.mark.parametrize('path', (
    'conversations/create',
    'conversations/1/update',
    'conversations/1/delete',
    'conversations/1/add-message',
    'conversations/1/agent-response',
))
def test_modify_conversation_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


@pytest.mark.parametrize('path', (
    'conversations/2/update',
    'conversations/2/delete',
    'conversations/2/add-message',
    'conversations/2/agent-response',
))
def test_modify_conversation_must_exist(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_modify_conversation_must_be_creator(app, client, auth):
    # change the conversation creator to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE conversations SET creator_id = 3 WHERE id = 1')
        db.commit()

    auth.login()
    # current user doesn't see Open link
    assert b'href="/conversations/1"' not in client.get('/conversations').data
    # current user can't view or modify another user's conversation
    assert client.post('conversations/1/update').status_code == 403
    assert client.post('conversations/1/delete').status_code == 403
    assert client.post('conversations/1/add-message').status_code == 403
    assert client.post('conversations/1/agent-response').status_code == 403


def test_add_message(client, auth, app):
    auth.login()
    response = client.post('/conversations/1/add-message', json={'content': 'hello'})
    assert response.status_code == 200
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
        assert count == 4


def test_add_message_validation(client, auth, app):
    auth.login()
    response = client.post('/conversations/1/add-message', json={'content': ''})
    assert b'Message can\'t be empty.' in response.data


def test_agent_response(client, auth, app):
    auth.login()
    response = client.post('/conversations/1/agent-response')
    assert response.status_code == 200
    assert response.json == {'content': 'Working'}
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
        assert count == 4
        db.execute('UPDATE agents SET instructions = ? WHERE id = 1', ('Reply with one word: "Successful"',))
        db.execute('UPDATE messages SET content = ? WHERE human = 0', ('Successful',))
        db.execute('DELETE FROM messages WHERE id > 3')
        db.commit()
    response = client.post('/conversations/1/agent-response')
    assert response.status_code == 200
    assert response.json == {'content': 'Successful'}
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
        assert count == 4
        db.execute('UPDATE agents SET vendor = ?, model = ? WHERE id = 1', ('anthropic', 'claude-3-5-haiku-latest'))
        db.execute('DELETE FROM messages WHERE id > 3')
        db.commit()
    response = client.post('/conversations/1/agent-response')
    assert response.status_code == 200
    assert response.json == {'content': 'Successful'}
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
        assert count == 4
        db.execute('UPDATE agents SET vendor = ?, model = ? WHERE id = 1', ('google', 'gemini-1.5-flash-8b'))
        db.execute('DELETE FROM messages WHERE id > 3')
        db.commit()
    response = client.post('/conversations/1/agent-response')
    assert response.status_code == 200
    response_content = response.json['content']
    clean_response_content = ''.join(e for e in response_content if e.isalnum())
    assert clean_response_content == 'Successful'
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM messages').fetchone()[0]
        assert count == 4


# Cannot test get_agent_response error handling until I can spoof the model for example. I havent figured out how to use the responses library to spoof the whole openai api response. Perhaps I need to refactor the way ai responses are being requrested in order to enable using the responses library.


def test_delete(client, auth, app): # the delete view should should redirect to the index url and the conversation should no longer exist in the db.
    auth.login()
    response = client.post('/conversations/1/delete')
    assert response.headers['Location'] == '/conversations/'
    with app.app_context():
        db = get_db()
        conversation = db.execute('SELECT * FROM conversations WHERE id = 1').fetchone()
        assert conversation is None
        # messages whould be deleted
        count = db.execute('SELECT COUNT(id) FROM messages WHERE conversation_id = 1').fetchone()[0]
        assert count == 0
